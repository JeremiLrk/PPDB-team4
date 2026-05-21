# Dashboard

The dashboard is the main workspace after login.

## What It Covers

The dashboard brings the common player and club tools into one place:

- profile details
- password changes
- club search
- club creation
- join requests
- team list, team invitations, and team creation
- availability blocks
- weekly match proposals
- match proposal responses and score submission
- club management requests
- light and dark theme switching

## Main Tabs

The dashboard is split into focused tabs so the page stays readable:

- overview for the main account summary
- profile for personal details and password changes
- search for finding clubs
- availability for weekly planning blocks
- requests for join request history
- teams for your teams, team creation, and invitations
- matches for match proposals, responses, and score submission
- create club for new club requests
- manage clubs for club ownership work

## Why It Exists

It keeps the user from having to jump between separate pages for everyday actions.

That is especially useful because the dashboard is where the app mixes account actions, club actions, and planning actions in one flow.

## Theme Support

The dashboard supports both light and dark mode, and the sidebar collapses into a hamburger menu on smaller screens.

## What To Expect

The dashboard is the place where most signed-in users will start:

- players use it for profile and availability
- club owners use it for club requests and management
- team managers use it for match and team work
- the whole page is designed to keep controls usable on narrow screens

## Team Invitations

The Teams tab shows team-related invitations.

There are two invitation types:

- player invitations, where a user is invited to join a team
- club invitations, where a club asks a managed independent team to join the club and optionally enter a ladder

Accepting a club invitation moves the team into the club, adds current team managers and players as club members, and places the team in the requested ladder when one was selected.

## Team Creation And Self-Add

When a manager creates a team from the dashboard, NetRank refreshes the shared
current-user context right away so the new team-manager role is visible without
a hard refresh.

The Teams tab also shows a small follow-up action for the newly created team:

- `Add yourself as player`

That shortcut uses the normal player join-request flow and immediately accepts
the request when the backend creates it successfully. It exists so a new team
manager does not need to open a second invite flow just to become a player on
the same team.

## Where The Invitation Hierarchy Lives

For the full invitation and role hierarchy, see [team-system.md](team-system.md).
