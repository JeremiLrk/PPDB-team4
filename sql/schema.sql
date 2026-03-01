-- 1. BASE TABLES (No dependencies)
CREATE TABLE IF NOT EXISTS SportType (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    players_per_team INT
);

CREATE TABLE IF NOT EXISTS RuleSet (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS MatchStatus (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS RatingFunction (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- 2. USER HIERARCHY
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    date_of_birth DATE,
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS admin (
    user_id INT PRIMARY KEY REFERENCES "user"(id),
    access_level VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS teammanager (
    user_id INT PRIMARY KEY REFERENCES "user"(id)
);

CREATE TABLE IF NOT EXISTS clubowner (
    user_id INT PRIMARY KEY REFERENCES "user"(id)
);

-- 3. RULES & CLUBS
CREATE TABLE IF NOT EXISTS Rule (
    id SERIAL PRIMARY KEY,
    sport_type_id INT REFERENCES SportType(id),
    name VARCHAR(255) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS RuleSet_rules (
    rule_set_id INT REFERENCES RuleSet(id),
    rule_id INT REFERENCES Rule(id),
    PRIMARY KEY (rule_set_id, rule_id)
);

CREATE TABLE IF NOT EXISTS club (
    id SERIAL PRIMARY KEY,
    owner_id INT REFERENCES clubowner(user_id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    ruleset_id INT REFERENCES RuleSet(id)
);

-- 4. TEAMS & LADDERS
CREATE TABLE IF NOT EXISTS team (
    id SERIAL PRIMARY KEY,
    sport_type_id INT REFERENCES SportType(id),
    club_id INT REFERENCES club(id),
    minimum_time_between_matches INTERVAL,
    availabilty_for_match BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS player (
    user_id INT PRIMARY KEY REFERENCES "user"(id),
    team_id INT references team
);

CREATE TABLE IF NOT EXISTS ladder (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sporttype_id INT REFERENCES SportType(id),
    rating_parameters INT REFERENCES RatingFunction(id),
    scheduling_frequency INTERVAL, 
    ruleset_id INT REFERENCES RuleSet(id),
    nr_of_players_per_team INT,
    club_id INT REFERENCES club(id)
);

-- 5. RELATIONSHIP TABLES (Many-to-Many)
CREATE TABLE IF NOT EXISTS managerteams (
    manager_id INT REFERENCES teammanager(user_id),
    team_id INT REFERENCES team(id),
    PRIMARY KEY (manager_id, team_id)
);

CREATE TABLE IF NOT EXISTS participatesinladder (
    ladder_id INT REFERENCES ladder(id),
    team_id INT REFERENCES team(id),
    PRIMARY KEY (ladder_id, team_id)
);

CREATE TABLE IF NOT EXISTS teamlist (
    team_id INT REFERENCES team(id),
    player_id INT REFERENCES player(user_id),
    PRIMARY KEY (team_id, player_id)
);

CREATE TABLE IF NOT EXISTS clubteams (
    club_id INT REFERENCES club(id),
    team_id INT REFERENCES team(id),
    PRIMARY KEY (club_id, team_id)
);

-- 6. MATCHES
CREATE TABLE IF NOT EXISTS MatchProposal (
    id SERIAL PRIMARY KEY,
    sport_type_id INT REFERENCES SportType(id),
    ruleset_id INT REFERENCES RuleSet(id),
    team1_id INT REFERENCES team(id),
    team2_id INT REFERENCES team(id),
    status_id INT REFERENCES MatchStatus(id),
    date_of_match DATE NOT NULL,
    score_team_1 INT DEFAULT 0,
    score_team_2 INT DEFAULT 0,
  	accepted bool default false
);
--Ladder itself
CREATE TABLE IF NOT EXISTS LadderStanding (
    ladder_id INT REFERENCES ladder(id),
    team_id INT REFERENCES team(id),
    current_rating INT DEFAULT 1200,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    draws INT DEFAULT 0,
    PRIMARY KEY (ladder_id, team_id)
);