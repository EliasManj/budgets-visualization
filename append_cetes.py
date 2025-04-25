import sqlite3
import re
from datetime import datetime

raw_data = """
BONDDIA
8.85%
21,798.76\t556.95\t21,798.76\t
21,798.76
10,094 títulos
CETES
9.39%
84,150.07\t1,781.44\t86,034.48\t
85,931.49
8,712 títulos
ENERFIN
9.85%
72,944.94\t5,413.80\t78,358.75\t
78,358.75
4,057 títulos
REMANENTES
1.59
DEPÓSITOS DEL DÍA
0.00
TOTAL
9.52%
178,894.77\t7,752.20\t186,193.58\t
186,090.59
22,864 títulos
"""

# Current date
today_str = datetime.today().strftime("%Y-%m-%d")

lines = [line.strip() for line in raw_data.strip().splitlines()]
records = []

i = 0
while i < len(lines):
    # Check if a valid block starts here (e.g., BONDDIA, CETES, TOTAL, etc.)
    if re.match(r'^[A-Z]+$', lines[i]) or lines[i] == 'TOTAL':
        try:
            instrumento = lines[i]
            percentage = lines[i + 1]
            values1 = [float(x.replace(",", "")) for x in lines[i + 2].split()]
            valuado = float(lines[i + 3].replace(",", ""))
            # Skip 'títulos' line and advance pointer
            i += 5
            invertido, plusminus, disp = values1
            records.append((today_str, instrumento, invertido, plusminus, disp, valuado))
        except Exception as e:
            print(f"Skipping block starting at line {i}: {e}")
            i += 1
    else:
        i += 1

# Create SQLite DB and table
conn = sqlite3.connect("db/database.db")
cursor = conn.cursor()

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
