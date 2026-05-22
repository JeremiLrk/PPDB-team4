/*
 =====
 USERS
 =====
 Accounts share one base table and extend into role-specific tables through
 one-to-one primary-key foreign keys.
 */

CREATE TABLE IF NOT EXISTS account_role (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) NOT NULL UNIQUE,

    CONSTRAINT pk_account_role
        PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS account (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    first_name VARCHAR(32),
    last_name VARCHAR(32),
    date_of_birth DATE,
    gender VARCHAR(32),
    phone VARCHAR(64),
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
