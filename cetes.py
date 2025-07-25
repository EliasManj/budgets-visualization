import sqlite3
import re
from datetime import datetime
import os

def get_month_year(filename):
    filename = os.path.basename(filename)
    if filename.endswith(".txt"):
        base = filename[:-4] 
    else:
        base = filename
    month, year = base.split("-")
    return month, year

def process_file(file):
    print(f"Processing file: {file}")

    # Read raw data cetes a file
    with open(file, "r", encoding="utf-8") as file:
        raw_data = file.read()

    month, year = get_month_year(file.name)
    # Convert to datetime object, using the first day of the month
    date_obj = datetime.strptime(f"{month} {year}", "%b %Y").date()
    date_str = date_obj.isoformat() 
    lines = [line.strip() for line in raw_data.strip().splitlines()]
    records = []

    i = 0
    while i < len(lines):
        # Check if a valid block starts here (e.g., BONDDIA, CETES, TOTAL, etc.)
        if re.match(r'^[A-Z]+$', lines[i]) or lines[i] == 'TOTAL':
            try:
                instrumento = lines[i]
                percentage = lines[i + 1]
                raw_values_line = lines[i + 2].replace("\\t", "\t").replace("  ", "\t").replace("\t\t", "\t")
                values = raw_values_line.strip().split("\t")
                values1 = [float(x.replace(",", "")) for x in values if x.strip()]
                valuado = float(lines[i + 3].replace(",", ""))
                # Skip 'títulos' line and advance pointer
                i += 5
                invertido, plusminus, disp = values1
                records.append((date_obj, instrumento, invertido, plusminus, disp, valuado))
            except Exception as e:
                print(f"Skipping block starting at line {i}: {e}")
                i += 1
        else:
            i += 1
    return records

def insert_records(records):
    # Create SQLite DB and table
    conn = sqlite3.connect("db/database.db")
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cetes (
        date TEXT,
        instrumento TEXT,
        invertido REAL,
        plusminus REAL,
        disp REAL,
        valuado REAL,
        PRIMARY KEY (date, instrumento)
    )
    """)

    # Insert records
    cursor.executemany("""
    INSERT OR REPLACE INTO cetes (date, instrumento, invertido, plusminus, disp, valuado)
    VALUES (?, ?, ?, ?, ?, ?)
    """, records)

    conn.commit()
    conn.close()

    # Output result
    for r in records:
        print(r)

def import_cetes():
    data_dir = "./data/cetes"
    txt_files = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
    for file in txt_files:
        records = process_file(os.path.join(data_dir, file))
        insert_records(records)

if __name__ == "__main__":
    import_cetes()
