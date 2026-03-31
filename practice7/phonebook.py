
import csv
import psycopg2
from connect import get_connection


# 1. TABLE SETUP


def create_table():
    """
    Creates the phonebook table if it does not already exist.

    Schema explanation:
      id         — auto-incrementing primary key (SERIAL handles this)
      first_name — required; NOT NULL means the field cannot be empty
      last_name  — optional contact surname
      phone      — required AND unique; no two contacts share a number
      created_at — timestamp filled automatically when the row is inserted
    """
    sql = """
        CREATE TABLE IF NOT EXISTS phonebook (
            id         SERIAL PRIMARY KEY,
            first_name VARCHAR(50)  NOT NULL,
            last_name  VARCHAR(50),
            phone      VARCHAR(20)  NOT NULL UNIQUE,
            created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
        );
    """
    # 'with' ensures the connection is closed even if an error occurs
    with get_connection() as conn:
        # A cursor is how we send SQL commands to the database
        with conn.cursor() as cur:
            cur.execute(sql)
        # conn.commit() permanently saves the change.
        # Without it, the table would not actually be created.
        conn.commit()
    print("Table 'phonebook' is ready.")



# 2. INSERT FROM CSV


def insert_from_csv(filepath: str):
    """
    Reads a CSV file and inserts every row into the phonebook.

    The CSV must have columns: first_name, last_name, phone

    ON CONFLICT (phone) DO NOTHING means:
      If a phone number already exists in the table, skip that row
      instead of crashing with a duplicate-key error.
    This makes the import safe to run multiple times.
    """
    sql = """
        INSERT INTO phonebook (first_name, last_name, phone)
        VALUES (%s, %s, %s)
        ON CONFLICT (phone) DO NOTHING;
    """
    inserted = 0
    skipped  = 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Open the CSV with utf-8 encoding to handle special characters
            with open(filepath, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)  # reads header row automatically
                for row in reader:
                    cur.execute(sql, (
                        row['first_name'].strip(),
                        row['last_name'].strip(),
                        row['phone'].strip()
                    ))
                    # rowcount tells us how many rows were actually inserted
                    if cur.rowcount == 1:
                        inserted += 1
                    else:
                        skipped += 1
        conn.commit()

    print(f"CSV import done — inserted: {inserted}, skipped (duplicate): {skipped}")



# 3. INSERT FROM CONSOLE


