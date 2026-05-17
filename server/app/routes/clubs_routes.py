from flask import Blueprint, jsonify, request

from server.app.decorators import login_required
from server.app.models.club import Club
from server.app.models.ladder_team import LadderTeam
from server.app.models.match import MatchPlayed, MatchProposal, MatchStatus
from server.app.services.auth_service import verify_user
from server.app.models.ladder import Ladder
from server.app.models.team import Team
from server.extensions import cache, db
from server.app.models.account import Account, Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.club_owner_club import ClubOwnerClub
from server.app.models.club_player import ClubPlayer
from server.app.models.team import TeamManager
from server.app.routes.dashboard_routes import get_current_user_id_from_cookie
from server.app.services.city_service import resolve_city_label
from sqlalchemy import or_

clubs_bp = Blueprint("clubs", __name__, url_prefix="/api")

@clubs_bp.get("/clubs")
@cache.cached(timeout=300, key_prefix="clubs_list")
def list_clubs():
    db_clubs = Club.query.order_by(Club.name.asc()).all()
    clubs = [{
        "id": club.id,
        "name": club.name,
        "description": club.description,
        "sport_type_id": club.sport_type_id,
        "sport": club.sport,
        "city": club.city,
    } for club in db_clubs]
    return jsonify({"clubs": clubs}), 200

@clubs_bp.get("/clubs/<int:club_id>")
@cache.memoize(timeout=300)
def get_club(club_id: int):
    club = Club.query.filter_by(id=club_id).first()
    if not club:
        return jsonify({"message": "Club not found"}), 404
    
    return jsonify({"club": {
        "id": club.id,
        "name": club.name,
        "description": club.description,
        "sport_type_id": club.sport_type_id,
        "sport": club.sport,
        "city": club.city,
    }}), 200

@clubs_bp.get("/clubs/<int:club_id>/is_manager")
def check_if_manager(club_id: int):
    # 1. Get the token from the cookie
    token = request.cookies.get("access_token")
    account = verify_user(token)

    # 2. If no valid account is found, they definitely aren't a manager
    if not account:
        return jsonify({"is_manager": False}), 401

    # 3. Find the club in the database
    club = Club.query.filter_by(id=club_id).first()
    if not club:
        return jsonify({"message": "Club not found"}), 404

    admin = Administrator.query.filter_by(id=account.id).first()
    if admin:
        return jsonify({"is_manager": True}), 200

    clubowner = ClubOwner.query.filter_by(id=account.id).first()
    if not clubowner:
        return jsonify({"message": "Unauthorized"}), 401
    
    owner_check = ClubOwnerClub.query.filter_by(club_owner_id=clubowner.id, club_id=club_id).first()
    if not owner_check:
        return jsonify({"message": "Forbidden"}), 403

    return jsonify({"is_manager": True}), 200

@clubs_bp.post("/clubs")
def create_club():
    # 1. Kijk wie de club probeert aan te maken (net als bij je is_manager route)
    token = request.cookies.get("access_token")
    account = verify_user(token)

    if not account:
        return jsonify({"message": "Je moet ingelogd zijn om een club te maken"}), 401

    # 2. Read payload
    data = request.get_json() or {}
    club_name = (data.get("name") or "").strip()

    if not club_name:
        return jsonify({"message": "Clubnaam is verplicht"}), 400

    city_input = (data.get("city") or "").strip()
    if not city_input:
        return jsonify({"message": "City is required."}), 400

    city = resolve_city_label(city_input)
    if not city:
        return jsonify({"message": "Please select a real city from the suggestions."}), 400

    description = (data.get("description") or "Club created by user").strip() or "Club created by user"
    sport_type_id = data.get("sport_type_id")
    sport_name = data.get("sport")

    # Ensure the account can own clubs: team_manager -> club_owner chain.
    team_manager = TeamManager.query.filter_by(id=account.id).first()
    if not team_manager:
        team_manager = TeamManager(id=account.id)
        db.session.add(team_manager)
        db.session.flush()

    club_owner = ClubOwner.query.filter_by(id=account.id).first()
    if not club_owner:
        club_owner = ClubOwner(id=account.id)
        db.session.add(club_owner)
        db.session.flush()

    # 3. Create club (all required fields present)
    new_club = Club(
        name=club_name,
        description=description,
        city=city,
        sport_type_id=sport_type_id,
    )

    db.session.add(new_club)
    db.session.flush()

    owner_link = ClubOwnerClub.query.filter_by(club_owner_id=club_owner.id, club_id=new_club.id).first()
    if not owner_link:
        db.session.add(
            ClubOwnerClub(
                club_owner_id=club_owner.id,
                club_id=new_club.id,
                can_rename=True,
                can_change_description=True,
                can_manage_match=True,
                can_add_club_players=True,
                can_add_club_owners=True,
                can_add_club_rule=True,
            )
        )

    # 5. Persist
    db.session.commit()

    cache.delete("clubs_list")

    return jsonify({
        "message": "Club succesvol aangemaakt!", 
        "club": {"id": new_club.id, "name": new_club.name}
    }), 201

