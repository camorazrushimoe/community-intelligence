-- Game catalog: the stable backbone every signal attaches to.
-- Keyed by Steam app id so Steam reviews and Reddit mentions can be joined.

CREATE TABLE games (
    steam_app_id  int PRIMARY KEY,
    name          text NOT NULL,
    name_variants text[] NOT NULL DEFAULT '{}',
    genres        text[] NOT NULL DEFAULT '{}',
    tags          text[] NOT NULL DEFAULT '{}',
    developer     text,
    publisher     text,
    release_date  date,
    price         numeric,
    platforms     text[] NOT NULL DEFAULT '{}'
);
