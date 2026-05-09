from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import hashlib

from server.app.models.availability_block import AvailabilityBlock
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
from server.app.models.match import MatchPlayed, MatchProposal, MatchStatus, teams_share_players
from server.app.models.team import Team
from server.app.services.availability_service import weekly_window_for_block
from server.extensions import db


DEFAULT_MATCH_DURATION_MINUTES = 60
DEFAULT_AUTOGEN_MIN_LEAD_DAYS = 7
DEFAULT_MAX_PROPOSAL_LEAD_WEEKS = 2
DEFAULT_AUTOGEN_EARLIEST_HOUR = 8
DEFAULT_REMATCH_OTHER_MATCHES_REQUIRED = 3


@dataclass(frozen=True)
class TimeWindow:
    start: datetime
    end: datetime


def week_start_for(value: date | datetime) -> date:
    current_date = value.date() if isinstance(value, datetime) else value
    return current_date - timedelta(days=current_date.weekday())


def next_week_start(reference: date | None = None) -> date:
    today = reference or date.today()
    return week_start_for(today) + timedelta(days=7)


def latest_allowed_proposal_week_start(reference: date | None = None) -> date:
    return next_week_start(reference) + timedelta(weeks=DEFAULT_MAX_PROPOSAL_LEAD_WEEKS)


def generate_weekly_match_proposals(
    proposed_by_user_id: int,
    *,
    week_start_date: date | None = None,
    ladder_id: int | None = None,
    managed_team_ids: set[int] | None = None,
    duration_minutes: int = DEFAULT_MATCH_DURATION_MINUTES,
    location: str | None = None,
    generated_at: datetime | None = None,
) -> dict:
    """
    Generate pending match proposals for teams sharing a ladder.

    Teams are paired by ladder rank: #1 vs #2, #3 vs #4, etc. A proposal is
    created only when every player on both teams has an overlapping
    availability window long enough for the requested match duration.
    """
    if duration_minutes <= 0:
        raise ValueError("duration_minutes must be greater than zero.")

    target_week_start = week_start_date or next_week_start()
    reference_date = generated_at.date() if generated_at else date.today()
    if target_week_start > latest_allowed_proposal_week_start(reference_date):
        raise ValueError(
            f"week_start_date cannot be more than {DEFAULT_MAX_PROPOSAL_LEAD_WEEKS} weeks ahead."
        )
    week_end_exclusive = target_week_start + timedelta(days=7)
    week_start_at = datetime.combine(target_week_start, time.min)
    week_end_at = datetime.combine(week_end_exclusive, time.min)
    duration = timedelta(minutes=duration_minutes)
    not_before = None
    if week_start_date is None:
        # Automatic weekly runs keep a safety window before the earliest slot.
        not_before = auto_generation_not_before(generated_at or datetime.utcnow())

    pending_status = resolve_status("pending")
    if not pending_status:
        raise RuntimeError("Missing reference data: match status 'pending' was not seeded.")

    ladders = load_ladders(ladder_id)
    created = []
    skipped = []

    for ladder in ladders:
        ladder_rows = load_ladder_rows(ladder.id)
        # Weekly proposals keep nearby pairings with controlled variation:
        # mostly #1-#2 / #3-#4, sometimes #1-#3 / #2-#4.
        for first_row, second_row in pair_ladder_rows(
            ladder_rows,
            ladder_id=ladder.id,
            week_start_date=target_week_start,
        ):
            team1 = db.session.get(Team, first_row.team_id)
            team2 = db.session.get(Team, second_row.team_id)

            if not team1 or not team2:
                skipped.append(skip(ladder.id, first_row.team_id, second_row.team_id, "team_not_found"))
                continue

            if teams_share_players(team1, team2):
                skipped.append(skip(ladder.id, team1.id, team2.id, "shared_players"))
                continue

            if managed_team_ids is not None and team1.id not in managed_team_ids and team2.id not in managed_team_ids:
                skipped.append(skip(ladder.id, team1.id, team2.id, "not_managed"))
                continue

            ordered_team1_id, ordered_team2_id = sorted((team1.id, team2.id))
            existing = MatchProposal.query.filter_by(
                week_start_date=target_week_start,
                team1_id=ordered_team1_id,
                team2_id=ordered_team2_id,
            ).first()
            if existing:
                skipped.append(skip(ladder.id, team1.id, team2.id, "already_exists", existing.id))
                continue

            if not meets_rematch_cooldown(
                team1.id,
                team2.id,
                required_other_matches=DEFAULT_REMATCH_OTHER_MATCHES_REQUIRED,
            ):
                skipped.append(skip(ladder.id, team1.id, team2.id, "rematch_cooldown"))
                continue

            # A team is available only when every player on that team has an
            # overlapping block; then both team windows must overlap too.
            common_window = find_common_team_window(
                team1,
                team2,
                week_start_at,
                week_end_at,
                duration,
                not_before=not_before,
            )
            if not common_window:
                skipped.append(skip(ladder.id, team1.id, team2.id, "no_common_availability"))
                continue

            sport_type_id = ladder.sport_type_id or team1.sport_type_id or team2.sport_type_id
            if not sport_type_id:
                skipped.append(skip(ladder.id, team1.id, team2.id, "missing_sport_type"))
                continue

            proposal = MatchProposal(
                proposed_by_user_id=proposed_by_user_id,
                sport_type_id=sport_type_id,
                ruleset_id=ladder.ruleset_id,
                team1_id=ordered_team1_id,
                team2_id=ordered_team2_id,
                status_id=pending_status.id,
                week_start_date=target_week_start,
                proposed_start_at=common_window.start,
                proposed_end_at=common_window.start + duration,
                location=location,
            )
            db.session.add(proposal)
            db.session.flush()
            created.append(proposal)

    db.session.commit()

    return {
        "week_start_date": target_week_start.isoformat(),
        "created": [proposal.to_dict() for proposal in created],
        "created_count": len(created),
        "skipped": skipped,
        "skipped_count": len(skipped),
    }


