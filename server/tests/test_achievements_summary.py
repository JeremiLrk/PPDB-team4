from math import isclose

from server.app.models.account import Account
from server.app.models.club import Club
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
from server.app.models.match import MatchPlayed, MatchProposal
from server.app.services.elo_service import (
    DEFAULT_RATING,
    actualScore,
    expectedScore,
    kFactor,
    roundHalfAwayFromZero,
)
from server.extensions import db
from sqlalchemy import or_


def _player_stats_from_history(team_ids: list[int], *, ladder_id: int | None = None):
    query = (
        db.session.query(MatchProposal, MatchPlayed)
        .join(MatchPlayed, MatchPlayed.id == MatchProposal.id)
        .filter(
            or_(
                MatchProposal.team1_id.in_(team_ids),
                MatchProposal.team2_id.in_(team_ids),
            )
        )
        .order_by(
            MatchPlayed.played_at.asc().nullslast(),
            MatchProposal.id.asc(),
        )
    )
    if ladder_id is not None:
        query = query.filter(MatchProposal.ladder_id == ladder_id)

    rows = query.all()
    outcomes: list[bool] = []
    for proposal, played in rows:
        team1_was_mine = proposal.team1_id in team_ids
        team2_was_mine = proposal.team2_id in team_ids
        win = (
            team1_was_mine and played.score_team1 > played.score_team2
        ) or (
            team2_was_mine and played.score_team2 > played.score_team1
        )
        outcomes.append(win)

    total_matches = len(outcomes)
    wins = sum(outcomes)

    current_streak = 0
    for win in reversed(outcomes):
        if win:
            current_streak += 1
        else:
            break

    best_streak = 0
    streak = 0
    for win in outcomes:
        if win:
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0

    return {
        "wins": wins,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "total_matches": total_matches,
        "win_rate": (wins / total_matches) if total_matches else 0.0,
    }


def _rank1_streaks_from_history(team_rows: list[LadderTeam], *, ladder_id: int):
    rows = (
        db.session.query(MatchProposal, MatchPlayed)
        .join(MatchPlayed, MatchPlayed.id == MatchProposal.id)
        .filter(MatchProposal.ladder_id == ladder_id)
        .order_by(
            MatchPlayed.played_at.asc().nullslast(),
            MatchProposal.id.asc(),
        )
        .all()
    )
    ratings = {
        row.team_id: row.rating if row.rating is not None else DEFAULT_RATING
        for row in team_rows
    }
    played_counts = {row.team_id: row.matches_played or 0 for row in team_rows}
    current_streaks = {row.team_id: 0 for row in team_rows}
    best_streaks = {row.team_id: 0 for row in team_rows}

    for proposal, played in rows:
        if proposal.team1_id not in ratings or proposal.team2_id not in ratings:
            continue

        rating1 = ratings[proposal.team1_id]
        rating2 = ratings[proposal.team2_id]
        delta1 = roundHalfAwayFromZero(
            kFactor(rating1, played_counts[proposal.team1_id])
            * (actualScore(played.score_team1, played.score_team2) - expectedScore(rating1, rating2))
        )
        delta2 = roundHalfAwayFromZero(
            kFactor(rating2, played_counts[proposal.team2_id])
            * (actualScore(played.score_team2, played.score_team1) - expectedScore(rating2, rating1))
        )

        ratings[proposal.team1_id] += delta1
        ratings[proposal.team2_id] += delta2
        played_counts[proposal.team1_id] += 1
        played_counts[proposal.team2_id] += 1

        leader_id = max(ratings.items(), key=lambda item: (item[1], -item[0]))[0]
        for team_id in ratings:
            if team_id == leader_id:
                current_streaks[team_id] += 1
                best_streaks[team_id] = max(best_streaks[team_id], current_streaks[team_id])
            else:
                current_streaks[team_id] = 0

    return best_streaks


# Verifies dashboard achievements match seeded player history.
def test_dashboard_achievements_match_seeded_player_history(seeded_client, seeded_app):
    response = seeded_client.post(
        "/api/login",
        json={"email": "alice.moore@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200

    with seeded_app.app_context():
        account = Account.query.filter_by(email="alice.moore@example.com").first()
        assert account is not None
        expected = _player_stats_from_history([team.id for team in account.player.teams])

    achievements = seeded_client.get("/api/me/achievements")
    assert achievements.status_code == 200
    payload = achievements.get_json()

    assert payload["wins"] == expected["wins"] == 10
    assert payload["current_streak"] == expected["current_streak"] == 10
    assert payload["best_streak"] == expected["best_streak"] == 10
    assert payload["total_matches"] == expected["total_matches"] == 10
    assert isclose(expected["win_rate"], 1.0)


# Verifies ladder players expose seeded win and streak stats.
def test_ladder_players_expose_seeded_win_and_streak_stats(seeded_client, seeded_app):
    with seeded_app.app_context():
        club = Club.query.filter_by(name="NetRank Club").first()
        ladder = Ladder.query.filter_by(name="Men's Singles").first()
        assert club is not None
        assert ladder is not None

        team_one = Account.query.filter_by(email="alice.moore@example.com").first()
        team_two = Account.query.filter_by(email="bob.taylor@example.com").first()
        assert team_one is not None
        assert team_two is not None

        team_one_id = team_one.player.teams[0].id
        team_two_id = team_two.player.teams[0].id
        team_one_stats = _player_stats_from_history([team_one_id], ladder_id=ladder.id)
        team_two_stats = _player_stats_from_history([team_two_id], ladder_id=ladder.id)
        ladder_team_rows = LadderTeam.query.filter_by(ladder_id=ladder.id).all()
        rank1_streaks = _rank1_streaks_from_history(
            ladder_team_rows,
            ladder_id=ladder.id,
        )

    response = seeded_client.get(f"/api/clubs/{club.id}/ladders/{ladder.id}/players")
    assert response.status_code == 200
    payload = response.get_json()

    aces = next(row for row in payload if row["name"] == "NetRank Aces")
    juniors = next(row for row in payload if row["name"] == "NetRank Juniors")

    assert aces["wins"] == team_one_stats["wins"]
    assert aces["win_streak"] == team_one_stats["current_streak"]
    assert aces["best_win_streak"] == team_one_stats["best_streak"]
    assert aces["best_rank1_streak"] == rank1_streaks[team_one_id]
    assert isclose(aces["win_rate"], team_one_stats["win_rate"])

    assert juniors["wins"] == team_two_stats["wins"]
    assert juniors["win_streak"] == team_two_stats["current_streak"]
    assert juniors["best_win_streak"] == team_two_stats["best_streak"]
    assert juniors["best_rank1_streak"] == rank1_streaks[team_two_id]
    assert isclose(juniors["win_rate"], team_two_stats["win_rate"])


# Verifies U14 rank reigns use the ladder's stored rating baseline, not a flat 1000 rating reset.
def test_u14_rank1_reign_matches_seeded_ladder_order(seeded_client, seeded_app):
    with seeded_app.app_context():
        club = Club.query.filter_by(name="NetRank Club").first()
        ladder = Ladder.query.filter_by(name="U14 Singles").first()
        assert club is not None
        assert ladder is not None

    response = seeded_client.get(f"/api/clubs/{club.id}/ladders/{ladder.id}/players")
    assert response.status_code == 200
    payload = response.get_json()

    juniors = next(row for row in payload if row["name"] == "NetRank Juniors")
    aces = next(row for row in payload if row["name"] == "NetRank Aces")

    assert juniors["best_rank1_streak"] == 10
    assert aces["best_rank1_streak"] == 0