@clubs_bp.get("/clubs/<int:club_id>/ladders")
@cache.memoize(timeout=300)
def get_club_ladders(club_id: int):
    # Haal alle ladders op die bij deze specifieke club horen
    ladders = Ladder.query.filter_by(club_id=club_id).all()
    
    # Zet ze om naar een lijst die React begrijpt
    return jsonify([
        {"id": l.id, "name": l.name, "description": l.description,"ruleset_id": l.ruleset_id}
        for l in ladders
    ]), 200

@clubs_bp.get("/clubs/<int:club_id>/home-summary")
def get_club_home_summary(club_id: int):
    # One summary payload keeps the club homepage from having to stitch together several separate requests.
    club = Club.query.filter_by(id=club_id).first()
    if not club:
        return jsonify({"message": "Club not found"}), 404

    ladders = Ladder.query.filter_by(club_id=club_id).order_by(Ladder.name.asc()).all()
    ladder_by_id = {ladder.id: ladder for ladder in ladders}

    # Resolve ladder membership once so we can infer match ladders later even when the proposal itself is sparse.
    membership_rows = (
        db.session.query(LadderTeam, Team, Ladder)
        .join(Team, Team.id == LadderTeam.team_id)
        .join(Ladder, Ladder.id == LadderTeam.ladder_id)
        .filter(Ladder.club_id == club_id)
        .all()
    )

    team_to_ladders: dict[int, set[int]] = {}
    team_payloads: dict[int, dict] = {}
    for ladder_team, team, ladder in membership_rows:
        team_to_ladders.setdefault(team.id, set()).add(ladder.id)
        current = team_payloads.get(team.id)
        if current is None or ladder_team.rating > current["rating"]:
            team_payloads[team.id] = {
                "id": team.id,
                "name": team.name,
                "rating": ladder_team.rating,
                "ladder_id": ladder.id,
                "ladder_name": ladder.name,
                "ladder_rank": ladder_team.rank,
            }

    club_team_ids = sorted(team_payloads.keys())

    def resolve_status(status_name: str):
        return MatchStatus.query.filter(db.func.lower(MatchStatus.name) == status_name.lower()).first()

    accepted_status = resolve_status("accepted")
    played_status = resolve_status("played")
    if not accepted_status or not played_status or not club_team_ids:
        return jsonify({
            "club": club.serialize(),
            "ladders": [
                {"id": ladder.id, "name": ladder.name, "description": ladder.description}
                for ladder in ladders
            ],
            "performers": [],
            "upcoming_matches": [],
            "latest_results": [],
        }), 200

    def infer_ladder(team1_id: int, team2_id: int, proposal_ladder_id: int | None):
        # Use the explicit ladder first, then fall back to the ladder both teams share.
        if proposal_ladder_id in ladder_by_id:
            return ladder_by_id[proposal_ladder_id]

        common_ladders = sorted(team_to_ladders.get(team1_id, set()) & team_to_ladders.get(team2_id, set()))
        if not common_ladders:
            return None
        return ladder_by_id.get(common_ladders[0])

    def serialize_match(match: MatchProposal, *, played: MatchPlayed | None = None):
        # Flatten the ORM objects into the exact shape the React card layout needs.
        ladder = infer_ladder(match.team1_id, match.team2_id, match.ladder_id)
        payload = {
            "id": match.id,
            "team1Id": match.team1_id,
            "team2Id": match.team2_id,
            "team1Name": match.team1.name if match.team1 else None,
            "team2Name": match.team2.name if match.team2 else None,
            "team1ClubName": match.team1.club.name if match.team1 and match.team1.club else None,
            "team2ClubName": match.team2.club.name if match.team2 and match.team2.club else None,
            "ladderId": ladder.id if ladder else match.ladder_id,
            "ladderName": ladder.name if ladder else None,
            "weekStartDate": match.week_start_date.isoformat() if match.week_start_date else None,
            "proposedStartAt": match.proposed_start_at.isoformat() + "Z" if match.proposed_start_at else None,
            "proposedEndAt": match.proposed_end_at.isoformat() + "Z" if match.proposed_end_at else None,
            "status": match.status.name if match.status else None,
            "scoreStatus": match.score_status,
        }

        if played is not None:
            payload.update({
                "scoreTeam1": played.score_team1,
                "scoreTeam2": played.score_team2,
                "playedAt": played.played_at.isoformat() + "Z" if played.played_at else None,
                "rating": played.rating,
            })

        return payload

    # Rank performers server-side so the frontend can just render the already-ordered list.
    performer_rows = sorted(
        team_payloads.values(),
        key=lambda item: (-item["rating"], item["name"].lower(), item["id"]),
    )

    # Accepted proposals are treated as upcoming even if the score is still disputed later.
    upcoming_matches = (
        db.session.query(MatchProposal)
        .filter(MatchProposal.status_id == accepted_status.id)
        .filter(
            or_(
                MatchProposal.team1_id.in_(club_team_ids),
                MatchProposal.team2_id.in_(club_team_ids),
            )
        )
        .order_by(
            MatchProposal.proposed_start_at.asc().nullslast(),
            MatchProposal.week_start_date.asc().nullslast(),
            MatchProposal.id.asc(),
        )
        .all()
    )

    # Only resolved played matches are surfaced in the latest-results panel.
    latest_results = (
        db.session.query(MatchProposal, MatchPlayed)
        .join(MatchPlayed, MatchPlayed.id == MatchProposal.id)
        .filter(MatchProposal.status_id == played_status.id)
        .filter(
            or_(
                MatchProposal.team1_id.in_(club_team_ids),
                MatchProposal.team2_id.in_(club_team_ids),
            )
        )
        .order_by(
            MatchPlayed.played_at.desc().nullslast(),
            MatchProposal.id.desc(),
        )
        .limit(3)
        .all()
    )

    return jsonify({
        "club": club.serialize(),
        "ladders": [
            {"id": ladder.id, "name": ladder.name, "description": ladder.description}
            for ladder in ladders
        ],
        "performers": performer_rows,
        "upcoming_matches": [serialize_match(match) for match in upcoming_matches],
        "latest_results": [
            serialize_match(match, played=played)
            for match, played in latest_results
        ],
    }), 200

