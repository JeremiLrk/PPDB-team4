# Match Proposals, Scores, And Disputes

NetRank treats matches as a controlled flow instead of a free-form score entry. That keeps ladder play consistent and makes disputes easier to resolve.

## Match Proposal Flow

A match starts as a proposal between two eligible teams.

The proposal system checks:

- that the teams belong to the same ladder context
- that the teams do not share players
- that the same proposal does not already exist for that week
- that the teams are not inside the rematch cooldown window
- that both teams have overlapping availability
- that the ladder and sport data needed for the proposal exist

If all checks pass, the proposal is stored with:

- the proposed teams
- the ladder ruleset
- the target week
- the planned time window
- the match location when one is provided
- contact info for both teams, including name, email, and phone when available

The manual proposal route is meant for an authorized club owner, team manager, or administrator who wants to set up a specific match directly. It does not need the weekly scheduler, but it still has to pass the permission and scheduling checks above.

## Weekly Proposal Generation

The weekly proposal service is built around ladder ranking order.

Teams are paired by rank, so the system tries to create sensible matchups instead of random ones. In each block of four teams, it can also use a deterministic alternate pairing so the schedule does not look identical every week.

The service uses availability blocks to find a time where both teams are free long enough for the requested match duration.

The weekly generator also has a rematch cooldown. That means it will skip a pair if they have not played enough other matches since their last meeting. This cooldown is for the automatic weekly system, not for every manually created proposal.

## Score Submission

After a match is played, both sides can submit a score.

The score flow works like this:

1. Team side one submits a score.
2. Team side two submits a score.
3. If both scores match, the result finalizes automatically.
4. If the scores do not match, the match becomes disputed.

The system also supports a ladder-admin adjudication path.

That means a club owner for the ladder's club or a platform administrator can submit the deciding score when the match is disputed.

The score route is also role-based:

- users connected to one side of the match can submit for that side if they are a manager, club owner, administrator, or a player on that team
- ladder admins can settle a dispute
- one role can only submit one score for the same match

In other words:

- if you are on the team, you can usually score for that team
- if you manage the team or the club, you can also score for that team
- if the match is disputed, the club owner of the ladder’s club or an administrator can give the final score

## Disputed Matches

Disputed matches are the review queue for unresolved results.

They show:

- both submitted scores
- the ladder they belong to
- the ruleset context
- the teams involved

This makes it easier for an authorized reviewer to understand why the dispute happened and what result should be recorded.

## What Happens At Finalization

Once a result is unambiguous, NetRank writes the authoritative played record and updates ladder ratings through the Elo service.

So one final score does two things:

- it closes the match result
- it moves the ladder ratings and standings forward

It writes the played record, stores the final score, and then updates the ladder data underneath it.
