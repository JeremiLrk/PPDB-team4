from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from server.app.models.availability_block import AvailabilityBlock
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
from server.app.models.match import MatchProposal, MatchStatus
from server.app.models.team import Team
from server.extensions import db


DEFAULT_MATCH_DURATION_MINUTES = 60


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


def generate_weekly_match_proposals(
    proposed_by_user_id: int,
    *,
    week_start_date: date | None = None,
    ladder_id: int | None = None,
    managed_team_ids: set[int] | None = None,
    duration_minutes: int = DEFAULT_MATCH_DURATION_MINUTES,
    location: str | None = None,
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
    week_end_exclusive = target_week_start + timedelta(days=7)
    week_start_at = datetime.combine(target_week_start, time.min)
    week_end_at = datetime.combine(week_end_exclusive, time.min)
    duration = timedelta(minutes=duration_minutes)

    pending_status = _resolve_status("pending")
    if not pending_status:
        raise RuntimeError("Missing reference data: match status 'pending' was not seeded.")

    ladders = _load_ladders(ladder_id)
    created = []
    skipped = []

    for ladder in ladders:
        ladder_rows = _load_ladder_rows(ladder.id)
        # Weekly proposals are deterministic: adjacent ladder ranks are paired
        # and the DB uniqueness constraint prevents duplicates for that week.
        for first_row, second_row in _pair_ladder_rows(ladder_rows):
            team1 = db.session.get(Team, first_row.team_id)
            team2 = db.session.get(Team, second_row.team_id)

            if not team1 or not team2:
                skipped.append(_skip(ladder.id, first_row.team_id, second_row.team_id, "team_not_found"))
                continue

            if managed_team_ids is not None and team1.id not in managed_team_ids and team2.id not in managed_team_ids:
                skipped.append(_skip(ladder.id, team1.id, team2.id, "not_managed"))
                continue

            ordered_team1_id, ordered_team2_id = sorted((team1.id, team2.id))
            existing = MatchProposal.query.filter_by(
                week_start_date=target_week_start,
                team1_id=ordered_team1_id,
                team2_id=ordered_team2_id,
            ).first()
            if existing:
                skipped.append(_skip(ladder.id, team1.id, team2.id, "already_exists", existing.id))
                continue

            # A team is available only when every player on that team has an
            # overlapping block; then both team windows must overlap too.
            common_window = _find_common_team_window(team1, team2, week_start_at, week_end_at, duration)
            if not common_window:
                skipped.append(_skip(ladder.id, team1.id, team2.id, "no_common_availability"))
                continue

            sport_type_id = ladder.sport_type_id or team1.sport_type_id or team2.sport_type_id
            if not sport_type_id:
                skipped.append(_skip(ladder.id, team1.id, team2.id, "missing_sport_type"))
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


def _resolve_status(name: str):
    return MatchStatus.query.filter(MatchStatus.name.ilike(name)).first()


def _load_ladders(ladder_id: int | None) -> list[Ladder]:
    query = Ladder.query
    if ladder_id is not None:
        query = query.filter(Ladder.id == ladder_id)
    return query.order_by(Ladder.id.asc()).all()


def _load_ladder_rows(ladder_id: int) -> list[LadderTeam]:
    return (
        LadderTeam.query.filter_by(ladder_id=ladder_id)
        .order_by(LadderTeam.rank.asc(), LadderTeam.rating.desc(), LadderTeam.team_id.asc())
        .all()
    )


def _pair_ladder_rows(rows: list[LadderTeam]):
    for index in range(0, len(rows) - 1, 2):
        yield rows[index], rows[index + 1]


def _find_common_team_window(
    team1: Team,
    team2: Team,
    week_start_at: datetime,
    week_end_at: datetime,
    duration: timedelta,
) -> TimeWindow | None:
    team1_windows = _team_available_windows(team1, week_start_at, week_end_at)
    team2_windows = _team_available_windows(team2, week_start_at, week_end_at)

    for window in _intersect_window_lists(team1_windows, team2_windows):
        if window.end - window.start >= duration:
            return window
    return None


def _team_available_windows(team: Team, week_start_at: datetime, week_end_at: datetime) -> list[TimeWindow]:
    player_ids = [player.id for player in team.players]
    if not player_ids:
        return []

    team_windows = None
    for player_id in player_ids:
        player_windows = _player_available_windows(player_id, week_start_at, week_end_at)
        if not player_windows:
            return []
        team_windows = player_windows if team_windows is None else _intersect_window_lists(team_windows, player_windows)

    return team_windows or []


def _player_available_windows(player_id: int, week_start_at: datetime, week_end_at: datetime) -> list[TimeWindow]:
    blocks = (
        AvailabilityBlock.query.filter(
            AvailabilityBlock.user_id == player_id,
            AvailabilityBlock.start_at < week_end_at,
            AvailabilityBlock.end_at > week_start_at,
        )
        .order_by(AvailabilityBlock.start_at.asc())
        .all()
    )

    windows = [
        TimeWindow(
            start=max(block.start_at, week_start_at),
            end=min(block.end_at, week_end_at),
        )
        for block in blocks
        if max(block.start_at, week_start_at) < min(block.end_at, week_end_at)
    ]
    return _merge_windows(windows)


def _merge_windows(windows: list[TimeWindow]) -> list[TimeWindow]:
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


def _intersect_window_lists(first: list[TimeWindow], second: list[TimeWindow]) -> list[TimeWindow]:
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


def _skip(ladder_id: int, team1_id: int, team2_id: int, reason: str, proposal_id: int | None = None) -> dict:
    skipped = {
        "ladder_id": ladder_id,
        "team1_id": team1_id,
        "team2_id": team2_id,
        "reason": reason,
    }
    if proposal_id is not None:
        skipped["proposal_id"] = proposal_id
    return skipped
