-- procedures.sql  (TSIS 1)
-- New PL/pgSQL objects for the extended PhoneBook.
-- Run after schema.sql:   \i procedures.sql


-- ─────────────────────────────────────────────────────────────────────────────
-- PROCEDURE: add_phone
-- Adds a new phone number to an existing contact (by first name).
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR DEFAULT 'mobile'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    -- Look up the contact id (case-insensitive match on first_name)
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE first_name ILIKE p_contact_name
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type);

    RAISE NOTICE 'Added % phone "%" to contact id %', p_type, p_phone, v_contact_id;
END;
$$;


-- ─────────────────────────────────────────────────────────────────────────────
-- PROCEDURE: move_to_group
-- Moves a contact to a different group; creates the group if it does not exist.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id   INTEGER;
BEGIN
    -- Find contact
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE first_name ILIKE p_contact_name
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    -- Find or create group
    SELECT id INTO v_group_id FROM groups WHERE name ILIKE p_group_name LIMIT 1;

    IF v_group_id IS NULL THEN
        INSERT INTO groups (name) VALUES (p_group_name) RETURNING id INTO v_group_id;
        RAISE NOTICE 'Created new group "%"', p_group_name;
    END IF;

    -- Move contact
    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;

    RAISE NOTICE 'Moved contact "%" to group "%"', p_contact_name, p_group_name;
END;
$$;


-- ─────────────────────────────────────────────────────────────────────────────
-- FUNCTION: search_contacts
-- Extends the Practice 8 pattern-search to also match email and all phones
-- in the phones table (multi-phone schema).
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE(
    id         INT,
    first_name VARCHAR,
    last_name  VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
        SELECT DISTINCT
            c.id,
            c.first_name,
            c.last_name,
            c.email,
            c.birthday,
            g.name AS group_name
        FROM contacts c
        LEFT JOIN groups g ON c.group_id = g.id
        LEFT JOIN phones p ON p.contact_id = c.id
        WHERE
            c.first_name ILIKE '%' || p_query || '%'
            OR c.last_name  ILIKE '%' || p_query || '%'
            OR c.email      ILIKE '%' || p_query || '%'
            OR p.phone      ILIKE '%' || p_query || '%'
        ORDER BY c.first_name;
END;
$$;
