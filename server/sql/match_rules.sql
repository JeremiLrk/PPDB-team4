/*
 =====
 MATCH RULE SET
 Structured ruleset for tennis/padel ladder competitions.
 =====
 */

CREATE TABLE IF NOT EXISTS match_rule_set (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(64) NOT NULL,
    description VARCHAR(512),

    -- Match format: best_of_3 | timed | pro_set
    match_format VARCHAR(20) NOT NULL DEFAULT 'best_of_3',
    -- Duration in minutes (only used when match_format = 'timed')
    timed_duration_minutes INT DEFAULT NULL,
    -- Games needed to win a pro set (only used when match_format = 'pro_set')
    pro_set_games INT DEFAULT NULL,
    -- Third set rule (only relevant for best_of_3): full_set | super_tiebreak
    third_set_format VARCHAR(20) NOT NULL DEFAULT 'super_tiebreak',
    -- Deuce rule: advantage | golden_point
    deuce_rule VARCHAR(20) NOT NULL DEFAULT 'advantage',
    -- Game format: singles | doubles
    game_format VARCHAR(20) NOT NULL DEFAULT 'doubles',

    can_be_used_by_others BOOLEAN NOT NULL DEFAULT true,

    creator_id BIGINT DEFAULT NULL,
    club_id    BIGINT DEFAULT NULL,

    CONSTRAINT fk_match_rule_set_creator_account
        FOREIGN KEY (creator_id)
            REFERENCES account(id)
            ON DELETE SET NULL,

    CONSTRAINT fk_match_rule_set_club
        FOREIGN KEY (club_id)
            REFERENCES club(id)
            ON DELETE SET NULL,

    CONSTRAINT pk_match_rule_set
        PRIMARY KEY (id)
);

-- Migration: add new columns to existing tables
ALTER TABLE match_rule_set ADD COLUMN IF NOT EXISTS match_format VARCHAR(20) NOT NULL DEFAULT 'best_of_3';
ALTER TABLE match_rule_set ADD COLUMN IF NOT EXISTS timed_duration_minutes INT DEFAULT NULL;
ALTER TABLE match_rule_set ADD COLUMN IF NOT EXISTS pro_set_games INT DEFAULT NULL;
ALTER TABLE match_rule_set ADD COLUMN IF NOT EXISTS third_set_format VARCHAR(20) NOT NULL DEFAULT 'super_tiebreak';
ALTER TABLE match_rule_set ADD COLUMN IF NOT EXISTS deuce_rule VARCHAR(20) NOT NULL DEFAULT 'advantage';
ALTER TABLE match_rule_set ADD COLUMN IF NOT EXISTS game_format VARCHAR(20) NOT NULL DEFAULT 'doubles';

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
    ruleset_id BIGINT,

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