@clubs_bp.put("/clubs/<int:club_id>")
def update_club(club_id: int):
    data = request.get_json() or {}

    user_id = get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401
    
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404
    
    clubowner = ClubOwner.query.filter_by(id=user_id).first()
    admin = Administrator.query.filter_by(id=user_id).first()
    if not clubowner and not admin:
        return jsonify({"message": "Unauthorized"}), 401

    owner_check = None
    if clubowner:
        owner_check = ClubOwnerClub.query.filter_by(club_owner_id=clubowner.id, club_id=club_id).first()

    if not owner_check and not admin:
        return jsonify({"message": "Forbidden"}), 403

    club.name = data.get("name", club.name)
    club.description = data.get("description", club.description)

    if "city" in data:
        city_input = (data.get("city") or "").strip()
        if not city_input:
            return jsonify({"message": "City is required."}), 400

        city = resolve_city_label(city_input)
        if not city:
            return jsonify({"message": "Please select a real city from the suggestions."}), 400

        club.city = city

    club.sport_type_id = data.get("sport_type_id", club.sport_type_id)

    db.session.commit()

    cache.delete_memoized(get_club, club_id)
    cache.delete("clubs_list")

    return jsonify({"message": "Club updated successfully"}), 200

@clubs_bp.get("/clubs/<int:club_id>/members")
def get_club_members(club_id: int):
    user_id = get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404

    # Subquery: get all owner user_ids for this club
    owner_user_ids = (
        db.session.query(ClubOwner.id)
        .join(ClubOwnerClub, ClubOwnerClub.club_owner_id == ClubOwner.id)
        .filter(ClubOwnerClub.club_id == club_id)
        .subquery()
    )

    # Main query: members excluding owners
    members = (
        db.session.query(Account)
        .join(ClubPlayer, ClubPlayer.player_id == Account.id)
        .filter(ClubPlayer.club_id == club_id)
        .filter(~Account.id.in_(owner_user_ids))
        .all()
    )

    result = [
        {
            "id": account.id,
            "email": account.email,
        }
        for account in members
    ]

    return jsonify({"members": result}), 200

