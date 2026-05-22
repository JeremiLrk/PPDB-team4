/*
 =====
 CLUBS
 =====
 Clubs group teams, owners, and players. Permission flags live on join tables
 so access can vary per club or team.
 */

CREATE TABLE IF NOT EXISTS club (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(64) NOT NULL,
    description VARCHAR(512),
    sport_type_id BIGINT,
    city VARCHAR(128),

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
    can_manage_match BOOLEAN NOT NULL DEFAULT false,
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

    -- Team names are unique within a club. Club-less teams are covered by
    -- the partial unique index below because PostgreSQL treats NULL values
    -- as distinct in regular unique constraints.
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
-- Team names are also unique for independent teams without a club.
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
    can_manage_match BOOLEAN NOT NULL DEFAULT false,

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

CREATE TABLE IF NOT EXISTS team_join_request (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    team_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    date TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    CONSTRAINT fk_team_join_request_team
        FOREIGN KEY (team_id)
            REFERENCES team(id)
            ON DELETE CASCADE,

    CONSTRAINT fk_team_join_request_user
        FOREIGN KEY (user_id)
            REFERENCES account(id)
            ON DELETE CASCADE,

    CONSTRAINT pk_team_join_request
        PRIMARY KEY (id)
);

-- A user can have one pending join request per team. Completed requests do
-- not block a later request.
CREATE UNIQUE INDEX IF NOT EXISTS uq_team_join_request_pending
    ON team_join_request (team_id, user_id)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_team_join_request_status
    ON team_join_request(team_id, status);
