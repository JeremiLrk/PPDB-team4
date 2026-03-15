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

    account_role_id BIGINT NOT NULL,

    CONSTRAINT fk_account_role
        FOREIGN KEY (id)
        REFERENCES account_role_id(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_account
        PRIMARY KEY (id)
);

create table IF NOT EXISTS administrator (
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

    CONSTRAINT fk_club_owner_team_manager
        FOREIGN KEY (id)
        REFERENCES team_manager(id)
        ON DELETE CASCADE,

    CONSTRAINT pk_club_owner
        PRIMARY KEY (id)
);
/*
 =====
 CLUBS
 =====
 */
CREATE TABLE IF NOT EXISTS club (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(64) NOT NULL,

    CONSTRAINT pk_club
        PRIMARY KEY (id)
    );

CREATE TABLE IF NOT EXISTS club_owner_club (
    club_owner_id BIGINT NOT NULL,
    club_id BIGINT NOT NULL,

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

    CONSTRAINT pk_match_rule
        PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS match_rule_set (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(64) NOT NULL,
    description VARCHAR(512),

    CONSTRAINT pk_match_rule_set
        PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS match_rule_set_rule (
    match_rule_set_id BIGINT NOT NULL,
    match_rule_id  INT NOT NULL,

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
    ladder_rating_function_id BIGINT NOT NULL,

    CONSTRAINT fk_ladder_sport_type_id
        FOREIGN KEY (sport_type_id)
        REFERENCES sport_type(id)
        ON DELETE CASCADE,

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

/*
 =====
 DEMO DATA (FOR LIVE SHOWCASE)
 =====
 */

INSERT INTO sport_type (name, minimum_number_of_players_on_a_team, maximum_number_of_players_per_team)
SELECT 'Tennis Singles', 1, 1
WHERE NOT EXISTS (
    SELECT 1 FROM sport_type WHERE name = 'Tennis Singles'
);

INSERT INTO ladder_rating_function (name)
SELECT 'ELO Demo'
WHERE NOT EXISTS (
    SELECT 1 FROM ladder_rating_function WHERE name = 'ELO Demo'
);

INSERT INTO club (name)
SELECT 'NetRank Club'
WHERE NOT EXISTS (
    SELECT 1 FROM club WHERE name = 'NetRank Club'
);

-- Keep demo data deterministic on every startup/deploy run.
DELETE FROM ladder_team
WHERE ladder_id IN (
    SELECT l.id
    FROM ladder l
    WHERE l.club_id = (SELECT id FROM club WHERE name = 'NetRank Club' ORDER BY id LIMIT 1)
);

DELETE FROM ladder
WHERE club_id = (SELECT id FROM club WHERE name = 'NetRank Club' ORDER BY id LIMIT 1);

DELETE FROM team
WHERE club_id = (SELECT id FROM club WHERE name = 'NetRank Club' ORDER BY id LIMIT 1);

INSERT INTO team (club_id, name, sport_type_id)
SELECT
    (SELECT id FROM club WHERE name = 'NetRank Club' ORDER BY id LIMIT 1),
    x.team_name,
    (SELECT id FROM sport_type WHERE name = 'Tennis Singles' ORDER BY id LIMIT 1)
FROM (
    VALUES
        ('Thomas'),
        ('Lars'),
        ('Noah'),
        ('Milan'),
        ('Tom'),
        ('Ben')
) AS x(team_name)
WHERE NOT EXISTS (
    SELECT 1
    FROM team t
    WHERE t.club_id = (SELECT id FROM club WHERE name = 'NetRank Club' ORDER BY id LIMIT 1)
      AND t.name = x.team_name
);

INSERT INTO ladder (club_id, name, description, sport_type_id, ladder_rating_function_id)
SELECT
    (SELECT id FROM club WHERE name = 'NetRank Club' ORDER BY id LIMIT 1),
    x.name,
    x.description,
    (SELECT id FROM sport_type WHERE name = 'Tennis Singles' ORDER BY id LIMIT 1),
    (SELECT id FROM ladder_rating_function WHERE name = 'ELO Demo' ORDER BY id LIMIT 1)
FROM (
    VALUES
        ('Men''s Singles', 'Senior singles ranking.'),
        ('U14 Singles', 'Youth under-14 singles ranking.')
) AS x(name, description)
WHERE NOT EXISTS (
    SELECT 1
    FROM ladder l
    WHERE l.club_id = (SELECT id FROM club WHERE name = 'NetRank Club' ORDER BY id LIMIT 1)
      AND l.name = x.name
);

INSERT INTO ladder_team (ladder_id, team_id, rank, rating, matches_played)
SELECT
    (SELECT id FROM ladder WHERE club_id = (SELECT id FROM club WHERE name = 'NetRank Club' ORDER BY id LIMIT 1) AND name = x.ladder_name ORDER BY id LIMIT 1),
    (SELECT id FROM team WHERE club_id = (SELECT id FROM club WHERE name = 'NetRank Club' ORDER BY id LIMIT 1) AND name = x.team_name ORDER BY id LIMIT 1),
    x.rank,
    x.rating,
    x.matches_played
FROM (
    VALUES
        ('Men''s Singles', 'Thomas', 1, 1290, 14),
        ('Men''s Singles', 'Lars', 2, 1245, 13),
        ('Men''s Singles', 'Noah', 3, 1205, 12),
        ('Men''s Singles', 'Milan', 4, 1170, 11),
        ('U14 Singles', 'Tom', 1, 1150, 10),
        ('U14 Singles', 'Ben', 2, 1120, 9),
        ('U14 Singles', 'Noah', 3, 1085, 8),
        ('U14 Singles', 'Milan', 4, 1050, 7)
) AS x(ladder_name, team_name, rank, rating, matches_played)
ON CONFLICT (ladder_id, team_id)
DO UPDATE SET
    rank = EXCLUDED.rank,
    rating = EXCLUDED.rating,
    matches_played = EXCLUDED.matches_played;
