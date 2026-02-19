from waittime.services.database import DatabaseService


def inspect_schema():
    db = DatabaseService()
    print(f"Connecting to: {db.database_url.split('@')[1] if '@' in db.database_url else 'LOCAL'}")

    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'measurements';
            """
            )
            columns = cur.fetchall()
            print("Columns in 'measurements':")
            for col in columns:
                print(f" - {col[0]} ({col[1]})")


if __name__ == "__main__":
    inspect_schema()
