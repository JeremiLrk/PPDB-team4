"""
Tests for the score-submission flow.

Coverage
--------
Unit (service layer — no HTTP):
  - submit_score resolves team1_side role for team1 manager
  - submit_score resolves team2_side role for team2 manager
  - match is auto-finalized when both sides submit identical scores
  - match enters 'disputed' state when sides submit different scores
  - ladder_admin submission finalizes a disputed match
  - duplicate submission for the same role raises ScoreSubmissionError (409)
  - submission on already-finalized match raises ScoreSubmissionError (409)
  - submission on cancelled match raises ScoreSubmissionError (409)
  - negative scores raise ScoreSubmissionError (422)
  - account with no team relation raises ScoreSubmissionError (403)
  - ladder_admin submission rejected when match is not yet disputed

Integration (HTTP routes):
  - POST /api/matches/<id>/score returns 201 and submission data
  - POST /api/matches/<id>/score returns finalized=true when both sides agree
  - POST /api/matches/<id>/score returns 409 on duplicate role submission
  - POST /api/matches/<id>/score returns 403 for unrelated account
  - GET  /api/matches/<id>/score returns submissions and score_status
  - GET  /api/matches/disputed returns only matches the caller can adjudicate
"""

import pytest
from unittest.mock import patch

from server.extensions import db
from server.app.models.account import Account, AccountRole, Administrator
from server.app.models.club import Club
from server.app.models.club_owner import ClubOwner
from server.app.models.club_owner_club import ClubOwnerClub
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
from server.app.models.match import (
    MatchCancelled,
    MatchPlayed,
    MatchProposal,
    MatchScoreSubmission,
    MatchStatus,
    SubmissionRole,
)
from server.app.models.match_rule import MatchRuleSet
from server.app.models.sport_type import SportType
from server.app.models.team import Team, TeamManager, TeamManagerTeam
from server.app.services.match_score_service import ScoreSubmissionError, submit_score
from server.tests._authed_client import _authed_client


# ===========================================================================
# Factories
# ===========================================================================

def _role(name: str) -> AccountRole:
    r = AccountRole.query.filter_by(name=name).first()
    if not r:
        r = AccountRole(name=name)
        db.session.add(r)
        db.session.flush()
    return r


def _account(email: str, role_name: str = "team_manager") -> Account:
    acc = Account(
        email=email,
        password_hash="x",
        first_name="T",
        last_name="U",
        account_role_id=_role(role_name).id,
        is_verified=True,
    )
    db.session.add(acc)
    db.session.flush()
    return acc


def _sport() -> SportType:
    s = SportType.query.first()
    if not s:
        s = SportType(name="Tennis")
        db.session.add(s)
        db.session.flush()
    return s


def _club(name: str = "Club A") -> Club:
    c = Club(name=name, sport_type_id=_sport().id)
    db.session.add(c)
    db.session.flush()
    return c


def _team(club: Club, name: str = "Team A") -> Team:
    t = Team(name=name, club_id=club.id, sport_type_id=club.sport_type_id)
    db.session.add(t)
    db.session.flush()
    return t


def _team_manager(account: Account, team: Team, *, can_manage_match: bool = True) -> TeamManager:
    tm = TeamManager(id=account.id)
    db.session.add(tm)
    db.session.flush()
    assoc = TeamManagerTeam(
        team_manager_id=tm.id,
        team_id=team.id,
        can_manage_match=can_manage_match,
    )
    db.session.add(assoc)
    db.session.flush()
    db.session.refresh(account)
    return tm


def _club_owner(account: Account, club: Club) -> ClubOwner:
    tm = TeamManager(id=account.id)
    db.session.add(tm)
    db.session.flush()
    co = ClubOwner(id=tm.id)
    db.session.add(co)
    db.session.flush()
    assoc = ClubOwnerClub(
        club_owner_id=co.id,
        club_id=club.id,
        can_manage_match=True,
    )
    db.session.add(assoc)
    db.session.flush()
    db.session.refresh(account)
    return co


