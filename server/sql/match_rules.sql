/*
 =====
 MATCH RULE SET
 =====
 Structured rules for tennis and padel matches. Rulesets can be global,
 account-created, or club-specific.
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
