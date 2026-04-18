/*
 =====
 INFRASTRUCTURE
 =====
 */

CREATE TABLE IF NOT EXISTS venue_type(
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(32) NOT NULL UNIQUE -- outdoor, indoor, indoor/outdoor
);
CREATE TABLE IF NOT EXISTS sport_type (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) NOT NULL,
    minimum_number_of_players_on_a_team INT NOT NULL,
    maximum_number_of_players_per_team INT NOT NULL,

    CONSTRAINT pk_sport_type
        PRIMARY KEY (id),

    CHECK (minimum_number_of_players_on_a_team > 0),
    CHECK (maximum_number_of_players_per_team > 0),

    CONSTRAINT chk_min_le_max
        CHECK (minimum_number_of_players_on_a_team <= maximum_number_of_players_per_team)
);
CREATE TABLE IF NOT EXISTS match_status (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) NOT NULL,

    CONSTRAINT pk_match_status
        PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS ladder_rating_function (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) NOT NULL,

    CONSTRAINT pk_ladder_rating_function
        PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS account_role (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) NOT NULL,

    CONSTRAINT pk_account_role
        PRIMARY KEY (id)
);

/*
 =====
 USERS
 =====
 */
CREATE TABLE IF NOT EXISTS account (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    first_name VARCHAR(32),
    last_name VARCHAR(32),
    date_of_birth DATE,
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'account',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,

    account_role_id BIGINT NOT NULL,

    CONSTRAINT fk_account_role
        FOREIGN KEY (account_role_id)
        REFERENCES account_role(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_account
        PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS administrator (
    id BIGINT,
    access_level INT NOT NULL,


    CONSTRAINT chk_positive_access_level
        CHECK (access_level >= 0),

    CONSTRAINT fk_administrator_user
        FOREIGN KEY (id)
        REFERENCES account(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_administrator
        PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS player (
    id BIGINT,

    CONSTRAINT fk_player_account
        FOREIGN KEY (id)
        REFERENCES account(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_player
        PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS team_manager (
    id BIGINT,

    CONSTRAINT fk_team_manager_account
        FOREIGN KEY (id)
        REFERENCES account(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_team_manager
        PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS club_owner (
    id BIGINT,

    CONSTRAINT fk_club_owner_account
        FOREIGN KEY (id)
        REFERENCES team_manager(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_club_owner
        PRIMARY KEY (id)
);

/*
=====
AVAILABILITY
=====
*/

CREATE TABLE IF NOT EXISTS availability_block (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    user_id BIGINT NOT NULL,
    start_at TIMESTAMP NOT NULL,
    end_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_availability_block_user
        FOREIGN KEY (user_id)
        REFERENCES account(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_availability_block
        PRIMARY KEY (id),

    CONSTRAINT check_availability_block_start_before_end
        CHECK (start_at < end_at)
);

/*
 =====
 CLUBS
 =====
 */

CREATE TABLE IF NOT EXISTS club (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(64) NOT NULL,
    description VARCHAR(512) NOT NULL,
    sport_type_id BIGINT,
    city VARCHAR(128) NOT NULL,

    CONSTRAINT fk_club_sport_type_id
        FOREIGN KEY (sport_type_id)
        REFERENCES sport_type(id)
        ON DELETE SET NULL,

    CONSTRAINT pk_club
        PRIMARY KEY (id)
    );

CREATE TABLE IF NOT EXISTS club_owner_club (
    club_owner_id BIGINT NOT NULL,
    club_id BIGINT NOT NULL,

    can_rename BOOLEAN NOT NULL DEFAULT false,
    can_change_description BOOLEAN NOT NULL DEFAULT false,
    can_create_match BOOLEAN NOT NULL DEFAULT false,
    can_add_club_players BOOLEAN NOT NULL DEFAULT false,
    can_add_club_owners BOOLEAN NOT NULL DEFAULT false,
    can_add_club_rule BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT fk_co_club_owner
        FOREIGN KEY (club_owner_id)
        REFERENCES club_owner(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_co_club
        FOREIGN KEY (club_id)
        REFERENCES club(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_club_owner_club
        PRIMARY KEY (club_owner_id, club_id)
);
CREATE TABLE IF NOT EXISTS club_join_request (
    club_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    date TIMESTAMPTZ NOT NULL,

    CONSTRAINT fk_club_id
        FOREIGN KEY (club_id)
        REFERENCES club(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_id
        FOREIGN KEY (user_id)
        REFERENCES account(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_club_id_user_id
        PRIMARY KEY (user_id, club_id)
);

CREATE TABLE IF NOT EXISTS club_player (
    club_id BIGINT NOT NULL,
    player_id BIGINT NOT NULL,

    CONSTRAINT fk_club_id
        FOREIGN KEY (club_id)
        REFERENCES club(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_player_id
        FOREIGN KEY (player_id)
        REFERENCES player(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_club_player
        PRIMARY KEY (club_id, player_id)
);
/*
 =====
 TEAMS
 =====
 */
CREATE TABLE IF NOT EXISTS team (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    club_id BIGINT NULL,
    name VARCHAR(64) NOT NULL,
    sport_type_id BIGINT,

    -- FIX: UNIQUE(club_id, name) silently allows duplicate names when club_id IS NULL
    --      because PostgreSQL does not consider NULL = NULL in UNIQUE constraints.
    --      The partial index below covers the NULL case separately.
    UNIQUE (club_id, name),

    CONSTRAINT fk_team_club
        FOREIGN KEY (club_id)
        REFERENCES club(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_team_sport_type_id
        FOREIGN KEY (sport_type_id)
        REFERENCES sport_type(id)
        ON DELETE SET NULL,

    CONSTRAINT pk_team
        PRIMARY KEY (id)
);
-- Prevents duplicate team names among club-less (independent) teams.
CREATE UNIQUE INDEX IF NOT EXISTS uq_team_name_no_club
    ON team (name)
    WHERE club_id IS NULL;

CREATE TABLE IF NOT EXISTS player_team (
    player_id BIGINT NOT NULL,
    team_id BIGINT NOT NULL,

    CONSTRAINT fk_player_team_player
        FOREIGN KEY (player_id)
        REFERENCES player(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_player_team_team
        FOREIGN KEY (team_id)
        REFERENCES team(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_player_team
        PRIMARY KEY (player_id, team_id)
);
CREATE TABLE IF NOT EXISTS team_manager_team (
    team_manager_id BIGINT NOT NULL,
    team_id BIGINT NOT NULL,

    can_rename BOOLEAN NOT NULL DEFAULT true,
    can_delete BOOLEAN NOT NULL DEFAULT true,
    can_edit_players BOOLEAN NOT NULL DEFAULT true,
    can_edit_managers BOOLEAN NOT NULL DEFAULT true,
    can_create_match BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT fk_tm_team_manager
        FOREIGN KEY (team_manager_id)
        REFERENCES team_manager(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_tm_team
        FOREIGN KEY (team_id)
        REFERENCES team(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_team_manager_team
        PRIMARY KEY (team_manager_id, team_id)
);


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

/*
 =====
 MATCHES
 =====
 */

CREATE TABLE IF NOT EXISTS match_proposal (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    sport_type_id BIGINT NOT NULL,
    ruleset_id BIGINT,

    team1_id BIGINT NOT NULL,
    team2_id BIGINT NOT NULL,
    status_id BIGINT NOT NULL,

    location VARCHAR(256),
    venue_type_id BIGINT,

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

    CONSTRAINT pk_match_proposal PRIMARY KEY (id)
);
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

CREATE TABLE IF NOT EXISTS page_text (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    page VARCHAR(50),       -- 'home', 'about', 'contact'
    key VARCHAR(100),       -- 'hero_title', 'hero_subtitle', 'btn_signup'
    language VARCHAR(5),    -- 'uk', 'en', 'de'
    value TEXT,             -- the text itself
    CONSTRAINT unique_page_key_lang
        UNIQUE (page, key, language),

    CONSTRAINT pk_page_text
        PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS ladder_team (
    ladder_id BIGINT NOT NULL,
    team_id BIGINT NOT NULL,

    rank INT,
    rating INT DEFAULT 1000,
    matches_played INT DEFAULT 0,

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
/*
 =====
 TRIGGERS
 =====
 */
CREATE OR REPLACE FUNCTION check_teams_no_common_players()
RETURNS TRIGGER AS $$
DECLARE
    common_count INT;
BEGIN
    SELECT COUNT(*)
    INTO common_count

    FROM player_team pt1
    JOIN player_team pt2 ON pt1.player_id = pt2.player_id

    WHERE pt1.team_id = NEW.team1_id
    AND pt2.team_id = NEW.team2_id;

    IF common_count > 0 THEN
        RAISE WARNING 'Warning: Match has teams with common players';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_teams_no_common_players
ON match_proposal;

CREATE TRIGGER trg_check_teams_no_common_players
    BEFORE INSERT OR UPDATE ON match_proposal
    FOR EACH ROW
EXECUTE FUNCTION check_teams_no_common_players();