def _ladder(club: Club, ruleset: MatchRuleSet | None = None) -> Ladder:
    l = Ladder(club_id=club.id, name="Ladder A", ruleset_id=ruleset.id if ruleset else None)
    db.session.add(l)
    db.session.flush()
    return l


def _status(name: str) -> MatchStatus:
    s = MatchStatus.query.filter_by(name=name).first()
    assert s is not None, f"Seed status '{name}' missing — run seed_db fixture"
    return s


def _proposal(team1: Team, team2: Team, ladder: Ladder | None = None) -> MatchProposal:
    p = MatchProposal(
        sport_type_id=team1.sport_type_id,
        team1_id=team1.id,
        team2_id=team2.id,
        status_id=_status("accepted").id,
        ladder_id=ladder.id if ladder else None,
    )
    db.session.add(p)
    db.session.flush()
    db.session.refresh(p)
    return p


def _add_submission(proposal: MatchProposal, account: Account, role: SubmissionRole,
                    s1: int = 2, s2: int = 1) -> MatchScoreSubmission:
    sub = MatchScoreSubmission(
        match_id=proposal.id,
        submitted_by=account.id,
        submitted_by_role=role.value,
        score_team1=s1,
        score_team2=s2,
    )
    db.session.add(sub)
    db.session.flush()
    db.session.refresh(proposal)
    return sub


# ===========================================================================
# Unit tests — service layer
# ===========================================================================