def insert_from_console():
    """
    Asks the user to type a contact's details and saves it to the DB.

    %s placeholders are used instead of string formatting (f-strings) for
    security: psycopg2 escapes the values automatically, preventing
    SQL injection attacks.
    """
    print("\n--- Add a new contact ---")
    first = input("First name: ").strip()
    last  = input("Last name (leave blank to skip): ").strip()
    phone = input("Phone number: ").strip()

    if not first or not phone:
        print("First name and phone are required.")
        return

    sql = """
        INSERT INTO phonebook (first_name, last_name, phone)
        VALUES (%s, %s, %s)
        ON CONFLICT (phone) DO NOTHING;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (first, last or None, phone))
            if cur.rowcount == 1:
                print(f"Contact '{first} {last}' added.")
            else:
                print(f"Phone {phone} already exists. Contact not added.")
        conn.commit()



# 4. UPDATE


def update_contact():
    """
    Lets the user update either the first name or phone number
    of an existing contact identified by their current phone.

    The WHERE clause targets the exact row by phone number.
    %s placeholders keep the query safe from injection.
    """
    print("\n--- Update a contact ---")
    old_phone = input("Enter the phone number of the contact to update: ").strip()

    print("What would you like to update?")
    print("  1. First name")
    print("  2. Phone number")
    choice = input("Choice (1/2): ").strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            if choice == '1':
                new_name = input("New first name: ").strip()
                if not new_name:
                    print("Name cannot be empty.")
                    return
                cur.execute(
                    "UPDATE phonebook SET first_name = %s WHERE phone = %s;",
                    (new_name, old_phone)
                )
            elif choice == '2':
                new_phone = input("New phone number: ").strip()
                if not new_phone:
                    print("Phone cannot be empty.")
                    return
                cur.execute(
                    "UPDATE phonebook SET phone = %s WHERE phone = %s;",
                    (new_phone, old_phone)
                )
            else:
                print("Invalid choice.")
                return

            # rowcount == 0 means no row matched the WHERE clause
            if cur.rowcount == 0:
                print(f"No contact found with phone {old_phone}.")
            else:
                print("Contact updated successfully.")
        conn.commit()



# 5. QUERY / SEARCH


def query_contacts():
    """
    Offers three filter modes:
      A — show all contacts (no WHERE clause)
      B — filter by first name (case-insensitive with ILIKE)
      C — filter by phone prefix (LIKE '1234%' matches any number starting with that prefix)

    ILIKE is PostgreSQL's case-insensitive version of LIKE.
    The % wildcard means "anything can follow here".
    """
    print("\n--- Query contacts ---")
    print("  1. Show all contacts")
    print("  2. Search by first name")
    print("  3. Search by phone prefix")
    choice = input("Choice (1/2/3): ").strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            if choice == '1':
                cur.execute(
                    "SELECT id, first_name, last_name, phone, created_at FROM phonebook ORDER BY id;"
                )
            elif choice == '2':
                name = input("Enter first name (or part of it): ").strip()
                # ILIKE '%alice%' matches Alice, ALICE, alice, etc.
                cur.execute(
                    "SELECT id, first_name, last_name, phone, created_at "
                    "FROM phonebook WHERE first_name ILIKE %s ORDER BY first_name;",
                    (f"%{name}%",)
                )
            elif choice == '3':
                prefix = input("Enter phone prefix: ").strip()
                cur.execute(
                    "SELECT id, first_name, last_name, phone, created_at "
                    "FROM phonebook WHERE phone LIKE %s ORDER BY phone;",
                    (f"{prefix}%",)
                )
            else:
                print("Invalid choice.")
                return

            rows = cur.fetchall()  # retrieves all result rows as a list of tuples

    if not rows:
        print("No contacts found.")
    else:
        print(f"\n{'ID':<5} {'First':<15} {'Last':<15} {'Phone':<20} {'Added'}")
        print("-" * 75)
        for row in rows:
            rid, first, last, phone, created = row
            print(f"{rid:<5} {first:<15} {last or '':<15} {phone:<20} {created:%Y-%m-%d %H:%M}")


# 6. DELETE


def delete_contact():
    """
    Deletes a contact identified by either username (first name) or phone.

    Deleting by first name may affect multiple rows if names are not unique,
    so the user is warned and asked to confirm.
    """
    print("\n--- Delete a contact ---")
    print("  1. Delete by first name")
    print("  2. Delete by phone number")
    choice = input("Choice (1/2): ").strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            if choice == '1':
                name = input("First name to delete: ").strip()
                # Show matching rows before deleting so user can confirm
                cur.execute(
                    "SELECT id, first_name, last_name, phone FROM phonebook WHERE first_name ILIKE %s;",
                    (name,)
                )
                matches = cur.fetchall()
                if not matches:
                    print(f"No contacts named '{name}'.")
                    return
                print(f"Found {len(matches)} contact(s):")
                for r in matches:
                    print(f"  ID={r[0]}  {r[1]} {r[2]}  {r[3]}")
                confirm = input("Delete all of these? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("Deletion cancelled.")
                    return
                cur.execute(
                    "DELETE FROM phonebook WHERE first_name ILIKE %s;",
                    (name,)
                )
                print(f"Deleted {cur.rowcount} contact(s).")

            elif choice == '2':
                phone = input("Phone number to delete: ").strip()
                cur.execute(
                    "DELETE FROM phonebook WHERE phone = %s;",
                    (phone,)
                )
                if cur.rowcount == 0:
                    print(f"No contact with phone {phone}.")
                else:
                    print(f"Contact with phone {phone} deleted.")
            else:
                print("Invalid choice.")
                return
        conn.commit()



# 7. MAIN MENU


def main():
    """
    Entry point. Creates the table once, then runs an infinite loop
    showing a menu until the user chooses to quit.
    """
    create_table()

    menu = """
╔══════════════════════════════╗
║      PhoneBook Menu          ║
╠══════════════════════════════╣
║  1. Import contacts from CSV ║
║  2. Add contact (console)    ║
║  3. Update a contact         ║
║  4. Search / Query contacts  ║
║  5. Delete a contact         ║
║  0. Exit                     ║
╚══════════════════════════════╝
"""
    while True:
        print(menu)
        choice = input("Your choice: ").strip()

        if choice == '1':
            path = input("CSV file path [contacts.csv]: ").strip() or "contacts.csv"
            insert_from_csv(path)
        elif choice == '2':
            insert_from_console()
        elif choice == '3':
            update_contact()
        elif choice == '4':
            query_contacts()
        elif choice == '5':
            delete_contact()
        elif choice == '0':
            print("Goodbye!")
            break
        else:
            print("Unknown option, please try again.")


if __name__ == "__main__":
    main()
