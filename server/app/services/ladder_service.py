from server.app.models.team import Team
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

def get_all_players_ladder(ladder_id: int):
    return (
        db.session.query(Team, LadderTeam)
        .join(LadderTeam, Team.id == LadderTeam.team_id)
        .filter(LadderTeam.ladder_id == ladder_id)
        .order_by(LadderTeam.rank)
        .all()
    )


def get_ladder_player_achievement_stats(ladder_id: int) -> dict[int, dict]:
    """Return per-team achievement stats for a ladder.

    The ladder page shows achievement cards derived from resolved matches.
    """
    rows = get_all_players_ladder(ladder_id)
    stats = {
        team.id: {
            "wins": 0,
            "win_streak": 0,
            "best_win_streak": 0,
            "rank1_streak": 0,
            "best_rank1_streak": 0,
            "matches_played": 0,
        }
        for team, _ladder_team in rows
    }
    simulated_rows = {
        team.id: {
            "rating": ladder_team.rating if ladder_team.rating is not None else DEFAULT_RATING,
            "matches_played": ladder_team.matches_played or 0,
        }
        for team, ladder_team in rows
    }

    played_rows = (
        db.session.query(MatchProposal, MatchPlayed)
        .join(MatchPlayed, MatchPlayed.id == MatchProposal.id)
        .filter(MatchProposal.ladder_id == ladder_id)
        .order_by(
            MatchPlayed.played_at.asc().nullslast(),
            MatchProposal.id.asc(),
        )
        .all()
    )

    for proposal, played in played_rows:
        team1_stats = stats.get(proposal.team1_id)
        team2_stats = stats.get(proposal.team2_id)
        if team1_stats is None or team2_stats is None:
            continue

        team1_stats["matches_played"] += 1
        team2_stats["matches_played"] += 1

        if played.score_team1 > played.score_team2:
            team1_stats["wins"] += 1
            team1_stats["win_streak"] += 1
            team2_stats["win_streak"] = 0
            team1_stats["best_win_streak"] = max(team1_stats["best_win_streak"], team1_stats["win_streak"])
        elif played.score_team2 > played.score_team1:
            team2_stats["wins"] += 1
            team2_stats["win_streak"] += 1
            team1_stats["win_streak"] = 0
            team2_stats["best_win_streak"] = max(team2_stats["best_win_streak"], team2_stats["win_streak"])
        else:
            # Draws reset the active streak without adding a win.
            team1_stats["win_streak"] = 0
            team2_stats["win_streak"] = 0

        apply_simulated_ladder_result(simulated_rows, proposal, played)
        leader_id = _simulated_rank1_team_id(simulated_rows)
        for team_id, team_stats in stats.items():
            if team_id == leader_id:
                team_stats["rank1_streak"] += 1
                team_stats["best_rank1_streak"] = max(
                    team_stats["best_rank1_streak"],
                    team_stats["rank1_streak"],
                )
            else:
                team_stats["rank1_streak"] = 0

    return stats


def apply_simulated_ladder_result(
    simulated_rows: dict[int, dict],
    proposal: MatchProposal,
    played: MatchPlayed,
) -> None:
    """Apply a pure in-memory Elo update for achievement history."""
    row1 = simulated_rows.get(proposal.team1_id)
    row2 = simulated_rows.get(proposal.team2_id)
    if row1 is None or row2 is None:
        return

    score1 = actualScore(played.score_team1, played.score_team2)
    score2 = actualScore(played.score_team2, played.score_team1)
    expected1 = expectedScore(row1["rating"], row2["rating"])
    expected2 = expectedScore(row2["rating"], row1["rating"])
    delta1 = roundHalfAwayFromZero(kFactor(row1["rating"], row1["matches_played"]) * (score1 - expected1))
    delta2 = roundHalfAwayFromZero(kFactor(row2["rating"], row2["matches_played"]) * (score2 - expected2))

    row1["rating"] += delta1
    row2["rating"] += delta2
    row1["matches_played"] += 1
    row2["matches_played"] += 1


def _simulated_rank1_team_id(simulated_rows: dict[int, dict]) -> int | None:
    if not simulated_rows:
        return None
    return max(
        simulated_rows.items(),
        key=lambda item: (item[1]["rating"], -item[0]),
    )[0]
