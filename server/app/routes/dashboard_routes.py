from flask import Blueprint, jsonify, request
import jwt

from server.app.models.club_join_request import ClubJoinRequest
from server.app.models.club import Club
from server.app.models.club_owner import ClubOwner
from server.app.models.club_owner_club import ClubOwnerClub
from server.app.models.match import MatchProposal, MatchPlayed, MatchStatus
from server.app.models.player import Player
from server.app.models.club_player import ClubPlayer
from server.extensions import db
from server.app.models.account import Account
from server.config import SECRET_KEY
from server.app.services.club_notifications import send_join_request_confirmation_to_player
from server.app.services.club_notifications import send_join_request_notification_to_owner
from server.app.services.club_notifications import send_join_request_decision_to_player
from datetime import datetime, timezone

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api")


def _get_current_user_id_from_cookie():
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.PyJWTError:
        return None


def _serialize_upcoming_matches(account):
    player = getattr(account, "player", None)
    if not player:
        return []

    team_ids = [team.id for team in player.teams]
    if not team_ids:
        return []

    accepted_status = MatchStatus.query.filter(
        db.func.lower(MatchStatus.name) == "accepted"
    ).first()
    if not accepted_status:
        return []

    matches = (
        MatchProposal.query.filter(
            MatchProposal.status_id == accepted_status.id,
            db.or_(
                MatchProposal.team1_id.in_(team_ids),
                MatchProposal.team2_id.in_(team_ids),
            ),
        )
        .order_by(MatchProposal.id.desc())
        .all()
    )

    upcoming_matches = []
    for match in matches:
        upcoming_matches.append(
            {
                "id": match.id,
                "status": match.status.to_dict() if match.status else None,
                "location": match.location,
                "team1Id": match.team1_id,
                "team1Name": match.team1.name if match.team1 else None,
                "team1ClubName": match.team1.club.name if match.team1 and match.team1.club else None,
                "team2Id": match.team2_id,
                "team2Name": match.team2.name if match.team2 else None,
                "team2ClubName": match.team2.club.name if match.team2 and match.team2.club else None,
                "weekStartDate": match.week_start_date.isoformat() if match.week_start_date else None,
                "proposedStartAt": match.proposed_start_at.isoformat() + "Z" if match.proposed_start_at else None,
                "proposedEndAt": match.proposed_end_at.isoformat() + "Z" if match.proposed_end_at else None,
            }
        )

    return upcoming_matches


@dashboard_bp.get("/me/dashboard")
def get_my_dashboard():
    user_id = _get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    account = Account.query.filter_by(id=user_id).first()
    if not account:
        return jsonify({"message": "Account not found"}), 404

    clubs_map = {}

    club_owner = ClubOwner.query.filter_by(id=user_id).first()

    if club_owner:
        owned_links = ClubOwnerClub.query.filter_by(
            club_owner_id=club_owner.id
        ).all()

        owned_ids = [link.club_id for link in owned_links]

        if owned_ids:
            owned_clubs = Club.query.filter(Club.id.in_(owned_ids)).all()

            for club in owned_clubs:
                clubs_map[club.id] = {
                    **club.serialize(),
                    "membership_status": "owner"
                }

    member_links = ClubPlayer.query.filter_by(player_id=user_id).all()
    member_ids = [link.club_id for link in member_links]

    if member_ids:
        member_clubs = Club.query.filter(Club.id.in_(member_ids)).all()

        for club in member_clubs:
            if club.id not in clubs_map:
                clubs_map[club.id] = {
                    **club.serialize(),
                    "membership_status": "member"
                }

    join_requests = ClubJoinRequest.query.filter_by(user_id=user_id).all()

    return jsonify({
        "account": {"id": account.id, "email": account.email},
        "roles": [getattr(account, "role", "user")],
        "clubs": list(clubs_map.values()),
        "upcoming_matches": _serialize_upcoming_matches(account),
        "pending_requests": {
            "my_requests": [r.serialize() for r in join_requests],
            "my_club_creation_requests": [],
        },
    }), 200

