-- schema.sql  (TSIS 1)
-- Run once to set up the extended PhoneBook schema.
-- Extends the Practice 7/8 schema with:
--   groups table, phones table, email, birthday on contacts.

-- ── Groups ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Seed the default groups
INSERT INTO groups (name)
VALUES ('Family'), ('Work'), ('Friend'), ('Other')
ON CONFLICT (name) DO NOTHING;

-- ── Contacts (extended) ───────────────────────────────────────────────────────
-- If you already have a "phonebook" table from Practice 7, this creates a
-- fresh "contacts" table.  Adjust if your DB already has "contacts".
CREATE TABLE IF NOT EXISTS contacts (
    id         SERIAL PRIMARY KEY,
    first_name VARCHAR(50)  NOT NULL,
    last_name  VARCHAR(50),
    email      VARCHAR(100),
    birthday   DATE,
    group_id   INTEGER REFERENCES groups(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── Phones (1-to-many) ────────────────────────────────────────────────────────
-- Each contact can have multiple phone numbers with a type label.
CREATE TABLE IF NOT EXISTS phones (
    id         SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20) NOT NULL,
    type       VARCHAR(10) CHECK (type IN ('home', 'work', 'mobile')) DEFAULT 'mobile'
);