@clubs_bp.delete("/clubs/<int:club_id>/members/<int:user_id>")
def remove_member(club_id: int, user_id: int):
    current_user_id = get_current_user_id_from_cookie()
    if not current_user_id:
        return jsonify({"message": "Unauthorized"}), 401

    # Check club exists
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404

    # Check current account is an owner of this club
    club_owner = ClubOwner.query.filter_by(id=current_user_id).first()
    admin = Administrator.query.filter_by(id=current_user_id).first()
    if not club_owner and not admin:
        return jsonify({"message": "Unauthorized"}), 401

    owner_check = None
    if club_owner:
        owner_check = ClubOwnerClub.query.filter_by(
            club_owner_id=club_owner.id,
            club_id=club_id
        ).first()

    if not owner_check and not admin:
        return jsonify({"message": "Forbidden"}), 403

    is_owner = ClubOwnerClub.query.filter_by(
        club_owner_id=user_id,
        club_id=club_id
    ).first()

    if is_owner:
        return jsonify({"message": "Cannot remove a club owner"}), 403

    # Remove member from ClubPlayer table
    membership = ClubPlayer.query.filter_by(
        club_id=club_id,
        player_id=user_id
    ).first()

    if not membership:
        return jsonify({"message": "Member not found"}), 404

    db.session.delete(membership)
    db.session.commit()

    return jsonify({"message": "Member removed successfully"}), 200

@clubs_bp.post("/clubs/<int:club_id>/ladders")
def create_ladder(club_id: int):
    data = request.get_json() or {}

    user_id = get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    # Check club exists
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404

    # Check account is owner
    club_owner = ClubOwner.query.filter_by(id=user_id).first()
    admin = Administrator.query.filter_by(id=user_id).first()
    if not club_owner and not admin:
        return jsonify({"message": "Unauthorized"}), 401

    owner_check = None
    if club_owner:
        owner_check = ClubOwnerClub.query.filter_by(
            club_owner_id=club_owner.id,
            club_id=club_id
        ).first()

    if not owner_check and not admin:
        return jsonify({"message": "Forbidden"}), 403

    # Create ladder
    # Rulesets are optional for non-racket ladders.
    ruleset_id = data.get("ruleset_id")
    if ruleset_id in ("", None):
        ruleset_id = None
    else:
        ruleset_id = int(ruleset_id)

    ladder = Ladder(
        club_id=club_id,
        name=data.get("name"),
        description=data.get("description"),
        sport_type_id=data.get("sport_type_id", 1),
        ruleset_id=ruleset_id,
        ladder_rating_function_id=data.get("ladder_rating_function_id", 1),
    )

    db.session.add(ladder)
    db.session.commit()

    test = Ladder.query.filter_by(id=ladder.id).first()
    if not test:
        return jsonify({"message": "Forbidden"}), 903


    return jsonify({
        "ladder": {
            "id": ladder.id,
            "name": ladder.name,
            "description": ladder.description,
            "club_id": ladder.club_id
        }
    }), 201

@clubs_bp.get("/clubs/<int:club_id>/owners")
def get_club_owners(club_id: int):
    """List all owners/managers of a club."""
    current_user_id = get_current_user_id_from_cookie()
    if not current_user_id:
        return jsonify({"message": "Unauthorized"}), 401

    club_owner = ClubOwner.query.filter_by(id=current_user_id).first()
    admin = Administrator.query.filter_by(id=current_user_id).first()
    if not club_owner and not admin:
        return jsonify({"message": "Forbidden"}), 403

    owners_query = (
        db.session.query(Account)
        .join(ClubOwner, ClubOwner.id == Account.id)
        .join(ClubOwnerClub, ClubOwnerClub.club_owner_id == ClubOwner.id)
        .filter(ClubOwnerClub.club_id == club_id)
    )
    owners = owners_query.all()

    return jsonify({
        "owners": [
            {
                "id": owner.id,
                "email": owner.email,
                "name": f"{owner.first_name} {owner.last_name}".strip(),
            }
            for owner in owners
        ]
    }), 200

