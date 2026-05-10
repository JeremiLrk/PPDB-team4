/*
 =====
 MATCHES
 =====
 */

CREATE TABLE IF NOT EXISTS match_proposal (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    proposed_by_user_id BIGINT,
    sport_type_id BIGINT NOT NULL,
    rule_snapshot JSONB,
    -- ruleset_id kept for backward compatibility; ladder_id is authoritative
    -- for ladder matches (see ladder.ruleset_id).
    ruleset_id BIGINT,
    -- Direct FK to the ladder this match was registered for.
    -- NULL for friendly matches not belonging to any ladder.
    ladder_id BIGINT,

    team1_id BIGINT NOT NULL,
    team2_id BIGINT NOT NULL,
    status_id BIGINT NOT NULL,
    week_start_date DATE,
    proposed_start_at TIMESTAMP,
    proposed_end_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),

    location VARCHAR(256),
    venue_type_id BIGINT,

    CONSTRAINT fk_match_proposal_proposed_by
        FOREIGN KEY (proposed_by_user_id)
            REFERENCES account(id)
            ON DELETE RESTRICT,

    CONSTRAINT fk_match_proposal_sport_type_id
        FOREIGN KEY (sport_type_id)
            REFERENCES sport_type(id)
            ON DELETE RESTRICT,

    CONSTRAINT fk_match_proposal_ruleset
        FOREIGN KEY (ruleset_id)
            REFERENCES match_rule_set(id)
            ON DELETE SET NULL,

    CONSTRAINT fk_match_proposal_ladder
        FOREIGN KEY (ladder_id)
            REFERENCES ladder(id)
            ON DELETE SET NULL,

    CONSTRAINT fk_match_proposal_team1
        FOREIGN KEY (team1_id)
            REFERENCES team(id)
            ON DELETE CASCADE,

    CONSTRAINT fk_match_proposal_team2
        FOREIGN KEY (team2_id)
            REFERENCES team(id)
            ON DELETE CASCADE,

    CONSTRAINT fk_match_proposal_status
        FOREIGN KEY (status_id)
            REFERENCES match_status(id)
            ON DELETE RESTRICT,

    CONSTRAINT fk_match_proposal_venue_type
        FOREIGN KEY (venue_type_id)
            REFERENCES venue_type(id),

    CONSTRAINT chk_teams_different
        CHECK (team1_id <> team2_id),

    CONSTRAINT pk_match_proposal
        PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_match_proposal_week_pair
    ON match_proposal (week_start_date, team1_id, team2_id)
    WHERE week_start_date IS NOT NULL;

CREATE TABLE IF NOT EXISTS match_accepted (
    id BIGINT PRIMARY KEY,
    response_by_user_id BIGINT,
    response_text VARCHAR(512),

    CONSTRAINT fk_match_accepted_proposal
        FOREIGN KEY (id)
            REFERENCES match_proposal(id)
            ON DELETE CASCADE,

    CONSTRAINT fk_match_accepted_user
        FOREIGN KEY (response_by_user_id)
            REFERENCES account(id)
);

CREATE TABLE IF NOT EXISTS match_rejected (
    id BIGINT PRIMARY KEY,
    response_by_user_id BIGINT,
    response_text VARCHAR(512),

    CONSTRAINT fk_match_rejected_proposal
        FOREIGN KEY (id)
            REFERENCES match_proposal(id)
            ON DELETE CASCADE,

    CONSTRAINT fk_match_rejected_user
        FOREIGN KEY (response_by_user_id)
            REFERENCES account(id)
);

CREATE TABLE IF NOT EXISTS match_played (
    id BIGINT PRIMARY KEY,
    score_team1 INT NOT NULL,
    score_team2 INT NOT NULL,
    rating INT,
    played_at TIMESTAMP DEFAULT now(),

    CONSTRAINT fk_match_played_proposal
        FOREIGN KEY (id)
            REFERENCES match_proposal(id)
            ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS match_cancelled (
    id BIGINT PRIMARY KEY,
    reason VARCHAR(512),
    cancelled_at TIMESTAMP DEFAULT now(),

    CONSTRAINT fk_match_cancelled_proposal
        FOREIGN KEY (id)
            REFERENCES match_proposal(id)
            ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- match_score_submission
-- Each played match may have at most 3 submissions, one per role:
--   'team1_side'   — manager/owner authorised for team1
--   'team2_side'   — manager/owner authorised for team2
--   'ladder_admin' — club-owner/admin who adjudicates a disputed result
-- The unique constraint on (match_id, submitted_by_role) enforces the limit.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS match_score_submission (
    id                BIGINT GENERATED ALWAYS AS IDENTITY,
    match_id          BIGINT      NOT NULL,
    submitted_by      BIGINT      NOT NULL,
    submitted_by_role VARCHAR(16) NOT NULL
        CHECK (submitted_by_role IN ('team1_side', 'team2_side', 'ladder_admin')),
    score_team1       INT         NOT NULL,
    score_team2       INT         NOT NULL,
    submitted_at      TIMESTAMP   NOT NULL DEFAULT now(),

    CONSTRAINT pk_match_score_submission
        PRIMARY KEY (id),

    CONSTRAINT fk_mss_match
        FOREIGN KEY (match_id)
            REFERENCES match_proposal(id)
            ON DELETE CASCADE,

    CONSTRAINT fk_mss_account
        FOREIGN KEY (submitted_by)
            REFERENCES account(id)
            ON DELETE RESTRICT,

    -- At most one submission per role per match
    CONSTRAINT uq_mss_match_role
        UNIQUE (match_id, submitted_by_role)
);
