"""
Unit tests for server/app/routes/team/_helpers.py

Covers:
  get_team_or_404
  resolve_target
  search_accounts
  count_confirmed_players
  count_effective_players
  handle_team_after_last_manager_removed
  ladders_exceeding_max_after_add
  ladders_violating_min_after_remove
"""

import pytest
from datetime import datetime, timezone

from server.extensions import db
from server.app.models.team import Team, TeamManagerTeam
from server.app.models.player import Player, PlayerTeam
from server.app.models.team_join_request import TeamJoinRequest
from server.app.models.match_rule import MatchRuleSet

from server.app.routes.team._helpers import (
    get_team_or_404,
    resolve_target,
    search_accounts,
    count_confirmed_players,
    count_effective_players,
    handle_team_after_last_manager_removed,
    ladders_exceeding_max_after_add,
    ladders_violating_min_after_remove,
)


# ---------------------------------------------------------------------------
# Shared factories
# ---------------------------------------------------------------------------

from server.tests.team.factories import (
    _make_account,
    _make_team,
    _make_team_manager,
    _make_assoc,
    _make_sport_type,
    _make_ladder,
    _enroll,
    _add_player_to_team, _role,
)


# ===========================================================================
# get_team_or_404
# ===========================================================================

class TestGetTeamOr404:

    # Verifies existing team is returned.
    def test_existing_team_is_returned(self, app):
        with app.app_context():
            team = _make_team(name="Helper Exists Team")
            team_id = team.id
            result = get_team_or_404(team_id)
            assert result.id == team_id
            db.session.rollback()

    # Verifies missing team aborts with 404.
    def test_missing_team_aborts_404(self, app):
        with app.app_context():
            with app.test_request_context():
                try:
                    get_team_or_404(9_999_999)
                    assert False, "expected abort"
                except Exception as exc:
                    assert getattr(exc, "code", None) == 404


# ===========================================================================
# resolve_target
# ===========================================================================

class TestResolveTarget:

    # Verifies valid account is returned.
    def test_valid_account_is_returned(self, app):
        with app.app_context():
            acc = _make_account(email="rt_valid@t.com")
            result = resolve_target(acc.id)
            assert result.id == acc.id
            db.session.rollback()

    # Verifies none account id aborts 422.
    def test_none_account_id_aborts_422(self, app):
        with app.app_context():
            with app.test_request_context():
                try:
                    resolve_target(None)
                    assert False, "expected abort"
                except Exception as exc:
                    assert getattr(exc, "code", None) == 422

    # Verifies unknown account id aborts 404.
    def test_unknown_account_id_aborts_404(self, app):
        with app.app_context():
            with app.test_request_context():
                try:
                    resolve_target(9_999_999)
                    assert False, "expected abort"
                except Exception as exc:
                    assert getattr(exc, "code", None) == 404


# ===========================================================================
# search_accounts
# ===========================================================================

class TestSearchAccounts:

    # Verifies an empty query returns an empty list.
    def test_empty_query_returns_empty_list(self, app):
        with app.app_context():
            assert search_accounts("", set()) == []
            db.session.rollback()

    # Verifies a whitespace-only query returns an empty list.
    def test_whitespace_only_returns_empty_list(self, app):
        with app.app_context():
            assert search_accounts("   ", set()) == []
            db.session.rollback()

    # Verifies find by exact integer id.
    def test_find_by_exact_integer_id(self, app):
        with app.app_context():
            acc = _make_account(email="sa_id@t.com")
            result = search_accounts(str(acc.id), set())
            assert any(r.id == acc.id for r in result)
            db.session.rollback()

    # Verifies find by exact email case insensitive.
    def test_find_by_exact_email_case_insensitive(self, app):
        with app.app_context():
            acc = _make_account(email="sa_email_exact@t.com")
            result = search_accounts("SA_EMAIL_EXACT@T.COM", set())
            assert any(r.id == acc.id for r in result)
            db.session.rollback()

    # Verifies excluded ids are not returned.
    def test_excluded_ids_are_not_returned(self, app):
        with app.app_context():
            acc = _make_account(email="sa_excl@t.com")
            result = search_accounts(str(acc.id), {acc.id})
            assert not any(r.id == acc.id for r in result)
            db.session.rollback()

    # Verifies integer string that matches no id falls through to name search.
    def test_integer_string_that_matches_no_id_falls_through_to_name_search(self, app):
        with app.app_context():
            # A numeric string that is not an existing ID should not raise
            result = search_accounts("999999999", set())
            assert isinstance(result, list)
            db.session.rollback()


