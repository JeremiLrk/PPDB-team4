from pathlib import Path

from flask.testing import FlaskClient


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


def test_demo_club_exists_in_clubs_endpoint(seeded_client: FlaskClient):
    club_id = _get_netrank_club_id(seeded_client)
    assert club_id > 0


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


def test_dashboard_texts_exist_for_en_and_nl():
    en_dashboard = (TRANSLATION_ROOT / "en" / "LC_MESSAGES" / "dashboard.po").read_text(encoding="utf-8")
    nl_dashboard = (TRANSLATION_ROOT / "nl" / "LC_MESSAGES" / "dashboard.po").read_text(encoding="utf-8")

    assert 'msgid "dashboard.tab_overview"' in en_dashboard
    assert 'msgid "dashboard.tab_overview"' in nl_dashboard
    assert 'msgstr "Overview"' in en_dashboard
    assert 'msgstr "Overzicht"' in nl_dashboard


def test_matches_texts_exist_for_en_and_nl():
    en_matches = (TRANSLATION_ROOT / "en" / "LC_MESSAGES" / "matches.po").read_text(encoding="utf-8")
    nl_matches = (TRANSLATION_ROOT / "nl" / "LC_MESSAGES" / "matches.po").read_text(encoding="utf-8")

    assert 'msgid "matches.title"' in en_matches
    assert 'msgid "matches.title"' in nl_matches
    assert 'msgid "matches.reset_pending"' in en_matches
    assert 'msgid "matches.reset_pending"' in nl_matches
    assert 'msgstr "Set back to pending"' in en_matches
    assert 'msgstr "Opnieuw in afwachting zetten"' in nl_matches
