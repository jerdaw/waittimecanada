import json
import os
import sys
from datetime import datetime

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection() -> connection:
    if not DATABASE_URL:
        print("Error: DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(DATABASE_URL)


def get_last_scrape_time() -> datetime | None:
    """Get the timestamp of the most recent heartbeat."""
    # Annotate conn explicitly if needed, but return annotation covers it
    conn: connection = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT last_run
                FROM scraper_status
                ORDER BY last_run DESC
                LIMIT 1
            """
            )
            result = cur.fetchone()
            if result and result["last_run"]:
                return result["last_run"]
            return None
    except Exception as e:
        print(f"Error querying database: {e}")
        return None
    finally:
        conn.close()


def format_time_ago(dt: datetime) -> str:
    """Format a datetime as a 'time ago' string."""
    now = datetime.now(dt.tzinfo)
    diff = now - dt

    seconds = diff.total_seconds()
    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = int(hours // 24)

    if minutes < 1:
        return "just now"
    elif minutes < 60:
        return f"{minutes}m ago"
    elif hours < 24:
        return f"{hours}h ago"
    else:
        return f"{days}d ago"


def get_color(dt: datetime) -> str:
    """Determine badge color based on freshness."""
    now = datetime.now(dt.tzinfo)
    diff = now - dt
    minutes = int(diff.total_seconds() // 60)

    if minutes < 60:
        return "brightgreen"
    elif minutes < 120:
        return "yellow"
    else:
        return "red"


def main() -> None:
    last_run = get_last_scrape_time()

    if last_run:
        message = format_time_ago(last_run)
        color = get_color(last_run)
    else:
        message = "unknown"
        color = "lightgrey"

    badge_data = {"schemaVersion": 1, "label": "Last Scrape", "message": message, "color": color}

    # Check if passing output file argument
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
        with open(output_file, "w") as f:
            json.dump(badge_data, f)
        print(f"Badge data written to {output_file}")
    else:
        print(json.dumps(badge_data, indent=2))


if __name__ == "__main__":
    main()
