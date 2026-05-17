# Availability And Weekly Match Proposals

The availability calendar is not just a personal schedule view. It is the input that drives the weekly match proposal system.

## What An Availability Block Means

An availability block describes a repeating weekly time window.

The block stores:

- the weekday
- the start and end time
- the concrete date range for the current week window

This makes the calendar useful for planning on a weekly basis instead of treating availability as a one-off event.

## How It Is Used

When the weekly match proposal generator runs, it looks for a time window where both teams are available at the same time.

The generator:

1. picks the target week
2. reads the ladder order
3. pairs nearby teams
4. filters out invalid pairings
5. checks for shared-player conflicts
6. checks for matching availability windows
7. creates the proposal only when a valid window exists

## Why The Calendar Matters

The calendar is what makes weekly proposal generation possible.

Without availability, the app would have to guess match times. With availability, NetRank can create proposals that fit both teams' schedules better.

That is why the dashboard availability tab and the weekly match proposal system are part of the same feature set.

The time suggested by the weekly generator is a recommendation, not an obligation. It gives teams a workable slot to start from, but the teams can still arrange the final match time separately if needed.

Manual proposals can still be created without using the weekly generator, but the calendar is what makes the automated weekly match flow work well.

## Safety Rules

The proposal generator also keeps the schedule stable by applying a few safety rules:

- it avoids duplicate proposals for the same week and pair of teams
- it avoids pairings where players overlap between teams
- it avoids rematches too soon
- it limits how far ahead a proposal can be scheduled