class TestSubmitScoreRoleResolution:
    """submit_score assigns the correct SubmissionRole based on account permissions."""

    def test_team1_manager_gets_team1_side_role(self, seeded_app):
        """Manager of team1 receives role 'team1_side'."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            acc = _account("mgr1@test.com")
            _team_manager(acc, t1)
            proposal = _proposal(t1, t2)

            submission, _ = submit_score(proposal, acc, 2, 1)
            db.session.commit()

            assert submission.submitted_by_role == SubmissionRole.TEAM1_SIDE.value

    def test_team2_manager_gets_team2_side_role(self, seeded_app):
        """Manager of team2 receives role 'team2_side'."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            acc = _account("mgr2@test.com")
            _team_manager(acc, t2)
            proposal = _proposal(t1, t2)

            submission, _ = submit_score(proposal, acc, 1, 3)
            db.session.commit()

            assert submission.submitted_by_role == SubmissionRole.TEAM2_SIDE.value

    def test_unrelated_account_raises_forbidden(self, seeded_app):
        """Account with no relation to either team raises ScoreSubmissionError 403."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            stranger = _account("stranger@test.com")
            proposal = _proposal(t1, t2)

            with pytest.raises(ScoreSubmissionError) as exc:
                submit_score(proposal, stranger, 1, 0)

            assert exc.value.status_code == 403


class TestAutoFinalization:
    """Match is finalized automatically when the result becomes unambiguous."""

    def test_matching_submissions_finalize_match(self, seeded_app):
        """When both sides submit the same score, MatchPlayed is created immediately."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("m1@test.com")
            mgr2 = _account("m2@test.com")
            _team_manager(mgr1, t1)
            _team_manager(mgr2, t2)
            proposal = _proposal(t1, t2)

            submit_score(proposal, mgr1, 2, 1)
            db.session.commit()
            db.session.refresh(proposal)
            assert proposal.score_status == "not_submitted"  # only one side so far

            _, finalized = submit_score(proposal, mgr2, 2, 1)
            db.session.commit()
            db.session.refresh(proposal)

            assert finalized is True
            assert proposal.played is not None
            assert proposal.played.score_team1 == 2
            assert proposal.played.score_team2 == 1
            assert proposal.score_status == "resolved"

    def test_disagreeing_submissions_produce_disputed_status(self, seeded_app):
        """When sides submit different scores, match enters 'disputed' state."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("m1@test.com")
            mgr2 = _account("m2@test.com")
            _team_manager(mgr1, t1)
            _team_manager(mgr2, t2)
            proposal = _proposal(t1, t2)

            submit_score(proposal, mgr1, 2, 1)
            _, finalized = submit_score(proposal, mgr2, 1, 2)
            db.session.commit()
            db.session.refresh(proposal)

            assert finalized is False
            assert proposal.played is None
            assert proposal.score_status == "disputed"


class TestLadderAdminAdjudication:
    """Ladder admin can submit the decisive score for a disputed match."""

    def test_ladder_admin_finalizes_disputed_match(self, seeded_app):
        """ClubOwner of the ladder's club resolves a dispute with their submission."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("m1@test.com")
            mgr2 = _account("m2@test.com")
            _team_manager(mgr1, t1)
            _team_manager(mgr2, t2)
            admin_acc = _account("admin@test.com")
            _club_owner(admin_acc, club)
            ladder = _ladder(club)
            proposal = _proposal(t1, t2, ladder=ladder)

            # Create dispute
            submit_score(proposal, mgr1, 2, 1)
            submit_score(proposal, mgr2, 1, 2)
            db.session.commit()
            db.session.refresh(proposal)
            assert proposal.score_status == "disputed"

            # Admin resolves
            _, finalized = submit_score(proposal, admin_acc, 2, 1)
            db.session.commit()
            db.session.refresh(proposal)

            assert finalized is True
            assert proposal.score_status == "resolved"
            assert proposal.played.score_team1 == 2

    def test_ladder_admin_submission_rejected_when_not_disputed(self, seeded_app):
        """Admin adjudication is refused when no dispute exists yet."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            admin_acc = _account("admin@test.com")
            _club_owner(admin_acc, club)
            ladder = _ladder(club)
            proposal = _proposal(t1, t2, ladder=ladder)

            with pytest.raises(ScoreSubmissionError) as exc:
                submit_score(proposal, admin_acc, 2, 0)

            assert exc.value.status_code == 409
            assert "not yet disputed" in str(exc.value).lower() or "only allowed" in str(exc.value).lower()


class TestSubmissionGuards:
    """Edge-case guards on submit_score."""

    def test_duplicate_role_raises_409(self, seeded_app):
        """Second submission from same role raises ScoreSubmissionError 409."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("m1@test.com")
            _team_manager(mgr1, t1)
            proposal = _proposal(t1, t2)

            submit_score(proposal, mgr1, 2, 1)
            db.session.commit()
            db.session.refresh(proposal)

            with pytest.raises(ScoreSubmissionError) as exc:
                submit_score(proposal, mgr1, 3, 0)

            assert exc.value.status_code == 409

    def test_submission_on_finalized_match_raises_409(self, seeded_app):
        """Submitting a score after match is already finalized raises 409."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("m1@test.com")
            _team_manager(mgr1, t1)
            proposal = _proposal(t1, t2)

            played = MatchPlayed(id=proposal.id, score_team1=1, score_team2=0)
            db.session.add(played)
            db.session.flush()
            db.session.refresh(proposal)

            with pytest.raises(ScoreSubmissionError) as exc:
                submit_score(proposal, mgr1, 2, 1)

            assert exc.value.status_code == 409

    def test_submission_on_cancelled_match_raises_409(self, seeded_app):
        """Submitting a score for a cancelled match raises 409."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("m1@test.com")
            _team_manager(mgr1, t1)
            proposal = _proposal(t1, t2)

            cancelled = MatchCancelled(id=proposal.id)
            db.session.add(cancelled)
            db.session.flush()
            db.session.refresh(proposal)

            with pytest.raises(ScoreSubmissionError) as exc:
                submit_score(proposal, mgr1, 1, 0)

            assert exc.value.status_code == 409

    def test_negative_scores_raise_422(self, seeded_app):
        """Negative score values raise ScoreSubmissionError 422."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("m1@test.com")
            _team_manager(mgr1, t1)
            proposal = _proposal(t1, t2)

            with pytest.raises(ScoreSubmissionError) as exc:
                submit_score(proposal, mgr1, -1, 2)

            assert exc.value.status_code == 422


# ===========================================================================
# Integration tests — HTTP routes
# ===========================================================================

class TestPostScoreRoute:
    """POST /api/matches/<id>/score"""

    def test_returns_201_with_submission_data(self, seeded_app, client, monkeypatch):
        """Valid submission returns 201 with submission dict and scoreStatus."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr_acc = _account("mgr@test.com")
            _team_manager(mgr_acc, t1)
            proposal = _proposal(t1, t2)
            db.session.commit()
            pid = proposal.id

        authed = _authed_client(client, monkeypatch, mgr_acc)
        resp = authed.post(f"/api/matches/{pid}/score", json={"score_team1": 3, "score_team2": 1})

        assert resp.status_code == 201
        body = resp.get_json()
        assert body["submission"]["submittedByRole"] == SubmissionRole.TEAM1_SIDE.value
        assert body["submission"]["scoreTeam1"] == 3
        assert body["finalized"] is False

    def test_both_sides_agree_returns_finalized_true(self, seeded_app, client, monkeypatch):
        """When both sides submit matching scores, response contains finalized=true."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("mgr1@test.com")
            mgr2 = _account("mgr2@test.com")
            _team_manager(mgr1, t1)
            _team_manager(mgr2, t2)
            proposal = _proposal(t1, t2)
            db.session.commit()
            pid = proposal.id

        _authed_client(client, monkeypatch, mgr1).post(
            f"/api/matches/{pid}/score", json={"score_team1": 2, "score_team2": 0}
        )
        resp = _authed_client(client, monkeypatch, mgr2).post(
            f"/api/matches/{pid}/score", json={"score_team1": 2, "score_team2": 0}
        )

        assert resp.status_code == 201
        body = resp.get_json()
        assert body["finalized"] is True
        assert body["resolvedScore"] == {"scoreTeam1": 2, "scoreTeam2": 0}
        assert body["scoreStatus"] == "resolved"

    def test_duplicate_submission_returns_409(self, seeded_app, client, monkeypatch):
        """Submitting a second score for the same role returns 409."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("mgr1@test.com")
            _team_manager(mgr1, t1)
            proposal = _proposal(t1, t2)
            db.session.commit()
            pid = proposal.id

        authed = _authed_client(client, monkeypatch, mgr1)
        authed.post(f"/api/matches/{pid}/score", json={"score_team1": 1, "score_team2": 0})
        resp = authed.post(f"/api/matches/{pid}/score", json={"score_team1": 2, "score_team2": 0})

        assert resp.status_code == 409

    def test_unrelated_account_returns_403(self, seeded_app, client, monkeypatch):
        """Account with no team relation receives 403."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            stranger = _account("stranger@test.com")
            proposal = _proposal(t1, t2)
            db.session.commit()
            pid = proposal.id

        authed = _authed_client(client, monkeypatch, stranger)
        resp = authed.post(f"/api/matches/{pid}/score", json={"score_team1": 1, "score_team2": 0})

        assert resp.status_code == 403

    def test_missing_scores_returns_422(self, seeded_app, client, monkeypatch):
        """Request body missing score fields returns 422."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("mgr1@test.com")
            _team_manager(mgr1, t1)
            proposal = _proposal(t1, t2)
            db.session.commit()
            pid = proposal.id

        authed = _authed_client(client, monkeypatch, mgr1)
        resp = authed.post(f"/api/matches/{pid}/score", json={"score_team1": 1})

        assert resp.status_code == 422


