"""Shared helpers for match-rule and match-rule-set routes."""

from flask import abort
from server.app.models.match_rule import MatchRule, MatchRuleSet
from server.app.models.account import Administrator


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------

def _get_rule_or_404(rule_id: int) -> MatchRule:
    rule = MatchRule.query.get(rule_id)
    if not rule:
        abort(404, description="Match rule not found.")
    return rule


def _get_active_rule_or_404(rule_id: int) -> MatchRule:
    """Like _get_rule_or_404 but also rejects inactive rules."""
    rule = _get_rule_or_404(rule_id)
    if not rule.is_active:
        abort(410, description="This match rule is no longer active.")
    return rule


def _get_rule_set_or_404(rule_set_id: int) -> MatchRuleSet:
    rule_set = MatchRuleSet.query.get(rule_set_id)
    if not rule_set:
        abort(404, description="Match rule set not found.")
    return rule_set


# ---------------------------------------------------------------------------
# Ownership checks
# ---------------------------------------------------------------------------

def _is_owner_of_rule(resolved, rule: MatchRule) -> bool:
    """True if resolved created the rule or is an admin."""
    if isinstance(resolved, Administrator):
        return True
    account_id = getattr(resolved, "id", None)
    return account_id is not None and rule.creator_id == account_id


def _is_owner_of_rule_set(resolved, rule_set: MatchRuleSet) -> bool:
    """True if resolved created the rule set or is an admin."""
    if isinstance(resolved, Administrator):
        return True
    account_id = getattr(resolved, "id", None)
    return account_id is not None and rule_set.creator_id == account_id


def _can_use_rule(resolved, rule: MatchRule) -> bool:
    """True if the rule is public, owned by resolved, or resolved is admin."""
    if isinstance(resolved, Administrator):
        return True
    if rule.can_be_used_by_others:
        return True
    account_id = getattr(resolved, "id", None)
    return account_id is not None and rule.creator_id == account_id


def _can_use_rule_set(resolved, rule_set: MatchRuleSet) -> bool:
    """True if the rule set is public, owned by resolved, or resolved is admin."""
    if isinstance(resolved, Administrator):
        return True
    if rule_set.can_be_used_by_others:
        return True
    account_id = getattr(resolved, "id", None)
    return account_id is not None and rule_set.creator_id == account_id
