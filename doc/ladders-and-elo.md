# Ladders And Elo

Ladders are the ranking layer of NetRank. A ladder belongs to one club and defines the competition structure for the teams that are part of it.

## What A Ladder Stores

A ladder can point to:

- a club
- a sport type
- a ruleset
- a rating function

In practice, this lets a club run more than one competition at the same time without mixing their rankings or rules.

The ladder ruleset is the preferred source for roster-size behavior when it is
available. Older ladders still fall back to the sport-type limits, which keeps
legacy basketball, squash, and similar club data working while newer ladders
use the explicit ruleset model.

## Adding Teams To Ladders

Club teams can be added to a club ladder directly by a club owner or administrator.

Independent teams use an invitation flow:

1. The club manager selects the independent team in the ladder settings.
2. NetRank creates a pending invitation for the team manager.
3. The team manager accepts or rejects the invitation from the dashboard.
4. On acceptance, the team joins the club and is added to the ladder.

The ladder chooser shows the practical state of each candidate team:

- whether it is already a club team
- whether it needs an invitation
- whether an invitation is already pending
- whether the team is already in the selected ladder
- current managers and players

NetRank does not assign an independent team to a club without team-manager approval.

If a club manager tries to add a team that is technically too large for the
ladder, the UI warns first instead of silently blocking the action. The
confirmation flow then lets the manager decide whether to continue and remove
the ladder membership or create a new team instead.

Club managers can also manage existing ladder membership from the same settings area:

- remove a team from a ladder
- delete a ladder
- see how many teams are currently in each ladder

Removing a team from a ladder cancels that team's unplayed matches in that ladder. Deleting a ladder removes the ladder membership rows while keeping historical match records in the database.

## How Elo Works

NetRank uses an Elo-style rating system for ladder rankings. In plain language, that means every match changes a team’s rating based on whether it did better or worse than the system expected.

This is not the original textbook version of Elo. It is a custom version with a few practical rules added so the ladder behaves better for real club play.

The rating update is based on three ideas:

- the rating difference between the two teams
- the final result of the match
- how experienced each team already is

The service does the following:

1. It reads the current ladder rating for both teams.
2. It calculates the expected result from the rating gap.
3. It converts the final score into a win, loss, or draw result.
4. It applies a K-factor based on experience and rating strength.
5. It rounds the rating change and saves the new ratings.
6. It rebuilds the ladder ranking order from the updated ratings.

In this project, the default ladder rating starts at 1000. The rating change is based on a capped version of the rating gap, so huge mismatches do not create extreme jumps. The K-factor is:

- 40 for teams with fewer than 30 matches, which means their rating can move more quickly because the system is still learning where they belong
- 20 for normal established teams, which gives a medium-size rating change
- 10 for very strong teams at 2400 rating or above, which makes their rating move slowly because their rating is already very stable

In other words, the number is a speed setting:

- bigger K-factor = bigger rating jumps after each match
- smaller K-factor = smaller rating jumps after each match

## The Important Details

- Very large rating gaps are capped so one bad mismatch does not create extreme swings.
- Newer teams move faster because they still have less rating history.
- Strong, established teams move more slowly.
- A draw gives a half-point result.
- The rating delta is rounded half away from zero before it is saved.
- The ranking table is sorted again after every match so the ladder order stays current.
- A match updates every ladder where both teams are enrolled together. If the same pair exists in more than one ladder, each shared ladder gets its own rating update.

## Human Version

Think of the system like this:

- if a lower-rated team beats a stronger one, it gains more points
- if a stronger team wins like expected, it gains only a small amount
- if a stronger team loses to a weaker one, it loses more
- new teams move faster because the system is still learning where they belong
- experienced teams move more slowly because their rating is already more reliable

So the rating is not just a score tally. It is the system’s best estimate of where a team belongs in the ladder.

## What Happens After A Match

When a match is finalized, the rating update is applied to the ladder where both teams are present.

That means:

- the ladder standings update immediately after the final result
- the ranking changes are stored, not calculated only on the fly

## Ladder Achievements

Ladder pages include a small achievement summary for the teams in that ladder.

It highlights:

- most wins in the ladder
- best win streak in the ladder
- longest #1 reign in the ladder

These cards are derived from finalized match results for teams in the ladder. The longest #1 reign starts from the ladder rows' stored ratings and match counts, replays the ladder's finalized match history in order, and counts the longest run of consecutive completed matches where a team held the simulated top rank. The cards help explain performance history, but they do not change Elo ratings, ladder order, or match generation.