# ===========================================================================
# count_confirmed_players
# ===========================================================================

class TestCountConfirmedPlayers:

    # Verifies no players returns zero.
    def test_no_players_returns_zero(self, app):
        with app.app_context():
            team = _make_team(name="Count0 Team")
            assert count_confirmed_players(team.id) == 0
            db.session.rollback()

    # Verifies counts only confirmed members.
    def test_counts_only_confirmed_members(self, app):
        with app.app_context():
            team = _make_team(name="Count2 Team")
            for i in range(2):
                _add_player_to_team(team, f"count_pl_{i}@t.com")
            assert count_confirmed_players(team.id) == 2
            db.session.rollback()


# ===========================================================================
# count_effective_players
# ===========================================================================

class TestCountEffectivePlayers:

    # Verifies counts confirmed plus pending.
    def test_counts_confirmed_plus_pending(self, app):
        with app.app_context():
            team = _make_team(name="EffPl Team")
            _add_player_to_team(team, "effpl_confirmed@t.com")
            acc2 = _make_account(email="effpl_pending@t.com")
            db.session.add(TeamJoinRequest(
                team_id=team.id,
                user_id=acc2.id,
                date=datetime.now(timezone.utc),
                status="pending",
            ))
            db.session.flush()
            assert count_effective_players(team.id) == 2
            db.session.rollback()

    # Verifies rejected requests are not counted.
    def test_rejected_requests_are_not_counted(self, app):
        with app.app_context():
            team = _make_team(name="EffPl Rejected Team")
            acc = _make_account(email="effpl_rej@t.com")
            db.session.add(TeamJoinRequest(
                team_id=team.id,
                user_id=acc.id,
                date=datetime.now(timezone.utc),
                status="rejected",
            ))
            db.session.flush()
            assert count_effective_players(team.id) == 0
            db.session.rollback()

    # Verifies accepted requests are not double counted.
    def test_accepted_requests_are_not_double_counted(self, app):
        with app.app_context():
            team = _make_team(name="EffPl Accepted Team")
            acc = _make_account(email="effpl_acc@t.com")
            # Confirmed player + accepted request for same user — only 1 real slot
            player = Player(id=acc.id)
            db.session.add(player)
            db.session.flush()
            db.session.add(PlayerTeam(player_id=player.id, team_id=team.id))
            db.session.add(TeamJoinRequest(
                team_id=team.id,
                user_id=acc.id,
                date=datetime.now(timezone.utc),
                status="accepted",
            ))
            db.session.flush()
            # Only confirmed PlayerTeam row counts; accepted request is not pending
            assert count_effective_players(team.id) == 1
            db.session.rollback()


# ===========================================================================
# handle_team_after_last_manager_removed
# ===========================================================================

