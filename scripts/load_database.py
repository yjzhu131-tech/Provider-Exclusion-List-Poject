import csv
from pathlib import Path

import psycopg


# This file is the "load" step.
#
# Step 1:
#   clean.py reads raw LEIE/Georgia files and creates cleaned CSV files.
#
# Step 2:
#   this file reads those cleaned CSV files and inserts them into PostgreSQL.
#
# This file does not clean raw data.
# It assumes data/cleaned already exists.

ROOT = Path(__file__).resolve().parent.parent
CLEANED_DATA_DIR = ROOT / "data" / "cleaned"

# PostgreSQL connection settings.
DB_HOST = "localhost"
DB_PORT = "5433"
DB_NAME = "exclusion_db"
DB_USER = "postgres"
DB_PASSWORD = r"\\\\"


def blank_to_none(value):
    """PostgreSQL should receive NULL instead of empty strings for missing values."""
    # In the cleaned CSV files, missing values are saved as empty strings.
    # Example:
    #   reinstatement_date = ""
    #
    # In PostgreSQL, missing values should be NULL, not "".
    # psycopg inserts Python None as SQL NULL.
    if value == "":
        return None
    return value


def read_cleaned_csv(file_name):
    """Read one cleaned CSV file and return its rows."""
    # Example:
    #   file_name = "data_source.csv"
    #   path = data/cleaned/data_source.csv
    path = CLEANED_DATA_DIR / file_name

    with path.open(newline="", encoding="utf-8") as file:
        # DictReader reads each CSV row as a dictionary.
        # Example row:
        #   {
        #     "data_source_id": "1",
        #     "source_name": "HHS OIG LEIE"
        #   }
        reader = csv.DictReader(file)

        # list(reader) loads all rows into memory.
        # This is okay for this project size.
        return list(reader)


def connect_to_database():
    """Open a connection to PostgreSQL."""
    # psycopg.connect creates the connection to the database you created in pgAdmin.
    # It does not insert anything yet.
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def insert_data_sources(cursor):
    """Load data_source.csv."""
    # data_source is a parent table.
    # Other tables point to it using data_source_id.
    rows = read_cleaned_csv("data_source.csv")

    # This counts how many rows were actually inserted.
    # Rows skipped by ON CONFLICT DO NOTHING are not counted.
    inserted = 0

    for row in rows:
        # cursor.execute sends one SQL command to PostgreSQL.
        #
        # OVERRIDING SYSTEM VALUE is needed because our table ID columns use
        # GENERATED ALWAYS AS IDENTITY. Normally PostgreSQL generates the ID.
        # But our cleaned CSV already contains data_source_id, so this tells
        # PostgreSQL: use the ID from the CSV.
        #
        # ON CONFLICT (data_source_id) DO NOTHING means:
        # if this data_source_id already exists, skip this row instead of erroring.
        # This helps when you run load_database.py more than once.
        cursor.execute(
            """
            INSERT INTO data_source (
                data_source_id, source_name, file_name, file_type, source_date
            )
            OVERRIDING SYSTEM VALUE
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (data_source_id) DO NOTHING
            """,
            (
                row["data_source_id"],
                row["source_name"],
                row["file_name"],
                row["file_type"],
                blank_to_none(row["source_date"]),
            ),
        )

        # rowcount is 1 if inserted, 0 if skipped by ON CONFLICT.
        inserted += cursor.rowcount

    return inserted


def insert_import_logs(cursor):
    """Load import_log.csv."""
    # import_log records the import event for each source file.
    # It points back to data_source through data_source_id.
    rows = read_cleaned_csv("import_log.csv")
    inserted = 0

    for row in rows:
        # data_source_id must already exist in data_source.
        # That is why insert_data_sources() runs before this function.
        cursor.execute(
            """
            INSERT INTO import_log (
                import_log_id, data_source_id, imported_at, status, records_loaded, notes
            )
            OVERRIDING SYSTEM VALUE
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (import_log_id) DO NOTHING
            """,
            (
                row["import_log_id"],
                row["data_source_id"],
                row["imported_at"],
                row["status"],
                row["records_loaded"],
                blank_to_none(row["notes"]),
            ),
        )
        inserted += cursor.rowcount

    return inserted


