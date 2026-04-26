from datetime import date
from types import SimpleNamespace

import server.app.services.weekly_match_proposal_service as weekly_service


def rows(team_ids):
    return [
        SimpleNamespace(team_id=team_id, rank=index + 1, rating=1200 - index * 10)
        for index, team_id in enumerate(team_ids)
    ]


def test_pairing_default_is_adjacent_when_alternate_disabled(monkeypatch):
    monkeypatch.setattr(
        weekly_service,
        "use_alternate_pairing",
        lambda ladder_id, week_start_date, block_index: False,
    )
    pairs = list(
        weekly_service.pair_ladder_rows(
            rows([1, 2, 3, 4, 5, 6]),
            ladder_id=42,
            week_start_date=date(2026, 5, 4),
        )
    )
    assert [(a.team_id, b.team_id) for a, b in pairs] == [(1, 2), (3, 4), (5, 6)]


def test_pairing_alternate_stays_within_nearby_ranks(monkeypatch):
    monkeypatch.setattr(
        weekly_service,
        "use_alternate_pairing",
        lambda ladder_id, week_start_date, block_index: block_index == 0,
    )
    pairs = list(
        weekly_service.pair_ladder_rows(
            rows([1, 2, 3, 4, 5, 6]),
            ladder_id=42,
            week_start_date=date(2026, 5, 4),
        )
    )
    assert [(a.team_id, b.team_id) for a, b in pairs] == [(1, 3), (2, 4), (5, 6)]


def test_rematch_cooldown_requires_three_other_matches_for_both(monkeypatch):
    monkeypatch.setattr(weekly_service, "latest_pair_played_at", lambda team1_id, team2_id: date(2026, 5, 1))
    counts = {(10, 20): 3, (20, 10): 2}

    def fake_count(*, team1_id, excluded_opponent_id, since):
        return counts[(team1_id, excluded_opponent_id)]

    monkeypatch.setattr(weekly_service, "count_other_played_matches_since", fake_count)
    assert weekly_service.meets_rematch_cooldown(10, 20, required_other_matches=3) is False

    counts[(20, 10)] = 3
    assert weekly_service.meets_rematch_cooldown(10, 20, required_other_matches=3) is True
