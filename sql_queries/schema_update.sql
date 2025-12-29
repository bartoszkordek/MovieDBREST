PRAGMA foreign_keys = ON;
BEGIN;
-- create new tables
CREATE TABLE actor (
   id INTEGER PRIMARY KEY,
   name VARCHAR(256),
   surname VARCHAR(256)
);

CREATE TABLE movie (
   id INTEGER PRIMARY KEY,
   title VARCHAR(256),
   director VARCHAR(256),
   year INTEGER,
   description TEXT
);

CREATE TABLE movie_actor_through (
   id INTEGER PRIMARY KEY,
   movie_id INTEGER NOT NULL,
   actor_id INTEGER NOT NULL,
   FOREIGN KEY(movie_id) REFERENCES movie(id) ON DELETE CASCADE,
   FOREIGN KEY(actor_id) REFERENCES actor(id) ON DELETE CASCADE
);

SAVEPOINT createNewTables;

-- fill movie table with existing data (from movies)
INSERT OR IGNORE INTO movie (id, title, year)
SELECT ID, title, year FROM movies;

-- fill actor table
INSERT INTO actor (name, surname)
WITH RECURSIVE split_actors(actor_full, rest) AS (
    SELECT NULL, actors || ','
    FROM movies
    UNION ALL
    SELECT
        trim(substr(rest, 1, instr(rest, ',') - 1)),
        substr(rest, instr(rest, ',') + 1)
    FROM split_actors
    WHERE rest <> ''
)
SELECT
    substr(actor_full, 1, instr(actor_full, ' ') - 1) AS name,
    substr(actor_full, instr(actor_full, ' ') + 1) AS surname
FROM split_actors
WHERE actor_full IS NOT NULL AND actor_full <> '';

-- fill movie_actor_through table
INSERT INTO movie_actor_through (movie_id, actor_id)
WITH RECURSIVE split(movie_id, actor_full, rest) AS (
    SELECT id, NULL, actors || ',' FROM movies
    UNION ALL
    SELECT movie_id, trim(substr(rest, 1, instr(rest, ',') - 1)), substr(rest, instr(rest, ',') + 1)
    FROM split WHERE rest <> ''
)
SELECT
    split.movie_id,
    actor.id
FROM split
JOIN actor ON actor.name = substr(split.actor_full, 1, instr(split.actor_full, ' ') - 1)
           AND actor.surname = substr(split.actor_full, instr(split.actor_full, ' ') + 1)
WHERE split.actor_full IS NOT NULL AND split.actor_full <> '';

SAVEPOINT fillTablesWithExistingData;

-- remove movies table
DROP TABLE movies;

SAVEPOINT removeMoviesTable;


-- add missing values in movie table
UPDATE movie
SET
    director = 'Lana Wachowski',
    description = 'The Matrix is a sci-fi film where hacker Neo discovers his reality is a simulated world (the Matrix) created by machines to enslave humanity, using their bodies for energy, and joins rebels led by Morpheus and Trinity to fight for humanity''s freedom, becoming \"The One,\" a prophesied savior capable of manipulating the simulation. '
WHERE
    title = 'The Matrix';

UPDATE movie
SET
    director = 'Steven Spielberg',
    description = 'Indiana Jones (Dr. Henry Jones, Jr.) is an iconic American archaeologist and adventurer, famous for his fedora, leather jacket, and bullwhip, who globe-trots to find powerful ancient artifacts, often clashing with Nazis or other villains to secure them from falling into the wrong hands. Created by George Lucas, he''s a history professor by day and a daring treasure hunter by night, embodying classic pulp heroes in a series of popular films starting with Raiders of the Lost Ark.'
WHERE
    title = 'Indiana Jones';

UPDATE movie
SET
    director = 'Martin Campbell',
    description = 'Casino Royale is the iconic first James Bond novel (1953) and the basis for several films, notably the gritty 2006 reboot starring Daniel Craig, about a newly minted 00 agent''s first mission to bankrupt terrorist financier Le Chiffre in a high-stakes poker game, where he battles deception, betrayal, and falls for Treasury agent Vesper Lynd, learning the brutal realities of espionage and trust.'
WHERE
    title = 'Casino Royal';

SAVEPOINT addMissingMovieData;

COMMIT;