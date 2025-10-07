#!/usr/bin/env python3
"""
Dynamic Content Generator: Current Hedgehog Residents
Exports current hedgehog residents from database for HEDGEHOGS context hat
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Database path
DB_PATH = Path("/home/hedgehogs/hedgehog_care.db")

def get_current_residents():
    """Get list of current hedgehog residents with recent data"""
    if not DB_PATH.exists():
        return "⚠️ Hedgehog database not found at /home/hedgehogs/hedgehog_care.db"

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get current residents (those without leaving_date)
        cursor.execute("""
            SELECT name, admission_date, rescue_reason, other_notes
            FROM hedgehog_record
            WHERE leaving_date IS NULL
            ORDER BY admission_date DESC
        """)
        residents = cursor.fetchall()

        if not residents:
            return "No current residents in database."

        output = ["## Current Hedgehog Residents\n"]
        output.append(f"*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

        for resident in residents:
            name = resident['name']
            admission = resident['admission_date']
            rescue_reason = resident['rescue_reason'] or "Unknown"
            notes = resident['other_notes'] or ""

            output.append(f"### 🦔 {name}")
            output.append(f"- **Admitted**: {admission}")
            output.append(f"- **Rescue Reason**: {rescue_reason}")

            # Get most recent weight
            cursor.execute("""
                SELECT weight, date
                FROM hedgehog_daily
                WHERE hedgehog_name = ?
                ORDER BY date DESC
                LIMIT 1
            """, (name,))

            weight_row = cursor.fetchone()
            if weight_row:
                weight = weight_row['weight']
                measured = weight_row['date']
                output.append(f"- **Latest Weight**: {weight}g (recorded {measured})")

            # Get weight trend (last 7 days)
            cursor.execute("""
                SELECT weight, date
                FROM hedgehog_daily
                WHERE hedgehog_name = ?
                AND date >= date('now', '-7 days')
                ORDER BY date ASC
            """, (name,))

            weights = cursor.fetchall()
            if len(weights) >= 2:
                first_weight = weights[0]['weight']
                last_weight = weights[-1]['weight']
                if first_weight is not None and last_weight is not None:
                    change = last_weight - first_weight
                    trend = "+" if change > 0 else ""
                    output.append(f"- **7-Day Trend**: {trend}{change}g ({len(weights)} recordings)")

            # Check for recent medications
            cursor.execute("""
                SELECT date, medication_given
                FROM hedgehog_daily
                WHERE hedgehog_name = ?
                AND medication_given IS NOT NULL
                AND medication_given != ''
                AND date >= date('now', '-7 days')
                ORDER BY date DESC
            """, (name,))

            med_records = cursor.fetchall()
            if med_records:
                output.append(f"- **Recent Medications**: {len(med_records)} doses in past 7 days")

            if notes:
                output.append(f"- **Notes**: {notes}")

            output.append("")  # Blank line between residents

        conn.close()
        return "\n".join(output)

    except sqlite3.Error as e:
        return f"⚠️ Database error: {e}"
    except Exception as e:
        return f"⚠️ Error generating hedgehog status: {e}"

if __name__ == "__main__":
    print(get_current_residents())