@dashboard_bp.get("/club/join-request")
def get_join_requests_for_owner():
    user_id = _get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    club_owner = ClubOwner.query.filter_by(id=user_id).first()
    if not club_owner:
        return jsonify({"message": "Not a club owner"}), 403

    owner_links = ClubOwnerClub.query.filter_by(club_owner_id=club_owner.id).all()
    club_ids = [link.club_id for link in owner_links]

    if not club_ids:
        return jsonify({"requests": []}), 200

    results = (
        db.session.query(ClubJoinRequest, Account.first_name)
        .join(Account, ClubJoinRequest.user_id == Account.id)
        .filter(ClubJoinRequest.club_id.in_(club_ids))
        .all()
    )

    data = []
    for request_obj, first_name in results:
        serialized = request_obj.serialize()
        serialized["user_name"] = first_name
        data.append(serialized)

    return jsonify({"requests": data}), 200


@dashboard_bp.post("/club/join-request")
def set_join():
    user_id = _get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    account = Account.query.filter_by(id=user_id).first()
    if not account:
        return jsonify({"message": "Account not found"}), 404
    
    data = request.get_json() or {}
    club_id = data.get("club_id")
    if not club_id:
        return jsonify({"message": "Club not found"}), 404

    club = Club.query.filter_by(id=club_id).first()
    if not club:
        return jsonify({"message": "Club not found"}), 404
    
    if ClubJoinRequest.query.filter_by(club_id=club_id, user_id=user_id).first():
        return jsonify({"status": True}), 200

    join_request = ClubJoinRequest(
        club_id=club_id,
        user_id=user_id,
        date = datetime.now(timezone.utc)
    )

    db.session.add(join_request)
    db.session.commit()

    player_name = account.first_name or account.email
    send_join_request_confirmation_to_player(
        player_email=account.email,
        player_name=player_name,
        club_name=club.name,
        club_id=club.id,
    )

    owner_rows = (
        db.session.query(Account.email, Account.first_name)
        .join(ClubOwner, ClubOwner.id == Account.id)
        .join(ClubOwnerClub, ClubOwnerClub.club_owner_id == ClubOwner.id)
        .filter(ClubOwnerClub.club_id == club.id)
        .all()
    )
    for owner_email, owner_first_name in owner_rows:
        send_join_request_notification_to_owner(
            owner_email=owner_email,
            owner_name=owner_first_name or owner_email,
            player_name=player_name,
            club_name=club.name,
            club_id=club.id,
        )
    
    return jsonify({"status": True}), 200


@dashboard_bp.post("/club/join-request/decide")
def decide_request():
    owner_id = _get_current_user_id_from_cookie()
    if not owner_id:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()
    club_id = data.get("club_id")
    player_id = data.get("user_id")
    decision = data.get("status")

    if not club_id or not player_id or not decision:
        return jsonify({"message": "Missing identifiers or status"}), 400

    join_req = ClubJoinRequest.query.filter_by(club_id=club_id, user_id=player_id).first()
    if not join_req:
        return jsonify({"message": "Join request not found"}), 404

    player_user = Account.query.filter_by(id=player_id).first()
    if not player_user:
        return jsonify({"message": "Account not found"}), 404

    club = Club.query.filter_by(id=club_id).first()
    if not club:
        return jsonify({"message": "Club not found"}), 404

    # Security
    is_owner = ClubOwnerClub.query.filter_by(
        club_owner_id=owner_id, 
        club_id=club_id
    ).first()
    
    if not is_owner:
        return jsonify({"message": "You do not have permission to manage this club"}), 403

    if decision == "approved":
        existing_player = Player.query.filter_by(id=player_id).first()
        if not existing_player:
            new_player = Player(id=player_id)
            db.session.add(new_player)
            db.session.flush() 
        
        club_link = ClubPlayer(club_id=club_id, player_id=player_id)
        db.session.add(club_link)

    db.session.delete(join_req)
    db.session.commit()

    send_join_request_decision_to_player(
        player_email=player_user.email,
        player_name=player_user.first_name or player_user.email,
        club_name=club.name,
        decision=decision,
        club_id=club.id,
    )
    
    return jsonify({"status": True, "message": f"Request {decision}"}), 200

