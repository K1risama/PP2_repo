# phonebook.py  (TSIS 1)
# Extended PhoneBook with:
#   - Multi-phone contacts (phones table)
#   - Email, birthday, group fields
#   - Filter by group, search by email, sort results
#   - Paginated navigation (next / prev / quit)
#   - Export / import JSON
#   - Extended CSV import
#   - New stored procedures: add_phone, move_to_group, search_contacts

import json
import csv
import os
from datetime import datetime
from connect import get_connection


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def print_contacts(rows, headers=None):
    """Pretty-print a list of tuples with optional column headers."""
    if not rows:
        print("  (no results)")
        return
    if headers:
        print("  " + " | ".join(f"{h:<18}" for h in headers))
        print("  " + "-" * (21 * len(headers)))
    for row in rows:
        print("  " + " | ".join(f"{str(v):<18}" for v in row))


def ask(prompt, default=None):
    """Prompt the user; return stripped input or default if blank."""
    val = input(prompt).strip()
    return val if val else default


# ─────────────────────────────────────────────────────────────────────────────
# 1. Filter contacts by group
# ─────────────────────────────────────────────────────────────────────────────

def filter_by_group():
    """Show all groups, let user pick one, then list its contacts."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # List available groups
            cur.execute("SELECT id, name FROM groups ORDER BY name;")
            groups = cur.fetchall()
            if not groups:
                print("  No groups found.")
                return
            print("\n  Available groups:")
            for gid, gname in groups:
                print(f"    [{gid}] {gname}")

            try:
                gid_choice = int(input("  Enter group ID: ").strip())
            except ValueError:
                print("  Invalid input.")
                return

            cur.execute("""
                SELECT c.id, c.first_name, c.last_name, c.email, c.birthday
                FROM contacts c
                WHERE c.group_id = %s
                ORDER BY c.first_name;
            """, (gid_choice,))
            rows = cur.fetchall()

    print(f"\n--- Contacts in group {gid_choice} ---")
    print_contacts(rows, ["ID", "First", "Last", "Email", "Birthday"])


# ─────────────────────────────────────────────────────────────────────────────
# 2. Search by email (partial match)
# ─────────────────────────────────────────────────────────────────────────────

def search_by_email():
    """Search contacts whose email contains the given pattern."""
    pattern = ask("  Email pattern (e.g. gmail): ", "")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.first_name, c.last_name, c.email
                FROM contacts c
                WHERE c.email ILIKE %s
                ORDER BY c.first_name;
            """, (f"%{pattern}%",))
            rows = cur.fetchall()

    print(f"\n--- Email search: '{pattern}' ---")
    print_contacts(rows, ["ID", "First", "Last", "Email"])


# ─────────────────────────────────────────────────────────────────────────────
# 3. Search contacts (full pattern via DB function)
# ─────────────────────────────────────────────────────────────────────────────

def search_contacts():
    """Call the DB search_contacts() function that matches name/email/phone."""
    pattern = ask("  Search pattern: ", "")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM search_contacts(%s::TEXT);", (pattern,))
            rows = cur.fetchall()

    print(f"\n--- Search results for '{pattern}' ---")
    print_contacts(rows, ["ID", "First", "Last", "Email", "Birthday", "Group"])


# ─────────────────────────────────────────────────────────────────────────────
# 4. Sort and list all contacts
# ─────────────────────────────────────────────────────────────────────────────

