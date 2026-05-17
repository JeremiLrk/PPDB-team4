from pathlib import Path

from flask.testing import FlaskClient

from server.app.models.account import Account
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
from server.app.models.match import MatchProposal, MatchStatus
from server.app.models.player import PlayerTeam
from server.app.models.team import Team, TeamManagerTeam
from server.extensions import db


TRANSLATION_ROOT = Path(__file__).resolve().parents[1] / "translations"


def _get_netrank_club_id(client: FlaskClient) -> int:
    response = client.get("/api/clubs")
    assert response.status_code == 200

    payload = response.get_json()
    assert isinstance(payload, dict)
    clubs = payload.get("clubs", [])
    assert isinstance(clubs, list)

    target = next((club for club in clubs if club.get("name") == "NetRank Club"), None)
    assert target is not None, "Expected seeded club 'NetRank Club' to exist."
    assert isinstance(target.get("id"), int)
    return target["id"]


# Verifies demo club exists in clubs endpoint.
def test_demo_club_exists_in_clubs_endpoint(seeded_client: FlaskClient):
    club_id = _get_netrank_club_id(seeded_client)
    assert club_id > 0


# Verifies demo ladders include expected names.
def test_demo_ladders_include_expected_names(seeded_client: FlaskClient):
    club_id = _get_netrank_club_id(seeded_client)
    response = seeded_client.get(f"/api/clubs/{club_id}/ladders")
    assert response.status_code == 200

    payload = response.get_json()
    assert isinstance(payload, dict)
    ladders = payload.get("ladders", [])
    assert isinstance(ladders, list)
    assert len(ladders) >= 2

    ladder_names = {ladder.get("name") for ladder in ladders}
    assert "Men's Singles" in ladder_names
    assert "U14 Singles" in ladder_names


# Verifies manager only demo match is seeded.
def test_manager_only_demo_match_is_seeded(seeded_app):
    with seeded_app.app_context():
        ladder = Ladder.query.filter_by(name="Manager Demo Singles").first()
        assert ladder is not None

        rows = (
            LadderTeam.query.filter_by(ladder_id=ladder.id)
            .order_by(LadderTeam.rank.asc())
            .all()
        )
        team_names = [db.session.get(Team, row.team_id).name for row in rows]
        assert team_names == ["Manager Demo A", "Manager Demo B"]

        proposal = MatchProposal.query.filter_by(ladder_id=ladder.id).first()
        assert proposal is not None
        assert proposal.status_id == MatchStatus.ACCEPTED
        assert proposal.played is None

        jeremi = Account.query.filter_by(email="jeremilorek@outlook.com").first()
        lrk = Account.query.filter_by(email="lrk.j@outlook.com").first()
        assert jeremi is not None
        assert lrk is not None
        assert jeremi.team_manager is not None
        assert lrk.team_manager is not None

        assert TeamManagerTeam.query.filter_by(
            team_manager_id=jeremi.team_manager.id,
            team_id=rows[0].team_id,
        ).count() == 1
        assert TeamManagerTeam.query.filter_by(
            team_manager_id=lrk.team_manager.id,
            team_id=rows[1].team_id,
        ).count() == 1

        for team_name in team_names:
            team = Team.query.filter_by(name=team_name).first()
            assert team is not None
            assert PlayerTeam.query.filter_by(team_id=team.id).count() == 1

            assert jeremi.player is not None
            assert rows[0].team_id not in {team.id for team in jeremi.player.teams}
            assert lrk.player is None or rows[1].team_id not in {team.id for team in lrk.player.teams}


# Verifies manager only demo match score flow.
def test_manager_only_demo_match_score_flow(seeded_app, seeded_client: FlaskClient):
    with seeded_app.app_context():
        ladder = Ladder.query.filter_by(name="Manager Demo Singles").first()
        assert ladder is not None
        proposal = MatchProposal.query.filter_by(ladder_id=ladder.id).first()
        assert proposal is not None
        match_id = proposal.id

    login_jeremi = seeded_client.post(
        "/api/login",
        json={"email": "jeremilorek@outlook.com", "password": "qwertyuiop"},
    )
    assert login_jeremi.status_code == 200

    first = seeded_client.post(
        f"/api/matches/{match_id}/score",
        json={"score_team1": 2, "score_team2": 1},
    )
    assert first.status_code == 201
    first_body = first.get_json()
    assert first_body["submission"]["submittedByRole"] == "team1_side"
    assert first_body["finalized"] is False

    login_lrk = seeded_client.post(
        "/api/login",
        json={"email": "lrk.j@outlook.com", "password": "qwertyuiop"},
    )
    assert login_lrk.status_code == 200

    second = seeded_client.post(
        f"/api/matches/{match_id}/score",
        json={"score_team1": 2, "score_team2": 1},
    )
    assert second.status_code == 201
    second_body = second.get_json()
    assert second_body["submission"]["submittedByRole"] == "team2_side"
    assert second_body["finalized"] is True
    assert second_body["resolvedScore"] == {"scoreTeam1": 2, "scoreTeam2": 1}


