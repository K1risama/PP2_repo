# phonebook.py  (Practice 8)
# Calls PostgreSQL functions and procedures from Python using psycopg2.
#
# Before running:
#   1. Make sure the Practice 7 phonebook table exists.
#   2. Load the SQL files into PostgreSQL:
#        psql -d phonebook_db -f functions.sql
#        psql -d phonebook_db -f procedures.sql
#   3. Run this file:  python phonebook.py

from connect import get_connection   


# Helper: pretty-print a list of rows

def print_rows(rows):
    if not rows:
        print("  (no results)")
        return
    for row in rows:
        print(" ", row)


# 1. Call search_contacts() — a FUNCTION returning a table

def search_contacts(pattern: str):
    """
    Calls the PostgreSQL function search_contacts(pattern).

    Functions that return tables are called with SELECT ... FROM func().
    The result comes back as a normal list of tuples — same as any SELECT.
    """
    sql = "SELECT * FROM search_contacts(%s);"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (pattern,))
            rows = cur.fetchall()

    print(f"\n--- Search results for '{pattern}' ---")
    print_rows(rows)
    return rows



# 2. Call get_contacts_paginated() — a FUNCTION with LIMIT/OFFSET

def get_page(limit: int, offset: int):
    """
    Calls the PostgreSQL function get_contacts_paginated(limit, offset).

    limit  = rows per page
    offset = how many rows to skip (page_number - 1) * limit
    """
    sql = "SELECT * FROM get_contacts_paginated(%s, %s);"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit, offset))
            rows = cur.fetchall()

    page_number = (offset // limit) + 1
    print(f"\n--- Page {page_number} (limit={limit}, offset={offset}) ---")
    print_rows(rows)
    return rows


# 3. Call upsert_contact() — a STORED PROCEDURE

def upsert_contact(first_name: str, last_name: str, phone: str):
    """
    Calls the PostgreSQL procedure upsert_contact(first, last, phone).

    Procedures are called with CALL, NOT SELECT.
    psycopg2 treats CALL like any other statement — pass args as %s.
    No return value; logic is inside the procedure.
    Procedures manage their own transactions, so we still commit from Python
    to make sure the session flushes.
    """
    sql = "CALL upsert_contact(%s, %s, %s);"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (first_name, last_name, phone))
        conn.commit()

    print(f"\nupsert_contact('{first_name}', '{last_name}', '{phone}') done.")



# 4. Call bulk_insert_contacts() — PROCEDURE with array args

def bulk_insert(names: list, phones: list):
    """
    Passes two Python lists to the PostgreSQL procedure as arrays.

    psycopg2 automatically converts a Python list to a PostgreSQL array
    when the column/parameter type is an array type.

    After CALL, we SELECT from the temp table invalid_contacts to retrieve
    any rejected rows — the temp table lives for the duration of the session.
    """
    sql_call = "CALL bulk_insert_contacts(%s::VARCHAR[], %s::VARCHAR[]);"
    sql_invalid = "SELECT * FROM invalid_contacts;"

    with get_connection() as conn:
        with conn.cursor() as cur:
            # ::VARCHAR[] casts the Python list to a PostgreSQL VARCHAR array
            cur.execute(sql_call, (names, phones))
            conn.commit()

            # Now read back the invalid entries from the temp table
            # (same connection, same session → temp table still exists)
            cur.execute(sql_invalid)
            bad_rows = cur.fetchall()

    print(f"\nBulk insert done for {len(names)} entries.")
    if bad_rows:
        print("  Rejected (invalid phone):")
        for row in bad_rows:
            print(f"    name={row[0]}  phone={row[1]}")
    else:
        print("  All entries were valid.")



# 5. Call delete_contact() — PROCEDURE

def delete_contact(mode: str, value: str):
    """
    Calls the PostgreSQL procedure delete_contact(mode, value).

    mode  = 'name' or 'phone'
    value = the name or phone number to match
    """
    sql = "CALL delete_contact(%s, %s);"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (mode, value))
        conn.commit()

    print(f"\ndelete_contact(mode='{mode}', value='{value}') done.")



# 6. Interactive menu

def main():
    menu = """
╔══════════════════════════════════════════╗
║   PhoneBook — Functions & Procedures     ║
╠══════════════════════════════════════════╣
║  1. Search contacts (pattern)            ║
║  2. View contacts (paginated)            ║
║  3. Upsert contact (insert or update)    ║
║  4. Bulk insert contacts                 ║
║  5. Delete contact (by name or phone)    ║
║  0. Exit                                 ║
╚══════════════════════════════════════════╝
"""
    while True:
        print(menu)
        choice = input("Your choice: ").strip()

        if choice == '1':
            pat = input("Enter search pattern: ").strip()
            search_contacts(pat)

        elif choice == '2':
            try:
                limit  = int(input("Rows per page: ").strip())
                page   = int(input("Page number:   ").strip())
                offset = (page - 1) * limit
                get_page(limit, offset)
            except ValueError:
                print("Please enter numbers.")

        elif choice == '3':
            first = input("First name: ").strip()
            last  = input("Last name:  ").strip()
            phone = input("Phone:      ").strip()
            upsert_contact(first, last, phone)

        elif choice == '4':
            print("Enter contacts one per line as  name,phone")
            print("Leave a blank line when done.")
            names, phones = [], []
            while True:
                line = input("  > ").strip()
                if not line:
                    break
                parts = line.split(',')
                if len(parts) != 2:
                    print("  Format must be: name,phone")
                    continue
                names.append(parts[0].strip())
                phones.append(parts[1].strip())
            if names:
                bulk_insert(names, phones)

        elif choice == '5':
            mode  = input("Delete by (name/phone): ").strip().lower()
            value = input("Value: ").strip()
            delete_contact(mode, value)

        elif choice == '0':
            print("Goodbye!")
            break

        else:
            print("Unknown option.")


if __name__ == "__main__":
    main()