def insert_excluded_parties(cursor):
    """Load excluded_party.csv."""
    # excluded_party stores the people or entities on the exclusion lists.
    # Example individual:
    #   party_type = INDIVIDUAL, first_name/last_name filled
    #
    # Example entity:
    #   party_type = ENTITY, business_name filled
    rows = read_cleaned_csv("excluded_party.csv")
    inserted = 0

    for row in rows:
        # Some fields may be blank in the CSV.
        # blank_to_none() changes those blanks to PostgreSQL NULL.
        cursor.execute(
            """
            INSERT INTO excluded_party (
                party_id, party_type, first_name, middle_name, last_name,
                business_name, provider_category, specialty, dob, address,
                city, state, zip_code
            )
            OVERRIDING SYSTEM VALUE
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (party_id) DO NOTHING
            """,
            (
                row["party_id"],
                row["party_type"],
                blank_to_none(row["first_name"]),
                blank_to_none(row["middle_name"]),
                blank_to_none(row["last_name"]),
                blank_to_none(row["business_name"]),
                blank_to_none(row["provider_category"]),
                blank_to_none(row["specialty"]),
                blank_to_none(row["dob"]),
                blank_to_none(row["address"]),
                blank_to_none(row["city"]),
                blank_to_none(row["state"]),
                blank_to_none(row["zip_code"]),
            ),
        )
        inserted += cursor.rowcount

    return inserted


def insert_identifiers(cursor):
    """Load identifier.csv."""
    # identifier stores NPI and UPIN.
    #
    # This is a child table of excluded_party:
    # identifier.party_id must match an existing excluded_party.party_id.
    #
    # That is why insert_excluded_parties() runs before this function.
    rows = read_cleaned_csv("identifier.csv")
    inserted = 0

    for row in rows:
        # identifier.csv only contains real identifiers.
        # Missing NPIs and fake LEIE value 0000000000 were removed in clean.py.
        cursor.execute(
            """
            INSERT INTO identifier (
                identifier_id, party_id, identifier_type, identifier_value
            )
            OVERRIDING SYSTEM VALUE
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (identifier_id) DO NOTHING
            """,
            (
                row["identifier_id"],
                row["party_id"],
                row["identifier_type"],
                row["identifier_value"],
            ),
        )
        inserted += cursor.rowcount

    return inserted


def insert_exclusion_records(cursor):
    """Load exclusion_record.csv."""
    # exclusion_record stores the actual exclusion event:
    #   who was excluded?
    #   from which source file?
    #   when did the exclusion start?
    #   what is the EXCLTYPE code, if available?
    #
    # This table has three foreign keys:
    #   party_id -> excluded_party
    #   data_source_id -> data_source
    #   import_log_id -> import_log
    #
    # So excluded_party, data_source, and import_log must be loaded first.
    rows = read_cleaned_csv("exclusion_record.csv")
    inserted = 0

    for row in rows:
        # Georgia rows do not have exclusion_type, reinstatement_date,
        # waiver_date, or waiver_state. Those blank values become NULL here.
        cursor.execute(
            """
            INSERT INTO exclusion_record (
                exclusion_record_id, party_id, data_source_id, import_log_id,
                exclusion_type, exclusion_date, reinstatement_date, waiver_date,
                waiver_state, status
            )
            OVERRIDING SYSTEM VALUE
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (exclusion_record_id) DO NOTHING
            """,
            (
                row["exclusion_record_id"],
                row["party_id"],
                row["data_source_id"],
                row["import_log_id"],
                blank_to_none(row["exclusion_type"]),
                row["exclusion_date"],
                blank_to_none(row["reinstatement_date"]),
                blank_to_none(row["waiver_date"]),
                blank_to_none(row["waiver_state"]),
                row["status"],
            ),
        )
        inserted += cursor.rowcount

    return inserted


def main():
    # First connect to PostgreSQL.
    connection = connect_to_database()

    # Load parent tables first, then child tables.
    # This order matters because of foreign keys.
    #
    # This script does NOT truncate/delete old data.
    # If a row with the same primary key already exists,
    # ON CONFLICT DO NOTHING skips it.
    with connection:
        # A cursor is the object used to send SQL commands.
        with connection.cursor() as cursor:
            # 1. data_source first because import_log and exclusion_record use it.
            data_source_count = insert_data_sources(cursor)

            # 2. import_log second because exclusion_record uses import_log_id.
            import_log_count = insert_import_logs(cursor)

            # 3. excluded_party third because identifier and exclusion_record use party_id.
            party_count = insert_excluded_parties(cursor)

            # 4. identifier after excluded_party.
            identifier_count = insert_identifiers(cursor)

            # 5. exclusion_record last because it depends on three parent tables.
            exclusion_count = insert_exclusion_records(cursor)

    # After the with connection block finishes successfully,
    # psycopg commits the transaction.
    # If there is an error, it rolls back automatically.
    print("New cleaned CSV rows loaded into PostgreSQL")
    print(f"new data_source rows inserted: {data_source_count}")
    print(f"new import_log rows inserted: {import_log_count}")
    print(f"new excluded_party rows inserted: {party_count}")
    print(f"new identifier rows inserted: {identifier_count}")
    print(f"new exclusion_record rows inserted: {exclusion_count}")


if __name__ == "__main__":
    main()