# Verifies top players contract and sorting.
def test_top_players_contract_and_sorting(seeded_client: FlaskClient):
    club_id = _get_netrank_club_id(seeded_client)
    response = seeded_client.get(f"/api/clubs/{club_id}/top-players")
    assert response.status_code == 200

    payload = response.get_json()
    assert isinstance(payload, dict)
    players = payload.get("players", [])
    assert isinstance(players, list)
    assert len(players) > 0

    ratings = []
    for player in players:
        assert isinstance(player.get("id"), int)
        assert isinstance(player.get("name"), str)
        assert isinstance(player.get("rating"), int)
        ratings.append(player["rating"])

    assert ratings == sorted(ratings, reverse=True)


# Verifies club home summary contract.
def test_club_home_summary_contract(seeded_client: FlaskClient):
    club_id = _get_netrank_club_id(seeded_client)
    response = seeded_client.get(f"/api/clubs/{club_id}/home-summary")
    assert response.status_code == 200

    payload = response.get_json()
    assert isinstance(payload, dict)
    assert isinstance(payload.get("club"), dict)
    assert payload["club"]["id"] == club_id

    ladders = payload.get("ladders", [])
    performers = payload.get("performers", [])
    upcoming = payload.get("upcoming_matches", [])
    results = payload.get("latest_results", [])

    assert isinstance(ladders, list)
    assert isinstance(performers, list)
    assert isinstance(upcoming, list)
    assert isinstance(results, list)
    assert len(ladders) > 0
    assert len(performers) > 0
    assert len(upcoming) > 3
    assert len(results) > 0

    performer_ratings = [row["rating"] for row in performers]
    assert performer_ratings == sorted(performer_ratings, reverse=True)

    assert all(match.get("ladderName") for match in upcoming)
    assert all(match.get("ladderName") for match in results)
    assert all(match.get("status") == "accepted" for match in upcoming)
    assert all(match.get("status") == "played" for match in results)


# Verifies ladder detail contract.
def test_ladder_detail_contract(seeded_client: FlaskClient):
    club_id = _get_netrank_club_id(seeded_client)
    ladders_response = seeded_client.get(f"/api/clubs/{club_id}/ladders")
    assert ladders_response.status_code == 200
    ladders_payload = ladders_response.get_json()
    assert isinstance(ladders_payload, dict)
    ladders = ladders_payload.get("ladders", [])
    assert isinstance(ladders, list)
    assert len(ladders) > 0

    ladder_id = ladders[0]["id"]
    detail_response = seeded_client.get(f"/api/clubs/{club_id}/ladders/{ladder_id}")
    assert detail_response.status_code == 200

    rows = detail_response.get_json()
    assert isinstance(rows, list)
    assert len(rows) > 0

    for row in rows:
        assert isinstance(row.get("id"), int)
        assert isinstance(row.get("name"), str)
        assert isinstance(row.get("rating"), int)


# Verifies dashboard texts exist for en and nl.
def test_dashboard_texts_exist_for_en_and_nl():
    en_dashboard = (TRANSLATION_ROOT / "en" / "LC_MESSAGES" / "dashboard.po").read_text(encoding="utf-8")
    nl_dashboard = (TRANSLATION_ROOT / "nl" / "LC_MESSAGES" / "dashboard.po").read_text(encoding="utf-8")

    assert 'msgid "dashboard.tab_overview"' in en_dashboard
    assert 'msgid "dashboard.tab_overview"' in nl_dashboard
    assert 'msgstr "Overview"' in en_dashboard
    assert 'msgstr "Overzicht"' in nl_dashboard


# Verifies matches texts exist for en and nl.
def test_matches_texts_exist_for_en_and_nl():
    en_matches = (TRANSLATION_ROOT / "en" / "LC_MESSAGES" / "matches.po").read_text(encoding="utf-8")
    nl_matches = (TRANSLATION_ROOT / "nl" / "LC_MESSAGES" / "matches.po").read_text(encoding="utf-8")

    assert 'msgid "matches.title"' in en_matches
    assert 'msgid "matches.title"' in nl_matches
    assert 'msgid "matches.reset_pending"' in en_matches
    assert 'msgid "matches.reset_pending"' in nl_matches
    assert 'msgstr "Set back to pending"' in en_matches
    assert 'msgstr "Opnieuw in afwachting zetten"' in nl_matches
