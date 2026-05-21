# Clubs And Teams

Clubs are the main place where teams and club management live.

## Clubs

A club is the top-level organization for a group of teams.

Club features include:

- club discovery and search
- opening the club home page
- opening club settings when the user has permission

## Teams

Teams are the groups that actually compete in ladders and matches. Some teams belong to clubs, and some are independent.

Team features include:

- create a team
- rename a team
- add and remove players
- add and remove managers
- open the team detail page
- open the team settings page when the user has permission
- manage the team from the team settings page

## Independent Teams Joining Clubs

Independent teams are not silently claimed by a club.

When a club manager wants to place an independent team in a club ladder, NetRank creates a team-club invitation instead of changing the team immediately.

The invitation is sent to the team managers. A team manager with manager-edit rights can accept or reject it from the Teams tab in the dashboard.

When the invitation is accepted:

- the team becomes part of the club
- the team is added to the requested ladder when the ladder is still valid
- the current team managers become club members
- the current team players become club members

This keeps consent with the team while still giving club managers a clear path to invite outside teams into their club competitions.

Team settings cover the rest of the day-to-day team workflow:

- add and remove players
- add and remove managers
- create a team and optionally add yourself as a player right away
- update the team without having to refresh the page manually

## Why The Separation Matters

NetRank separates club management from team management on purpose.

That gives the app a cleaner permission model:

- clubs handle the overall organization
- teams handle the day-to-day competitive group
- ladders handle the competitive ranking layer

## Where To Read More

- [club-page.md](club-page.md) for the club home page
- [club-settings.md](club-settings.md) for the club settings shell and pages
- [dashboard.md](dashboard.md) for club search, join requests, team invitations, and account actions
- [team-system.md](team-system.md) for the full team and invitation hierarchy
