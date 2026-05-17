from server.app.models.team import Team
from server.app.models.ladder_team import LadderTeam
from server.app.models.match import MatchPlayed, MatchProposal
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
    """Return per-team win and streak stats for a ladder.

    The ladder page shows "Most wins" and "Best win streak" cards, so the
    values need to be derived from actual resolved matches rather than from
    the seeded rating rows alone.
    """
    rows = get_all_players_ladder(ladder_id)
    stats = {
        team.id: {
            "wins": 0,
            "win_streak": 0,
            "best_win_streak": 0,
            "matches_played": 0,
        }
        for team, _ladder_team in rows
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

    return stats
