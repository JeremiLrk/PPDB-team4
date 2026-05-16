/*
=====
AVAILABILITY
=====
*/

CREATE TABLE IF NOT EXISTS availability_block (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    user_id BIGINT NOT NULL,
    weekday INT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    start_at TIMESTAMP NOT NULL,
    end_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_availability_block_user
        FOREIGN KEY (user_id)
        REFERENCES account(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_availability_block
        PRIMARY KEY (id),

    CONSTRAINT check_availability_block_weekday_range
        CHECK (weekday BETWEEN 0 AND 6),

    CONSTRAINT check_availability_block_start_before_end_time
        CHECK (start_time < end_time),

    CONSTRAINT check_availability_block_start_before_end
        CHECK (start_at < end_at)
);

/*
 =====
 LADDERS
 =====
 */
CREATE TABLE IF NOT EXISTS ladder (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    club_id BIGINT NOT NULL,
    name VARCHAR(64) NOT NULL,
    description VARCHAR(1024),
    sport_type_id BIGINT,
    ruleset_id BIGINT,
    -- FIX: was NOT NULL with ON DELETE SET NULL — contradiction; made nullable.
    ladder_rating_function_id BIGINT,

    -- FIX: was ON DELETE CASCADE — deleting a sport_type destroyed all ladders.
    --      Changed to SET NULL because sport_type_id is already nullable.
    CONSTRAINT fk_ladder_sport_type_id
        FOREIGN KEY (sport_type_id)
        REFERENCES sport_type(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_ruleset_id
        FOREIGN KEY (ruleset_id)
        REFERENCES match_rule_set(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_ladder_rating_function_id
        FOREIGN KEY (ladder_rating_function_id)
        REFERENCES ladder_rating_function(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_ladder_club_id
        FOREIGN KEY (club_id)
        REFERENCES club(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_ladder
        PRIMARY KEY (id)
);


CREATE TABLE IF NOT EXISTS ladder_team (
    ladder_id BIGINT NOT NULL,
    team_id BIGINT NOT NULL,

    rank INT,
    rating INT DEFAULT 1000,
    matches_played INT DEFAULT 0,
    wins INT NOT NULL DEFAULT 0,
    win_streak INT NOT NULL DEFAULT 0,
    best_win_streak INT NOT NULL DEFAULT 0,
    rank1_streak INT NOT NULL DEFAULT 0,
    best_rank1_streak INT NOT NULL DEFAULT 0,

    CONSTRAINT fk_ladder_team_ladder
        FOREIGN KEY (ladder_id)
        REFERENCES ladder(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_ladder_team_team
        FOREIGN KEY (team_id)
        REFERENCES team(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_ladder_team
        PRIMARY KEY (ladder_id, team_id)
);
