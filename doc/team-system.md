# Team System

This page documents the team, invitation, and role hierarchy used across the
app.

## Hierarchy

NetRank uses a layered structure:

- account
- role
- club
- team
- ladder
- invitations and join requests

The same user can participate in more than one layer at the same time. For
example, someone can be a team manager, a club owner, and a player.

## Roles

The main role chain is:

- `administrator`
- `club_owner`
- `team_manager`
- `player`

Role checks are additive, not exclusive. Higher roles keep their broader access
even when the same account is also a player.

## Teams

Teams are the core competitive unit.

Teams can be:

- independent
- attached to a club

Teams can have:

- players
- managers
- ladder membership

The team settings page is where managers edit those relationships.

## Invitation Types

There are three different invitation/approval flows:

### Player invite

A team manager invites an account to join the team as a player.

Flow:

1. A manager opens team settings.
2. The manager searches for the account.
3. NetRank creates a join request.
4. The request can be accepted from the dashboard or by the invited account
   when the flow allows self-management.

### Manager invite

A team manager invites another account to manage the team.

Flow:

1. The manager searches for the account.
2. NetRank creates a manager assignment with specific permissions.
3. The new manager can rename the team, edit players, edit managers, or delete
   the team depending on the granted rights.

### Club / ladder invite

A club manager invites an independent team to join the club and, optionally, a
ladder.

Flow:

1. The club manager selects the team in club ladder settings.
2. If the team is already part of the club, it can be added directly.
3. If the team is independent, NetRank creates a club invitation.
4. Team managers accept or reject it from the Teams tab in the dashboard.
5. On acceptance, the team joins the club and the ladder when the ladder still
   fits the team rules.

## Self-Add Flow

When a team is created, the dashboard can offer an `Add yourself as player`
button.

That shortcut exists because a team manager often wants to become a player too.
It uses the normal player join-request flow, then immediately accepts the
request when the backend creates it successfully.

## Roster And Ladder Rules

The roster checks are based on the ladder requirements:

- singles ladders expect one-player teams
- doubles ladders expect two-player teams
- older ladders fall back to the sport-type limits when no ladder ruleset is
  stored yet

When a roster change would break a ladder rule, the UI warns first and lets the
user decide whether to continue, remove the team from the ladder, or create a
new team.

## Dashboard Behavior

The dashboard is the central place where these flows are resolved:

- team invitations are listed in the Teams tab
- club invitations are listed separately from player invitations
- badges show when something needs action
- team creation refreshes the current user so new manager access appears without
  a manual page reload

## Related Docs

- [dashboard.md](dashboard.md)
- [clubs-and-teams.md](clubs-and-teams.md)
- [ladders-and-elo.md](ladders-and-elo.md)