class TestHandleTeamAfterLastManagerRemoved:

    # Verifies team with club is left unchanged.
    def test_team_with_club_is_left_unchanged(self, app):
        with app.app_context():
            from server.app.models.club import Club
            club = Club(name="Keep Club HH", description="d", city="c")
            db.session.add(club)
            db.session.flush()
            team = _make_team(name="Club Guarded Team", club_id=club.id)
            team_id = team.id
            handle_team_after_last_manager_removed(team)
            db.session.flush()
            assert db.session.get(Team, team_id) is not None
            db.session.rollback()

    # Verifies team with remaining managers is left unchanged.
    def test_team_with_remaining_managers_is_left_unchanged(self, app):
        with app.app_context():
            team = _make_team(name="Still Has Manager Team")
            acc = _make_account(email="still_mgr@t.com")
            tm = _make_team_manager(acc)
            _make_assoc(tm, team)
            team_id = team.id
            handle_team_after_last_manager_removed(team)
            db.session.flush()
            assert db.session.get(Team, team_id) is not None
            db.session.rollback()

    # Verifies teamless player team is deleted.
    def test_teamless_player_team_is_deleted(self, app):
        with app.app_context():
            team = _make_team(name="Delete Empty Team")
            team_id = team.id
            handle_team_after_last_manager_removed(team)
            db.session.flush()
            assert db.session.get(Team, team_id) is None
            db.session.rollback()

    # Verifies team with player promotes first player to manager.
    def test_team_with_player_promotes_first_player_to_manager(self, app):
        with app.app_context():
            _role("team_manager")   # ensure role exists
            team = _make_team(name="Promote Player Team")
            _add_player_to_team(team, "promote_pl@t.com")
            db.session.refresh(team)
            team_id = team.id

            handle_team_after_last_manager_removed(team)
            db.session.flush()

            assert db.session.get(Team, team_id) is not None
            assoc = db.session.query(TeamManagerTeam).filter_by(team_id=team_id).first()
            assert assoc is not None
            db.session.rollback()


# ===========================================================================
# ladders_exceeding_max_after_add
# ===========================================================================

class TestLaddersExceedingMaxAfterAdd:

    # Verifies team with no ladder never exceeds.
    def test_team_with_no_ladder_never_exceeds(self, app):
        with app.app_context():
            team = _make_team(name="LadExcMax No Ladder")
            assert ladders_exceeding_max_after_add(team.id) == []
            db.session.rollback()

    # Verifies sport with no cap never exceeds.
    def test_sport_with_no_cap_never_exceeds(self, app):
        with app.app_context():
            st = _make_sport_type(max_players=None, name="NoMaxSport LadExc")
            team = _make_team(name="LadExcMax NoCap")
            team.sport_type_id = st.id
            ladder = _make_ladder(name="NoCap Ladder LadExc")
            _enroll(team, ladder)
            assert ladders_exceeding_max_after_add(team.id) == []
            db.session.rollback()

    # Verifies the max-capacity check returns affected ladders.
    def test_at_capacity_returns_affected_ladders(self, app):
        with app.app_context():
            st = _make_sport_type(max_players=1, name="MaxOneSport LadExc")
            team = _make_team(name="LadExcMax AtCap")
            team.sport_type_id = st.id
            _add_player_to_team(team, "excmax_pl@t.com")
            ladder = _make_ladder(name="AtCap Ladder LadExc")
            _enroll(team, ladder)
            result = ladders_exceeding_max_after_add(team.id)
            assert any(l.id == ladder.id for l in result)
            db.session.rollback()

    # Verifies the max-capacity check returns an empty list below capacity.
    def test_below_capacity_returns_empty(self, app):
        with app.app_context():
            st = _make_sport_type(max_players=5, name="MaxFiveSport LadExc")
            team = _make_team(name="LadExcMax BelowCap")
            team.sport_type_id = st.id
            ladder = _make_ladder(name="BelowCap Ladder LadExc")
            _enroll(team, ladder)
            assert ladders_exceeding_max_after_add(team.id) == []
            db.session.rollback()

    # Verifies pending requests count towards capacity.
    def test_pending_requests_count_towards_capacity(self, app):
        with app.app_context():
            st = _make_sport_type(max_players=1, name="MaxOnePendingSport")
            team = _make_team(name="LadExcMax Pending")
            team.sport_type_id = st.id
            # Pending request — no confirmed player yet
            acc = _make_account(email="excmax_pend@t.com")
            db.session.add(TeamJoinRequest(
                team_id=team.id,
                user_id=acc.id,
                date=datetime.now(timezone.utc),
                status="pending",
            ))
            db.session.flush()
            ladder = _make_ladder(name="Pending Cap Ladder")
            _enroll(team, ladder)
            result = ladders_exceeding_max_after_add(team.id)
            assert any(l.id == ladder.id for l in result)
            db.session.rollback()

    # Verifies ladder ruleset singles override a wider sport maximum.
    def test_ruleset_singles_uses_ladder_limit(self, app):
        with app.app_context():
            st = _make_sport_type(max_players=4, name="WideSport LadExc")
            ruleset = MatchRuleSet(name="Singles Ladder Rules", game_format="singles")
            db.session.add(ruleset)
            db.session.flush()
            team = _make_team(name="Ruleset Singles Team")
            team.sport_type_id = st.id
            _add_player_to_team(team, "ruleset_singles_1@t.com")
            ladder = _make_ladder(name="Ruleset Singles Ladder")
            ladder.ruleset_id = ruleset.id
            _enroll(team, ladder)
            result = ladders_exceeding_max_after_add(team.id)
            assert any(l.id == ladder.id for l in result)
            db.session.rollback()


