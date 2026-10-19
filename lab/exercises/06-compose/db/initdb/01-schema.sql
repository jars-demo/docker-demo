-- Runs once, the first time Postgres starts on an empty data directory.

CREATE TABLE notes (
    id serial PRIMARY KEY,
    text text NOT NULL
);

INSERT INTO notes (text)
SELECT 'seed note ' || n FROM generate_series(1, 1000) AS n;

-- Stands in for a slow first start: restoring a snapshot or running a long migration.
SELECT pg_sleep(4);
