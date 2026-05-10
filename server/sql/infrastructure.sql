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
    minimum_number_of_players_on_a_team INT,
    maximum_number_of_players_per_team INT,

    CONSTRAINT pk_sport_type
    PRIMARY KEY (id),

    CHECK (minimum_number_of_players_on_a_team IS NULL OR minimum_number_of_players_on_a_team > 0),
    CHECK (maximum_number_of_players_per_team IS NULL OR maximum_number_of_players_per_team > 0),

    CONSTRAINT chk_min_le_max
        CHECK (
            minimum_number_of_players_on_a_team IS NULL
            OR maximum_number_of_players_per_team IS NULL
            OR minimum_number_of_players_on_a_team <= maximum_number_of_players_per_team
        )
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