# ===========================================================================
# ladders_violating_min_after_remove
# ===========================================================================

class TestLaddersViolatingMinAfterRemove:

    # Verifies team with no ladder never violates.
    def test_team_with_no_ladder_never_violates(self, app):
        with app.app_context():
            team = _make_team(name="LadVioMin No Ladder")
            assert ladders_violating_min_after_remove(team.id) == []
            db.session.rollback()

    # Verifies sport with no minimum never violates.
    def test_sport_with_no_minimum_never_violates(self, app):
        with app.app_context():
            st = _make_sport_type(min_players=None, name="NoMinSport LadVio")
            team = _make_team(name="LadVioMin NoMin")
            team.sport_type_id = st.id
            ladder = _make_ladder(name="NoMin Ladder LadVio")
            _enroll(team, ladder)
            assert ladders_violating_min_after_remove(team.id) == []
            db.session.rollback()

    # Verifies the min-capacity check returns affected ladders.
    def test_at_minimum_returns_affected_ladders(self, app):
        with app.app_context():
            st = _make_sport_type(min_players=2, name="MinTwoSport LadVio")
            team = _make_team(name="LadVioMin AtMin")
            team.sport_type_id = st.id
            # Exactly 2 players — removing one drops to 1 < 2
            for i in range(2):
                _add_player_to_team(team, f"viomin_pl_{i}@t.com")
            ladder = _make_ladder(name="AtMin Ladder LadVio")
            _enroll(team, ladder)
            result = ladders_violating_min_after_remove(team.id)
            assert any(l.id == ladder.id for l in result)
            db.session.rollback()

    # Verifies the min-capacity check returns an empty list above minimum.
    def test_above_minimum_returns_empty(self, app):
        with app.app_context():
            st = _make_sport_type(min_players=2, name="MinTwoPlusSport LadVio")
            team = _make_team(name="LadVioMin AboveMin")
            team.sport_type_id = st.id
            # 3 players — removing one still leaves 2 >= min of 2
            for i in range(3):
                _add_player_to_team(team, f"abovemin_pl_{i}@t.com")
            ladder = _make_ladder(name="AboveMin Ladder LadVio")
            _enroll(team, ladder)
            assert ladders_violating_min_after_remove(team.id) == []
            db.session.rollback()

    # Verifies ladder ruleset doubles override a wider sport minimum.
    def test_ruleset_doubles_uses_ladder_limit(self, app):
        with app.app_context():
            st = _make_sport_type(min_players=1, name="WideSport LadVio")
            ruleset = MatchRuleSet(name="Doubles Ladder Rules", game_format="doubles")
            db.session.add(ruleset)
            db.session.flush()
            team = _make_team(name="Ruleset Doubles Team")
            team.sport_type_id = st.id
            for i in range(2):
                _add_player_to_team(team, f"ruleset_doubles_{i}@t.com")
            ladder = _make_ladder(name="Ruleset Doubles Ladder")
            ladder.ruleset_id = ruleset.id
            _enroll(team, ladder)
            result = ladders_violating_min_after_remove(team.id)
            assert any(l.id == ladder.id for l in result)
            db.session.rollback()
