-- procedures.sql
-- PostgreSQL STORED PROCEDURES for the PhoneBook app.
-- A procedure PERFORMS ACTIONS (insert/update/delete) and is called with CALL.
-- Run this file once:  \i procedures.sql


-- ─────────────────────────────────────────────────────────────
-- PROCEDURE 1: upsert a single contact
-- ─────────────────────────────────────────────────────────────
-- "Upsert" = INSERT or UPDATE.
-- If a contact with the given first_name already exists → update their phone.
-- If not → insert a new row.
--
-- EXISTS(SELECT 1 ...) returns TRUE if the subquery finds at least one row.
-- This is cheaper than SELECT COUNT(*) because it stops at the first match.
--
-- IF / THEN / ELSE / END IF  is PL/pgSQL's conditional block.

CREATE OR REPLACE PROCEDURE upsert_contact(
    p_first_name VARCHAR,
    p_last_name  VARCHAR,
    p_phone      VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM phonebook WHERE first_name = p_first_name
    ) THEN
        -- Contact found: update phone number
        UPDATE phonebook
           SET phone = p_phone
         WHERE first_name = p_first_name;
        RAISE NOTICE 'Updated phone for %', p_first_name;
    ELSE
        -- Contact not found: insert new row
        INSERT INTO phonebook (first_name, last_name, phone)
        VALUES (p_first_name, p_last_name, p_phone);
        RAISE NOTICE 'Inserted new contact %', p_first_name;
    END IF;
END;
$$;

-- How to call it:
--   CALL upsert_contact('Alice', 'Smith', '+77011111111');
--   CALL upsert_contact('Alice', 'Smith', '+77019999999'); -- updates phone


-- ─────────────────────────────────────────────────────────────
-- PROCEDURE 2: bulk insert with phone validation
-- ─────────────────────────────────────────────────────────────
-- Accepts two parallel arrays: names and phones.
-- For each pair it validates the phone number.
-- Valid pairs  → inserted (or upserted) into phonebook.
-- Invalid pairs → collected and returned via a temp table so the
--                 caller can see exactly what was rejected.
--
-- UNNEST() expands an array into a set of rows.
-- FOR ... IN ... LOOP iterates over those rows one at a time.
-- ~ is the PostgreSQL regex match operator; ~* is case-insensitive.
-- TEMP TABLE lives only for the current session / transaction.
--
-- Phone validation rule used here:
--   Must start with + followed by 7 to 15 digits  → ^\+[0-9]{7,15}$
--   Adjust the regex to match your country's format.

CREATE OR REPLACE PROCEDURE bulk_insert_contacts(
    p_names  VARCHAR[],   -- array of first names,  e.g. ARRAY['Alice','Bob']
    p_phones VARCHAR[]    -- array of phone numbers, e.g. ARRAY['+77011234567','bad']
)
LANGUAGE plpgsql AS $$
DECLARE
    v_name     VARCHAR;
    v_phone    VARCHAR;
    v_idx      INT := 1;
    v_total    INT;
    v_invalid  INT := 0;
BEGIN
    -- Create a temporary table to collect rejected rows.
    -- ON COMMIT DROP means it disappears at the end of the transaction.
    CREATE TEMP TABLE IF NOT EXISTS invalid_contacts (
        bad_name  VARCHAR,
        bad_phone VARCHAR
    ) ON COMMIT DROP;

    -- Clear any leftovers from a previous call in the same session
    DELETE FROM invalid_contacts;

    v_total := array_length(p_names, 1);

    IF v_total IS NULL OR v_total = 0 THEN
        RAISE NOTICE 'No data provided.';
        RETURN;
    END IF;

    -- Loop over every index from 1 to array length
    -- PL/pgSQL arrays are 1-indexed (unlike Python's 0-indexed)
    FOR v_idx IN 1 .. v_total LOOP
        v_name  := p_names[v_idx];
        v_phone := p_phones[v_idx];

        -- Phone validation: must be + followed by 7-15 digits
        IF v_phone ~ '^\+[0-9]{7,15}$' THEN
            -- Valid: upsert the contact
            IF EXISTS (SELECT 1 FROM phonebook WHERE first_name = v_name) THEN
                UPDATE phonebook SET phone = v_phone WHERE first_name = v_name;
            ELSE
                INSERT INTO phonebook (first_name, phone)
                VALUES (v_name, v_phone);
            END IF;
        ELSE
            -- Invalid: log it for the caller to inspect
            INSERT INTO invalid_contacts (bad_name, bad_phone)
            VALUES (v_name, v_phone);
            v_invalid := v_invalid + 1;
            RAISE NOTICE 'Invalid phone skipped — name: %, phone: %', v_name, v_phone;
        END IF;
    END LOOP;

    RAISE NOTICE 'Bulk insert done. Processed: %, invalid: %', v_total, v_invalid;
    -- After CALL, the caller queries:  SELECT * FROM invalid_contacts;
END;
$$;

-- How to call it:
--   CALL bulk_insert_contacts(
--       ARRAY['Carol','Dave','Eve'],
--       ARRAY['+77031112233', 'not-a-phone', '+77057778899']
--   );
--   SELECT * FROM invalid_contacts;   -- shows Dave's bad number


-- ─────────────────────────────────────────────────────────────
-- PROCEDURE 3: delete by username or phone
-- ─────────────────────────────────────────────────────────────
-- p_mode: 'name'  → delete by first_name (case-insensitive)
--         'phone' → delete by exact phone number
--
-- GET DIAGNOSTICS captures the number of rows affected by the
-- most recent DML statement — equivalent to cur.rowcount in Python.

CREATE OR REPLACE PROCEDURE delete_contact(
    p_mode  VARCHAR,   -- 'name' or 'phone'
    p_value VARCHAR    -- the name or phone number to delete
)
LANGUAGE plpgsql AS $$
DECLARE
    v_deleted INT;
BEGIN
    IF p_mode = 'name' THEN
        DELETE FROM phonebook WHERE first_name ILIKE p_value;

    ELSIF p_mode = 'phone' THEN
        DELETE FROM phonebook WHERE phone = p_value;

    ELSE
        -- RAISE EXCEPTION rolls back the current transaction and
        -- sends the error message back to the caller.
        RAISE EXCEPTION 'Unknown mode "%". Use ''name'' or ''phone''.', p_mode;
    END IF;

    -- GET DIAGNOSTICS fills v_deleted with the row count of the last DELETE
    GET DIAGNOSTICS v_deleted = ROW_COUNT;

    IF v_deleted = 0 THEN
        RAISE NOTICE 'No contact found with % = %', p_mode, p_value;
    ELSE
        RAISE NOTICE 'Deleted % row(s) where % = %', v_deleted, p_mode, p_value;
    END IF;
END;
$$;

-- How to call it:
--   CALL delete_contact('name',  'Alice');
--   CALL delete_contact('phone', '+77011234567');