def list_sorted():
    """List all contacts sorted by user's choice: name / birthday / date added."""
    print("  Sort by: [1] Name  [2] Birthday  [3] Date added")
    choice = ask("  Choice: ", "1")
    order_map = {"1": "c.first_name", "2": "c.birthday", "3": "c.created_at"}
    order_col = order_map.get(choice, "c.first_name")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT c.id, c.first_name, c.last_name, c.email,
                       c.birthday, g.name AS grp, c.created_at
                FROM contacts c
                LEFT JOIN groups g ON c.group_id = g.id
                ORDER BY {order_col} NULLS LAST;
            """)
            rows = cur.fetchall()

    print(f"\n--- All contacts (sorted by {order_col}) ---")
    print_contacts(rows, ["ID", "First", "Last", "Email", "Birthday", "Group", "Created"])


# ─────────────────────────────────────────────────────────────────────────────
# 5. Paginated navigation using the existing DB function
# ─────────────────────────────────────────────────────────────────────────────

def paginated_view():
    """Navigate contacts page by page using the DB get_contacts_paginated()."""
    try:
        limit = int(ask("  Rows per page [default 5]: ", "5"))
    except ValueError:
        limit = 5

    offset = 0
    while True:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM get_contacts_paginated(%s, %s);",
                            (limit, offset))
                rows = cur.fetchall()

        page = (offset // limit) + 1
        print(f"\n--- Page {page} (offset={offset}) ---")
        print_contacts(rows, ["ID", "First", "Last", "Phone"])

        if not rows:
            print("  (end of contacts)")

        nav = ask("\n  [n]ext  [p]rev  [q]uit: ", "q").lower()
        if nav == "n":
            if rows:
                offset += limit
            else:
                print("  Already at last page.")
        elif nav == "p":
            offset = max(0, offset - limit)
        else:
            break


# ─────────────────────────────────────────────────────────────────────────────
# 5b. Add / upsert a contact directly into the contacts table
# ─────────────────────────────────────────────────────────────────────────────

def add_contact():
    """Insert a new contact (or update if first_name already exists)."""
    first = ask("  First name: ", "")
    if not first:
        print("  First name is required.")
        return
    last  = ask("  Last name (optional): ", None)
    email = ask("  Email (optional): ", None)
    bday  = ask("  Birthday YYYY-MM-DD (optional): ", None)
    grp   = ask("  Group (Family/Work/Friend/Other, optional): ", None)

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Resolve group id
            g_id = None
            if grp:
                cur.execute(
                    "SELECT id FROM groups WHERE name ILIKE %s LIMIT 1;",
                    (grp,)
                )
                row = cur.fetchone()
                if row:
                    g_id = row[0]
                else:
                    cur.execute(
                        "INSERT INTO groups (name) VALUES (%s) RETURNING id;",
                        (grp,)
                    )
                    g_id = cur.fetchone()[0]

            # Upsert contact
            cur.execute(
                "SELECT id FROM contacts WHERE first_name ILIKE %s LIMIT 1;",
                (first,)
            )
            existing = cur.fetchone()
            if existing:
                cur.execute("""
                    UPDATE contacts
                       SET last_name=%s, email=%s, birthday=%s, group_id=%s
                     WHERE id=%s;
                """, (last, email, bday or None, g_id, existing[0]))
                print(f"  Updated existing contact '{first}'.")
            else:
                cur.execute("""
                    INSERT INTO contacts (first_name, last_name, email, birthday, group_id)
                    VALUES (%s, %s, %s, %s, %s);
                """, (first, last, email, bday or None, g_id))
                print(f"  Contact '{first}' added.")

            # Optionally add a phone right away
            phone = ask("  Phone number (optional, leave blank to skip): ", None)
            if phone:
                ptype = ask("  Phone type (home/work/mobile) [mobile]: ", "mobile")
                # Fetch the contact id we just inserted/updated
                cur.execute(
                    "SELECT id FROM contacts WHERE first_name ILIKE %s LIMIT 1;",
                    (first,)
                )
                cid = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s::VARCHAR);",
                    (cid, phone, ptype)
                )
                print(f"  Phone '{phone}' added.")

        conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# 6. Add a phone to an existing contact (calls procedure add_phone)
# ─────────────────────────────────────────────────────────────────────────────

def add_phone():
    """Call the add_phone stored procedure with explicit VARCHAR casts."""
    name  = ask("  Contact first name: ", "")
    phone = ask("  Phone number: ", "")
    ptype = ask("  Type (home/work/mobile) [mobile]: ", "mobile")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "CALL add_phone(%s::VARCHAR, %s::VARCHAR, %s::VARCHAR);",
                (name, phone, ptype)
            )
        conn.commit()
    print(f"  Phone added to '{name}'.")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Move contact to group (calls procedure move_to_group)
# ─────────────────────────────────────────────────────────────────────────────

def move_to_group():
    """Call the move_to_group stored procedure."""
    name  = ask("  Contact first name: ", "")
    group = ask("  Group name (Family/Work/Friend/Other or new): ", "Other")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "CALL move_to_group(%s::VARCHAR, %s::VARCHAR);",
                (name, group)
            )
        conn.commit()
    print(f"  '{name}' moved to group '{group}'.")


# ─────────────────────────────────────────────────────────────────────────────
# 8. Export all contacts to JSON
# ─────────────────────────────────────────────────────────────────────────────

def export_to_json():
    """Write all contacts (with phones and group) to contacts_export.json."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.first_name, c.last_name, c.email,
                       c.birthday::text, g.name AS grp
                FROM contacts c
                LEFT JOIN groups g ON c.group_id = g.id
                ORDER BY c.id;
            """)
            contacts = cur.fetchall()

            result = []
            for row in contacts:
                cid, first, last, email, bday, grp = row
                # Fetch all phones for this contact
                cur.execute(
                    "SELECT phone, type FROM phones WHERE contact_id = %s;",
                    (cid,)
                )
                phones = [{"phone": p, "type": t} for p, t in cur.fetchall()]
                result.append({
                    "first_name": first,
                    "last_name":  last,
                    "email":      email,
                    "birthday":   bday,
                    "group":      grp,
                    "phones":     phones,
                })

    filename = "contacts_export.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  Exported {len(result)} contacts to '{filename}'.")


# ─────────────────────────────────────────────────────────────────────────────
# 9. Import contacts from JSON
# ─────────────────────────────────────────────────────────────────────────────

def import_from_json():
    """Read contacts_export.json and insert into DB; handle duplicates."""
    filename = ask("  JSON file path [contacts_export.json]: ", "contacts_export.json")
    if not os.path.exists(filename):
        print(f"  File '{filename}' not found.")
        return

    with open(filename, encoding="utf-8") as f:
        records = json.load(f)

    inserted = updated = skipped = 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            for rec in records:
                first = rec.get("first_name", "")
                last  = rec.get("last_name")
                email = rec.get("email")
                bday  = rec.get("birthday")
                grp   = rec.get("group")
                phones = rec.get("phones", [])

                # Resolve group id
                g_id = None
                if grp:
                    cur.execute("SELECT id FROM groups WHERE name ILIKE %s LIMIT 1;", (grp,))
                    g_row = cur.fetchone()
                    if g_row:
                        g_id = g_row[0]
                    else:
                        cur.execute("INSERT INTO groups (name) VALUES (%s) RETURNING id;", (grp,))
                        g_id = cur.fetchone()[0]

                # Check duplicate
                cur.execute(
                    "SELECT id FROM contacts WHERE first_name ILIKE %s LIMIT 1;",
                    (first,)
                )
                existing = cur.fetchone()

                if existing:
                    action = ask(
                        f"  Duplicate '{first}'. [s]kip / [o]verwrite? ", "s"
                    ).lower()
                    if action == "o":
                        cid = existing[0]
                        cur.execute("""
                            UPDATE contacts
                               SET last_name=%s, email=%s, birthday=%s, group_id=%s
                             WHERE id=%s;
                        """, (last, email, bday, g_id, cid))
                        cur.execute("DELETE FROM phones WHERE contact_id=%s;", (cid,))
                        updated += 1
                    else:
                        skipped += 1
                        continue
                else:
                    cur.execute("""
                        INSERT INTO contacts (first_name, last_name, email, birthday, group_id)
                        VALUES (%s, %s, %s, %s, %s) RETURNING id;
                    """, (first, last, email, bday, g_id))
                    cid = cur.fetchone()[0]
                    inserted += 1

                # Insert phones
                for ph in phones:
                    cur.execute(
                        "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s);",
                        (cid, ph.get("phone"), ph.get("type", "mobile"))
                    )

        conn.commit()

    print(f"  Import done. Inserted: {inserted}, Updated: {updated}, Skipped: {skipped}.")


# ─────────────────────────────────────────────────────────────────────────────
# 10. Extended CSV import (supports email, birthday, group, phone type)
# ─────────────────────────────────────────────────────────────────────────────
# Expected CSV columns:
#   first_name, last_name, email, birthday, group, phone, phone_type

def import_from_csv():
    """Import contacts from a CSV file with extended fields."""
    filename = ask("  CSV file path [contacts.csv]: ", "contacts.csv")
    if not os.path.exists(filename):
        print(f"  File '{filename}' not found.")
        return

    imported = 0
    errors   = 0

    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        with get_connection() as conn:
            with conn.cursor() as cur:
                for row in reader:
                    try:
                        first = row.get("first_name", "").strip()
                        last  = row.get("last_name", "").strip() or None
                        email = row.get("email", "").strip() or None
                        bday  = row.get("birthday", "").strip() or None
                        grp   = row.get("group", "").strip() or None
                        phone = row.get("phone", "").strip() or None
                        ptype = row.get("phone_type", "mobile").strip() or "mobile"

                        if not first:
                            continue

                        # Resolve group
                        g_id = None
                        if grp:
                            cur.execute("SELECT id FROM groups WHERE name ILIKE %s LIMIT 1;", (grp,))
                            g_row = cur.fetchone()
                            g_id = g_row[0] if g_row else None

                        # Upsert contact
                        cur.execute(
                            "SELECT id FROM contacts WHERE first_name ILIKE %s LIMIT 1;",
                            (first,)
                        )
                        existing = cur.fetchone()
                        if existing:
                            cid = existing[0]
                        else:
                            cur.execute("""
                                INSERT INTO contacts (first_name, last_name, email, birthday, group_id)
                                VALUES (%s, %s, %s, %s, %s) RETURNING id;
                            """, (first, last, email, bday, g_id))
                            cid = cur.fetchone()[0]

                        # Insert phone if provided
                        if phone:
                            cur.execute(
                                "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s);",
                                (cid, phone, ptype)
                            )

                        imported += 1
                    except Exception as e:
                        print(f"  Error on row {row}: {e}")
                        errors += 1

            conn.commit()

    print(f"  CSV import done. Imported: {imported}, Errors: {errors}.")

def delete_contact():
    name = ask("  Enter first name of contact to delete: ", "")
    if not name:
        print("  Name is required.")
        return

    with get_connection() as conn:
        with conn.cursor() as cur:
            # найти контакт
            cur.execute(
                "SELECT id FROM contacts WHERE first_name ILIKE %s LIMIT 1;",
                (name,)
            )
            row = cur.fetchone()

            if not row:
                print(f"  Contact '{name}' not found.")
                return

            cid = row[0]

            # удалить сначала телефоны (из-за внешнего ключа)
            cur.execute("DELETE FROM phones WHERE contact_id=%s;", (cid,))
            # потом сам контакт
            cur.execute("DELETE FROM contacts WHERE id=%s;", (cid,))

        conn.commit()

    print(f"  Contact '{name}' deleted.")

# ─────────────────────────────────────────────────────────────────────────────
# Main menu
# ─────────────────────────────────────────────────────────────────────────────

MENU = """
╔══════════════════════════════════════════════════════╗
║   PhoneBook TSIS 1 — Extended Contact Management     ║
╠══════════════════════════════════════════════════════╣
║  1.  Add / update contact                            ║
║  2.  Filter contacts by group                        ║
║  3.  Search by email (partial match)                 ║
║  4.  Search contacts (name / email / phone)          ║
║  5.  List all contacts (sorted)                      ║
║  6.  Paginated navigation                            ║
║  7.  Add phone to existing contact                   ║
║  8.  Move contact to group                           ║
║  9.  Export contacts to JSON                         ║
║  10. Import contacts from JSON                       ║
║  11. Import contacts from CSV                        ║
║  12. Delete contact                                  ║
║  0.  Exit                                            ║
╚══════════════════════════════════════════════════════╝
"""

ACTIONS = {
    "1":  add_contact,
    "2":  filter_by_group,
    "3":  search_by_email,
    "4":  search_contacts,
    "5":  list_sorted,
    "6":  paginated_view,
    "7":  add_phone,
    "8":  move_to_group,
    "9":  export_to_json,
    "10": import_from_json,
    "11": import_from_csv,
    "12": delete_contact,
}


def main():
    while True:
        print(MENU)
        choice = input("Your choice: ").strip()
        if choice == "0":
            print("Goodbye!")
            break
        action = ACTIONS.get(choice)
        if action:
            try:
                action()
            except Exception as e:
                print(f"  Error: {e}")
        else:
            print("  Unknown option.")


if __name__ == "__main__":
    main()
