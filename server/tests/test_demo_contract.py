from flask.testing import FlaskClient


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


def test_dashboard_texts_exist_for_en_and_nl(client: FlaskClient):
    en_response = client.get("/api/texts/page/dashboard?lang=en")
    nl_response = client.get("/api/texts/page/dashboard?lang=nl")

    assert en_response.status_code == 200
    assert nl_response.status_code == 200

    en_texts = en_response.get_json()
    nl_texts = nl_response.get_json()
    assert isinstance(en_texts, dict)
    assert isinstance(nl_texts, dict)

    assert "tab_overview" in en_texts
    assert "tab_overview" in nl_texts
    assert en_texts["tab_overview"] != nl_texts["tab_overview"]
