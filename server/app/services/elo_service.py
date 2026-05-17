"""
Elo-style rating updates for ladder matches.

The service keeps ladder ratings stable by capping very large rating gaps,
using a different K-factor for new, normal, and elite teams, and then
recomputing ladder ranks after each result is applied.
"""

import math

from sqlalchemy.orm import aliased

from server.app.models.ladder_team import LadderTeam
from server.extensions import db


ELO_DIFFERENCE_CAP = 400
ELO_BASE = 10
ELO_SCALE = 400
DEFAULT_RATING = 1000


def roundHalfAwayFromZero(value: float) -> int:
    """Round a float to the nearest integer using half-away-from-zero."""
    if value >= 0:
        return int(math.floor(value + 0.5))
    return int(math.ceil(value - 0.5))


def expectedScore(player_rating: int, opponent_rating: int) -> float:
    """Return the expected score for the rating gap between two teams."""
    # Cap the rating gap so extreme mismatches do not produce huge swings.
    diff = max(-ELO_DIFFERENCE_CAP, min(ELO_DIFFERENCE_CAP, opponent_rating - player_rating))
    # A larger negative diff means the player is expected to win more often.
    return 1 / (1 + (ELO_BASE ** (diff / ELO_SCALE)))


def kFactor(rating: int, matches_played: int) -> int:
    """Return the Elo K-factor based on experience and rating strength."""
    # Newer teams move faster; very strong established teams move slower.
    if matches_played < 30:
        return 40
    if rating >= 2400:
        return 10
    return 20


def actualScore(score_for: int, score_against: int) -> float:
    """Convert a final score into the Elo win/draw/loss scale."""
    # Convert the final result into the Elo win/loss/draw scale.
    if score_for > score_against:
        return 1.0
    if score_for < score_against:
        return 0.0
    return 0.5


def recomputeLadderRanks(ladder_id: int) -> None:
    """Refresh the ladder ordering after rating changes."""
    # Rank is derived from rating, so any rating change requires a resort.
    rows = (
        LadderTeam.query
        .filter_by(ladder_id=ladder_id)
        .order_by(LadderTeam.rating.desc(), LadderTeam.team_id.asc())
        .all()
    )
    for rank, row in enumerate(rows, start=1):
        row.rank = rank


def apply_elo_for_match_result(team1_id: int, team2_id: int, score_team1: int, score_team2: int) -> list[dict]:
    """
    Apply Elo updates on every ladder where both teams participate.

    Returns a per-ladder update summary for observability/testing.
    """
    lt1 = aliased(LadderTeam)
    lt2 = aliased(LadderTeam)

    # A match may exist in multiple ladders; update every ladder where both
    # teams are present.
    ladder_pairs = (
        db.session.query(lt1, lt2)
        .join(
            lt2,
            (lt1.ladder_id == lt2.ladder_id) & (lt2.team_id == team2_id),
        )
        .filter(lt1.team_id == team1_id)
        .all()
    )

    if not ladder_pairs:
        return []

    # Compute the actual result once and reuse it for every ladder update.
    score1 = actualScore(score_team1, score_team2)
    score2 = actualScore(score_team2, score_team1)
    updates = []

    for row1, row2 in ladder_pairs:
        rating1 = row1.rating if row1.rating is not None else DEFAULT_RATING
        rating2 = row2.rating if row2.rating is not None else DEFAULT_RATING

        played1 = row1.matches_played or 0
        played2 = row2.matches_played or 0
        k1 = kFactor(rating1, played1)
        k2 = kFactor(rating2, played2)

        expected1 = expectedScore(rating1, rating2)
        expected2 = expectedScore(rating2, rating1)

        # Apply the rounded rating delta to each side independently.
        delta1 = roundHalfAwayFromZero(k1 * (score1 - expected1))
        delta2 = roundHalfAwayFromZero(k2 * (score2 - expected2))

        # Update both ladder rows before recomputing the rank order.
        row1.rating = rating1 + delta1
        row2.rating = rating2 + delta2
        row1.matches_played = played1 + 1
        row2.matches_played = played2 + 1

        recomputeLadderRanks(row1.ladder_id)

        updates.append(
            {
                "ladder_id": row1.ladder_id,
                "team1_delta": delta1,
                "team2_delta": delta2,
                "team1_rating": row1.rating,
                "team2_rating": row2.rating,
            }
        )

    return updates
