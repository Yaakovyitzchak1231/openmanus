import argparse
import os
import sqlite3


def list_feedback(db_path="feedback.db"):
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM feedback ORDER BY timestamp DESC")
        rows = cursor.fetchall()

        if not rows:
            print("No feedback entries found.")
        else:
            print(f"{'ID':<4} | {'Timestamp':<25} | {'Agent':<15} | {'Feedback'}")
            print("-" * 80)
            for row in rows:
                # id, ts, step, agent, feedback, success
                print(f"{row[0]:<4} | {row[1]:<25} | {row[3]:<15} | {row[4][:50]}...")

        conn.close()
    except Exception as e:
        print(f"Error reading database: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query HITL Feedback Database")
    parser.add_argument("--view", action="store_true", help="View all feedback entries")
    args = parser.parse_args()

    if args.view:
        list_feedback()
    else:
        parser.print_help()