@dashboard_bp.post("/club/add-club")
def add_club():
    user_id = _get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()

    required_fields = ["name", "description", "sport_type_id", "city"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({"message": f"Missing fields: {missing}"}), 400

    try:
            club = Club(
                name=data["name"],
                description=data["description"],
                sport_type_id=data["sport_type_id"],
                city=data["city"]
            )

            db.session.add(club)
            db.session.flush()

            club_owner = ClubOwner.query.filter_by(id=user_id).first()

            if not club_owner:
                club_owner = ClubOwner(id=user_id)
                db.session.add(club_owner)
                db.session.flush()

            club_owner_club = ClubOwnerClub(
                club_owner_id=club_owner.id,
                club_id=club.id
            )
        
            db.session.add(club_owner_club)
            db.session.flush()

            existing_player = Player.query.filter_by(id=user_id).first()
            if not existing_player:
                new_player = Player(id=user_id)
                db.session.add(new_player)
                db.session.flush()
            
            club_link = ClubPlayer(club_id=club.id, player_id=user_id)
            db.session.add(club_link)

            db.session.commit()

            return jsonify({"status": True,}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
    
@dashboard_bp.get("/me/achievements")
def get_my_achievements():
    user_id = _get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    empty = {"wins": 0, "current_streak": 0, "best_streak": 0, "total_matches": 0}

    player = Player.query.filter_by(id=user_id).first()
    if not player:
        return jsonify(empty), 200

    team_ids = [t.id for t in player.teams]
    if not team_ids:
        return jsonify(empty), 200

    rows = (
        db.session.query(MatchProposal, MatchPlayed)
        .join(MatchPlayed, MatchProposal.id == MatchPlayed.id)
        .filter(
            db.or_(
                MatchProposal.team1_id.in_(team_ids),
                MatchProposal.team2_id.in_(team_ids),
            )
        )
        .order_by(MatchPlayed.played_at.asc())
        .all()
    )

    team_id_set = set(team_ids)
    outcomes = []
    for proposal, played in rows:
        t1_mine = proposal.team1_id in team_id_set
        t2_mine = proposal.team2_id in team_id_set
        if t1_mine and played.score_team1 > played.score_team2:
            outcomes.append(True)
        elif t2_mine and played.score_team2 > played.score_team1:
            outcomes.append(True)
        else:
            outcomes.append(False)

    total_matches = len(outcomes)
    total_wins = sum(outcomes)

    current_streak = 0
    for w in reversed(outcomes):
        if w:
            current_streak += 1
        else:
            break

    best_streak = 0
    streak = 0
    for w in outcomes:
        if w:
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0

    return jsonify({
        "wins": total_wins,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "total_matches": total_matches,
    }), 200


@dashboard_bp.post("/club/delete")
def delete_club():
    owner_id = _get_current_user_id_from_cookie()
    if not owner_id:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()
    club_id = data.get("club_id")

    if not club_id:
        return jsonify({"message": "Missing identifiers or status"}), 400
    
    club_to_delete = Club.query.get(club_id)
        
    if not club_to_delete:
        return jsonify({"message": "Club not found"}), 404
    
    is_owner = ClubOwnerClub.query.filter_by(
        club_owner_id=owner_id, 
        club_id=club_id
    ).first()
    
    if not is_owner:
        return jsonify({"message": "You do not have permission to manage this club"}), 403
    
    try:
        db.session.delete(club_to_delete)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Club '{club_to_delete.name}' has been deleted."
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while deleting the club", "error": str(e)}), 500