@clubs_bp.post("/clubs/<int:club_id>/owners")
def add_club_owner(club_id: int):
    """Add a new owner to the club by their Account ID."""
    current_user_id = get_current_user_id_from_cookie()
    data = request.get_json() or {}
    target_owner_id = data.get("owner_id")

    if not current_user_id:
        return jsonify({"message": "Unauthorized"}), 401
    
    if not target_owner_id:
        return jsonify({"message": "Owner ID is required"}), 400

    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404

    requester_owner = ClubOwnerClub.query.filter_by(
        club_owner_id=current_user_id, club_id=club_id
    ).first()
    admin = Administrator.query.filter_by(id=current_user_id).first()
    if not requester_owner and not admin:
        return jsonify({"message": "Forbidden"}), 403

    target_account = Account.query.get(target_owner_id)
    if not target_account:
        return jsonify({"message": "User not found"}), 404

    target_manager = TeamManager.query.get(target_owner_id)
    if not target_manager:
        target_manager = TeamManager(id=target_owner_id)
        db.session.add(target_manager)
        db.session.flush()

    owner_profile = ClubOwner.query.get(target_owner_id)
    if not owner_profile:
        owner_profile = ClubOwner(id=target_owner_id)
        db.session.add(owner_profile)
        db.session.flush()

    existing_link = ClubOwnerClub.query.filter_by(
        club_owner_id=target_owner_id, club_id=club_id
    ).first()
    if existing_link:
        return jsonify({"message": "User is already an owner"}), 400

    new_link = ClubOwnerClub(club_owner_id=target_owner_id, club_id=club_id)
    db.session.add(new_link)
    db.session.commit()

    return jsonify({
        "message": "Owner added successfully",
        "owner": {"id": target_account.id, "email": target_account.email}
    }), 201

@clubs_bp.delete("/clubs/<int:club_id>/owners/<int:owner_id>")
def remove_club_owner(club_id: int, owner_id: int):
    """Remove an owner from the club."""
    current_user_id = get_current_user_id_from_cookie()
    if not current_user_id:
        return jsonify({"message": "Unauthorized"}), 401

    if current_user_id == owner_id:
        return jsonify({"message": "You cannot remove yourself"}), 400

    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404

    requester_owner = ClubOwnerClub.query.filter_by(
        club_owner_id=current_user_id, club_id=club_id
    ).first()
    admin = Administrator.query.filter_by(id=current_user_id).first()
    if not requester_owner and not admin:
        return jsonify({"message": "Forbidden"}), 403

    target_link = ClubOwnerClub.query.filter_by(
        club_owner_id=owner_id, club_id=club_id
    ).first()

    if not target_link:
        return jsonify({"message": "Owner not found in this club"}), 404

    db.session.delete(target_link)
    db.session.commit()

    return jsonify({"message": "Owner removed successfully"}), 200
@clubs_bp.get("/accounts/search")
def search_accounts():
    query = request.args.get("q", "").strip()
    
    if len(query) < 3:
        return jsonify({"accounts": []}), 200

    search_pattern = f"%{query}%"

    accounts = Account.query.filter(
        or_(
            Account.email.ilike(search_pattern),
            Account.first_name.ilike(search_pattern),
            Account.last_name.ilike(search_pattern)
        )
    ).limit(10).all()

    return jsonify({
        "accounts": [
            {
                "id": a.id,
                "email": a.email,
                "name": f"{a.first_name} {a.last_name}".strip() or "Unknown User"
            } 
            for a in accounts
        ]
    }), 200

@clubs_bp.get("/clubs/my")
@login_required
def list_my_clubs(account: Account):
    """Return all clubs the current user can manage (is an owner of)."""

    admin = Administrator.query.filter_by(id=account.id).first()
    if admin:
        db_clubs = Club.query.order_by(Club.name.asc()).all()
        clubs = [{"id": club.id, "name": club.name} for club in db_clubs]
        return jsonify({"clubs": clubs}), 200

    club_owner = ClubOwner.query.filter_by(id=account.id).first()
    if not club_owner:
        return jsonify({"clubs": []}), 200

    links = ClubOwnerClub.query.filter_by(club_owner_id=club_owner.id).all()
    club_ids = [link.club_id for link in links]

    if not club_ids:
        return jsonify({"clubs": []}), 200

    db_clubs = Club.query.filter(Club.id.in_(club_ids)).order_by(Club.name.asc()).all()
    clubs = [{"id": club.id, "name": club.name} for club in db_clubs]
    return jsonify({"clubs": clubs}), 200


@clubs_bp.delete("/clubs/<int:club_id>")
def delete_club(club_id: int):
    """
    Deletes the club and cleans up owner associations.
    """
    current_user_id = get_current_user_id_from_cookie()
    if not current_user_id:
        return jsonify({"message": "Unauthorized"}), 401

    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404

    requester_owner = ClubOwnerClub.query.filter_by(
        club_owner_id=current_user_id, club_id=club_id
    ).first()
    admin = Administrator.query.filter_by(id=current_user_id).first()
    if not requester_owner and not admin:
        return jsonify({"message": "Forbidden"}), 403

    try:
        db.session.delete(club)
        db.session.commit()
        return jsonify({
            "message": f"Club '{club.name}' and all associated data have been deleted."
        }), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"message": f"Failed to delete club: {str(exc)}"}), 500
