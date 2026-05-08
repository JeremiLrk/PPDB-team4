/*
 =====
 MATCH RULES
 =====
 */

CREATE TABLE IF NOT EXISTS match_rule (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(64) NOT NULL,
    description VARCHAR(512),

    can_be_used_by_others BOOLEAN NOT NULL DEFAULT true,

    creator_id BIGINT DEFAULT NULL,
    club_id BIGINT DEFAULT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT now(),

    is_active BOOLEAN NOT NULL DEFAULT true,
    replaced_by BIGINT DEFAULT NULL,

    CONSTRAINT fk_match_rule_replaced_by
        FOREIGN KEY (replaced_by)
            REFERENCES match_rule(id)
            ON DELETE SET NULL,

    CONSTRAINT fk_match_rule_creator_account
        FOREIGN KEY (creator_id)
            REFERENCES account(id)
            ON DELETE SET NULL,

    CONSTRAINT fk_match_rule_club
        FOREIGN KEY (club_id)
            REFERENCES club(id)
            ON DELETE SET NULL,

    CONSTRAINT pk_match_rule
        PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS match_rule_set (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(64) NOT NULL,
    description VARCHAR(512),

    can_be_used_by_others BOOLEAN NOT NULL DEFAULT true,

    creator_id BIGINT DEFAULT NULL,
    club_id BIGINT DEFAULT NULL,

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

CREATE TABLE IF NOT EXISTS match_rule_set_rule (
    match_rule_set_id BIGINT NOT NULL,
    match_rule_id BIGINT NOT NULL,

    CONSTRAINT fk_mrsr_rule_set
        FOREIGN KEY (match_rule_set_id)
            REFERENCES match_rule_set(id)
            ON DELETE CASCADE,

    CONSTRAINT fk_mrsr_rule
        FOREIGN KEY (match_rule_id)
            REFERENCES match_rule(id)
            ON DELETE CASCADE,

    CONSTRAINT pk_match_rule_set_rule
        PRIMARY KEY (match_rule_set_id, match_rule_id)
);