class TestGetScoreRoute:
    """GET /api/matches/<id>/score"""

    def test_returns_submissions_and_status(self, seeded_app, client, monkeypatch):
        """Authorised caller receives submissions list and scoreStatus."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("mgr1@test.com")
            _team_manager(mgr1, t1)
            proposal = _proposal(t1, t2)
            _add_submission(proposal, mgr1, SubmissionRole.TEAM1_SIDE, 3, 1)
            db.session.commit()
            pid = proposal.id

        authed = _authed_client(client, monkeypatch, mgr1)
        resp = authed.get(f"/api/matches/{pid}/score")

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["scoreStatus"] == "not_submitted"  # only one side
        assert len(body["submissions"]) == 1
        assert body["submissions"][0]["submittedByRole"] == "team1_side"
        assert body["resolvedScore"] is None

    def test_forbidden_for_unrelated_account(self, seeded_app, client, monkeypatch):
        """Account with no team relation receives 403 on GET."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            stranger = _account("stranger@test.com")
            proposal = _proposal(t1, t2)
            db.session.commit()
            pid = proposal.id

        authed = _authed_client(client, monkeypatch, stranger)
        resp = authed.get(f"/api/matches/{pid}/score")

        assert resp.status_code == 403


class TestDisputedRoute:
    """GET /api/matches/disputed"""

    def test_ladder_admin_sees_disputed_match(self, seeded_app, client, monkeypatch):
        """ClubOwner of the ladder's club receives disputed matches they can resolve."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("m1@test.com")
            mgr2 = _account("m2@test.com")
            admin_acc = _account("admin@test.com")
            _team_manager(mgr1, t1)
            _team_manager(mgr2, t2)
            _club_owner(admin_acc, club)
            ladder = _ladder(club)
            proposal = _proposal(t1, t2, ladder=ladder)

            _add_submission(proposal, mgr1, SubmissionRole.TEAM1_SIDE, 2, 1)
            _add_submission(proposal, mgr2, SubmissionRole.TEAM2_SIDE, 1, 2)
            db.session.commit()
            pid = proposal.id

        authed = _authed_client(client, monkeypatch, admin_acc)
        resp = authed.get("/api/matches/disputed")

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["total"] == 1
        assert body["matches"][0]["id"] == pid

    def test_team_manager_sees_empty_disputed_list(self, seeded_app, client, monkeypatch):
        """Ordinary team manager without ladder admin rights sees no disputed matches."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("m1@test.com")
            mgr2 = _account("m2@test.com")
            _team_manager(mgr1, t1)
            _team_manager(mgr2, t2)
            ladder = _ladder(club)
            proposal = _proposal(t1, t2, ladder=ladder)

            _add_submission(proposal, mgr1, SubmissionRole.TEAM1_SIDE, 2, 1)
            _add_submission(proposal, mgr2, SubmissionRole.TEAM2_SIDE, 1, 2)
            db.session.commit()

        authed = _authed_client(client, monkeypatch, mgr1)
        resp = authed.get("/api/matches/disputed")

        assert resp.status_code == 200
        assert resp.get_json()["total"] == 0

    def test_resolved_match_not_in_disputed_list(self, seeded_app, client, monkeypatch):
        """A match that has been finalized does not appear in disputed list."""
        with seeded_app.app_context():
            club = _club()
            t1, t2 = _team(club, "T1"), _team(club, "T2")
            mgr1 = _account("m1@test.com")
            mgr2 = _account("m2@test.com")
            admin_acc = _account("admin@test.com")
            _team_manager(mgr1, t1)
            _team_manager(mgr2, t2)
            _club_owner(admin_acc, club)
            ladder = _ladder(club)
            proposal = _proposal(t1, t2, ladder=ladder)

            _add_submission(proposal, mgr1, SubmissionRole.TEAM1_SIDE, 2, 1)
            _add_submission(proposal, mgr2, SubmissionRole.TEAM2_SIDE, 1, 2)

            # Finalize manually
            played = MatchPlayed(id=proposal.id, score_team1=2, score_team2=1)
            db.session.add(played)
            db.session.commit()

        authed = _authed_client(client, monkeypatch, admin_acc)
        resp = authed.get("/api/matches/disputed")

        assert resp.get_json()["total"] == 0
