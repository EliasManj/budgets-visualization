import sqlite3
import yaml
import re

def load_keywords():
    with open("keywords.yaml", "r") as file:
        keywords = yaml.safe_load(file)
        return keywords

def infer_tag(data, description):
    description = description.lower()
    description = ' '.join(description.split())
    if "0087608020" in description:
        print("a")
    # Iterate through each category and its keywords/regex
    for category, patterns in data.items():
        for pattern in patterns:
            # Check for match using regex (case-insensitive)
            if re.search(pattern, description, re.IGNORECASE):
                return category.capitalize()
    return "Other"


def insert_transaction(cursor, conn, fecha, descripcion, importe, tag, card):
    if importe <= 0.0:
        return
    cursor.execute(
        "SELECT COUNT(*) FROM transactions WHERE date = ? AND description = ? AND amount = ?",
        (fecha, descripcion, importe),
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO transactions (date, description, amount, tag, card) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT (date, description, amount) DO NOTHING;",
            (fecha, descripcion, importe, tag, card),
        )
        conn.commit()


def insert_import(cursor, conn, fecha, importe):
    if importe <= 0.0:
        return
    cursor.execute(
        "SELECT COUNT(*) FROM imports WHERE date = ? AND amount = ?",
        (fecha, importe),
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO imports (date, amount) VALUES (?, ?) "
            "ON CONFLICT (date, amount) DO NOTHING;",
            (fecha, importe),
        )
        conn.commit()
