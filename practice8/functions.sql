-- functions.sql
-- PostgreSQL FUNCTIONS for the PhoneBook app.
-- A function RETURNS a value (scalar or table) and is called with SELECT.
-- Run this file once in psql or pgAdmin to register the functions in the DB:
--   \i functions.sql


-- ─────────────────────────────────────────────────────────────
-- FUNCTION 1: search contacts by pattern
-- ─────────────────────────────────────────────────────────────
-- Returns every row whose first_name, last_name, OR phone
-- contains the supplied pattern (case-insensitive, partial match).
--
-- RETURNS TABLE means this function acts like a virtual table:
--   SELECT * FROM search_contacts('ali');
--
-- || is the SQL string-concatenation operator.
-- ILIKE is case-insensitive LIKE.
-- '%' || p_pattern || '%'  wraps the user's input in wildcards.
--
-- RETURN QUERY feeds the result of a SELECT straight into the
-- function's output stream — no need to loop row-by-row.

CREATE OR REPLACE FUNCTION search_contacts(p_pattern VARCHAR)
RETURNS TABLE(
    id         INT,
    first_name VARCHAR,
    last_name  VARCHAR,
    phone      VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
        SELECT
            pb.id,
            pb.first_name,
            pb.last_name,
            pb.phone
        FROM phonebook pb
        WHERE pb.first_name ILIKE '%' || p_pattern || '%'
           OR pb.last_name  ILIKE '%' || p_pattern || '%'
           OR pb.phone      ILIKE '%' || p_pattern || '%'
        ORDER BY pb.first_name;
END;
$$;

-- How to call it:
--   SELECT * FROM search_contacts('ali');
--   SELECT * FROM search_contacts('+7701');


-- ─────────────────────────────────────────────────────────────
-- FUNCTION 2: paginated query
-- ─────────────────────────────────────────────────────────────
-- Returns a "page" of contacts.
--
-- p_limit  — how many rows per page  (e.g. 10)
-- p_offset — how many rows to skip   (page 1 → 0, page 2 → 10, ...)
--
-- LIMIT restricts the number of rows returned.
-- OFFSET skips the first N rows before starting to return.
-- Together they implement pagination:
--   Page 1: LIMIT 10 OFFSET 0
--   Page 2: LIMIT 10 OFFSET 10
--   Page 3: LIMIT 10 OFFSET 20

CREATE OR REPLACE FUNCTION get_contacts_paginated(
    p_limit  INT,
    p_offset INT
)
RETURNS TABLE(
    id         INT,
    first_name VARCHAR,
    last_name  VARCHAR,
    phone      VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    -- Basic validation: page size must be positive
    IF p_limit <= 0 THEN
        RAISE EXCEPTION 'p_limit must be greater than 0, got %', p_limit;
    END IF;
    IF p_offset < 0 THEN
        RAISE EXCEPTION 'p_offset cannot be negative, got %', p_offset;
    END IF;

    RETURN QUERY
        SELECT
            pb.id,
            pb.first_name,
            pb.last_name,
            pb.phone
        FROM phonebook pb
        ORDER BY pb.id
        LIMIT  p_limit
        OFFSET p_offset;
END;
$$;

-- How to call it:
--   SELECT * FROM get_contacts_paginated(5, 0);   -- page 1, 5 per page
--   SELECT * FROM get_contacts_paginated(5, 5);   -- page 2
--   SELECT * FROM get_contacts_paginated(5, 10);  -- page 3
