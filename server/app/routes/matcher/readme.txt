"""
Match routes
============

Proposal lifecycle
------------------
  POST   /api/matches                              — create match_proposal
  POST   /api/matches/<id>/accept                  — accept a proposal
  POST   /api/matches/<id>/reject                  — reject a proposal
  POST   /api/matches/<id>/result/check            — dry-run: warn if result already exists, do NOT save
  POST   /api/matches/<id>/result                  — submit result (overwrites silently if already exists)
  POST   /api/matches/<id>/cancel                  — cancel an accepted match (=/= reject)

List endpoints
--------------
  GET    /api/matches/active                       — accepted matches (status=accepted, not yet played/cancelled)
  GET    /api/matches/played                       — matches with a result (status=played)
  GET    /api/matches/pending                      — proposals awaiting accept/reject by the current user's teams
  GET    /api/matches/awaiting-result              — accepted matches where current user's team can submit a result

Permission model
----------------
  Creating a proposal:
    - Administrator                              -> always allowed
    - ClubOwner with can_create_match on team's club -> allowed
    - TeamManager who manages at least one of the two teams -> allowed

  Accepting / Rejecting:
    - Only users who manage team2 (the challenged team) may respond.
    - Administrator can always respond.

  Submitting result:
    - Manager / ClubOwner of either team (team1 or team2).
    - Administrator.

  Cancelling (after acceptance):
    - Manager / ClubOwner of team1 (the proposing team).
    - Administrator.
"""