def resolve_status(name: str):
    return MatchStatus.query.filter(MatchStatus.name.ilike(name)).first()


def load_ladders(ladder_id: int | None) -> list[Ladder]:
    query = Ladder.query
    if ladder_id is not None:
        query = query.filter(Ladder.id == ladder_id)
    return query.order_by(Ladder.id.asc()).all()


def load_ladder_rows(ladder_id: int) -> list[LadderTeam]:
    return (
        LadderTeam.query.filter_by(ladder_id=ladder_id)
        .order_by(LadderTeam.rank.asc(), LadderTeam.rating.desc(), LadderTeam.team_id.asc())
        .all()
    )


def pair_ladder_rows(rows: list[LadderTeam], *, ladder_id: int, week_start_date: date):
    index = 0
    while index + 3 < len(rows):
        block = rows[index:index + 4]
        if use_alternate_pairing(ladder_id, week_start_date, block_index=index // 4):
            # Controlled randomization without big jumps: top team may face #3,
            # but never #4 from the same block.
            yield block[0], block[2]
            yield block[1], block[3]
        else:
            yield block[0], block[1]
            yield block[2], block[3]
        index += 4

    for leftover_index in range(index, len(rows) - 1, 2):
        yield rows[leftover_index], rows[leftover_index + 1]


def use_alternate_pairing(ladder_id: int, week_start_date: date, *, block_index: int) -> bool:
    """
    Deterministic per (ladder, week, block) with ~30% alternate frequency.
    """
    token = f"{ladder_id}:{week_start_date.isoformat()}:{block_index}".encode("utf-8")
    bucket = hashlib.sha256(token).digest()[0] % 10
    return bucket < 3


def find_common_team_window(
    team1: Team,
    team2: Team,
    week_start_at: datetime,
    week_end_at: datetime,
    duration: timedelta,
    not_before: datetime | None = None,
) -> TimeWindow | None:
    team1_windows = team_available_windows(team1, week_start_at, week_end_at)
    team2_windows = team_available_windows(team2, week_start_at, week_end_at)

    for window in intersect_window_lists(team1_windows, team2_windows):
        candidate_start = window.start
        if not_before and candidate_start < not_before:
            candidate_start = not_before
        if window.end - candidate_start >= duration:
            return TimeWindow(start=candidate_start, end=window.end)
    return None


def meets_rematch_cooldown(team1_id: int, team2_id: int, *, required_other_matches: int) -> bool:
    latest_played_at = latest_pair_played_at(team1_id, team2_id)
    if latest_played_at is None:
        return True

    team1_other_count = count_other_played_matches_since(
        team1_id=team1_id,
        excluded_opponent_id=team2_id,
        since=latest_played_at,
    )
    team2_other_count = count_other_played_matches_since(
        team1_id=team2_id,
        excluded_opponent_id=team1_id,
        since=latest_played_at,
    )
    return team1_other_count >= required_other_matches and team2_other_count >= required_other_matches


def latest_pair_played_at(team1_id: int, team2_id: int) -> datetime | None:
    ordered_team1_id, ordered_team2_id = sorted((team1_id, team2_id))
    latest = (
        db.session.query(MatchPlayed.played_at)
        .join(MatchProposal, MatchProposal.id == MatchPlayed.id)
        .filter(
            MatchProposal.team1_id == ordered_team1_id,
            MatchProposal.team2_id == ordered_team2_id,
            MatchProposal.status_id == MatchStatus.PLAYED,
        )
        .order_by(MatchPlayed.played_at.desc(), MatchProposal.id.desc())
        .first()
    )
    return latest[0] if latest else None


def count_other_played_matches_since(
    *,
    team1_id: int,
    excluded_opponent_id: int,
    since: datetime,
) -> int:
    played_matches = (
        db.session.query(MatchProposal.team1_id, MatchProposal.team2_id)
        .join(MatchPlayed, MatchPlayed.id == MatchProposal.id)
        .filter(
            MatchProposal.status_id == MatchStatus.PLAYED,
            MatchPlayed.played_at > since,
            db.or_(
                MatchProposal.team1_id == team1_id,
                MatchProposal.team2_id == team1_id,
            ),
        )
        .all()
    )

    count = 0
    for left_team_id, right_team_id in played_matches:
        opponent_id = right_team_id if left_team_id == team1_id else left_team_id
        if opponent_id != excluded_opponent_id:
            count += 1
    return count


def auto_generation_not_before(generated_at: datetime) -> datetime:
    threshold = generated_at + timedelta(days=DEFAULT_AUTOGEN_MIN_LEAD_DAYS)
    earliest_on_threshold_day = datetime.combine(
        threshold.date(),
        time(hour=DEFAULT_AUTOGEN_EARLIEST_HOUR),
    )
    if threshold < earliest_on_threshold_day:
        return earliest_on_threshold_day
    return threshold


def team_available_windows(team: Team, week_start_at: datetime, week_end_at: datetime) -> list[TimeWindow]:
    player_ids = [player.id for player in team.players]
    if not player_ids:
        return []

    team_windows = None
    for player_id in player_ids:
        player_windows = player_available_windows(player_id, week_start_at, week_end_at)
        if not player_windows:
            return []
        team_windows = player_windows if team_windows is None else intersect_window_lists(team_windows, player_windows)

    return team_windows or []


def player_available_windows(player_id: int, week_start_at: datetime, week_end_at: datetime) -> list[TimeWindow]:
    blocks = (
        AvailabilityBlock.query.filter_by(user_id=player_id)
        .order_by(AvailabilityBlock.weekday.asc(), AvailabilityBlock.start_time.asc(), AvailabilityBlock.id.asc())
        .all()
    )

    windows = []
    for block in blocks:
        block_window = weekly_window_for_block(block, week_start_at.date())
        if block_window is None:
            continue

        start_at, end_at = block_window
        if start_at < week_end_at and end_at > week_start_at:
            windows.append(
                TimeWindow(
                    start=max(start_at, week_start_at),
                    end=min(end_at, week_end_at),
                )
            )
    return merge_windows(windows)


def merge_windows(windows: list[TimeWindow]) -> list[TimeWindow]:
    if not windows:
        return []

    ordered = sorted(windows, key=lambda window: (window.start, window.end))
    merged = [ordered[0]]

    for window in ordered[1:]:
        previous = merged[-1]
        if window.start <= previous.end:
            merged[-1] = TimeWindow(start=previous.start, end=max(previous.end, window.end))
        else:
            merged.append(window)

    return merged


def intersect_window_lists(first: list[TimeWindow], second: list[TimeWindow]) -> list[TimeWindow]:
    intersections = []
    left = 0
    right = 0

    while left < len(first) and right < len(second):
        start = max(first[left].start, second[right].start)
        end = min(first[left].end, second[right].end)
        if start < end:
            intersections.append(TimeWindow(start=start, end=end))

        if first[left].end <= second[right].end:
            left += 1
        else:
            right += 1

    return intersections


def skip(ladder_id: int, team1_id: int, team2_id: int, reason: str, proposal_id: int | None = None) -> dict:
    skipped = {
        "ladder_id": ladder_id,
        "team1_id": team1_id,
        "team2_id": team2_id,
        "reason": reason,
    }
    if proposal_id is not None:
        skipped["proposal_id"] = proposal_id
    return skipped
