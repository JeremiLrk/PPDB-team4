"""
Routes for MatchRule:
  POST   /api/match-rules                             — create a rule
  DELETE /api/match-rules/<rule_id>                   — delete a rule
  PATCH  /api/match-rules/<rule_id>/name              — rename a rule
  PATCH  /api/match-rules/<rule_id>/description       — change description
  PATCH  /api/match-rules/<rule_id>/deactivate        — mark rule inactive
  PATCH  /api/match-rules/<rule_id>/replace           — deactivate & point to successor
  GET    /api/match-rules/<rule_id>                   — get a rule (public)
  GET    /api/match-rules                             — list rules (public, active only)
"""

"""
Routes for MatchRuleSet:
  POST   /api/match-rule-sets                                          — create a set
  DELETE /api/match-rule-sets/<set_id>                                 — delete a set
  PATCH  /api/match-rule-sets/<set_id>/name                            — rename a set
  PATCH  /api/match-rule-sets/<set_id>/description                     — change description
  POST   /api/match-rule-sets/<set_id>/rules                           — add a rule to a set
  DELETE /api/match-rule-sets/<set_id>/rules/<rule_id>                 — remove rule from set
  GET    /api/match-rule-sets/<set_id>                                 — get a set (public)
  GET    /api/match-rule-sets                                          — list sets (public)
"""