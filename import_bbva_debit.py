import pandas as pd
import psycopg2
from datetime import datetime
import yaml
import os
import re
import sqlite3

pattern = r"(spei\senviado\s\w+)\s+\/\s+\w+\s+(\d+)\s+\d+([\w-]+)"


def load_keywords():
    with open("keywords.yaml", "r") as file:
        keywords = yaml.safe_load(file)
        return keywords


def process_transfer(s):
    match = re.search(pattern, s)
    if match:
        return f"{match.group(1)} / {match.group(2)} / {match.group(3)}"
    else:
        return None


def infer_tag(keywords, description):
    description = description.lower()
    if "0051752472" in description:
        print("a")
    transferencia = process_transfer(description)
    if transferencia:
        for category, category_keywords in keywords.items():
            if (
                category.lower() == "investments"
                or category.lower() == "rent"
                or category.lower() == "cetes"
                or category.lower() == "gym"
            ):
                match = process_transfer(description)
                if match:
                    keyword_pairs = list(map(lambda x: x.split("/"), category_keywords))
                    keyword_pairs = [pair for pair in keyword_pairs if len(pair) > 2]
                    if any(
                        keyword_pair[0].lower() in match
                        and keyword_pair[1].lower()
                        and keyword_pair[2].lower() in match
                        for keyword_pair in keyword_pairs
                    ):
                        return category.capitalize()
    for category, category_keywords in keywords.items():
        if any(keyword.lower() in description for keyword in category_keywords):
            return category.capitalize()
    return "Other"


# Assuming df is your DataFrame
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)

# Get list of CSV files in the "./data" directory
data_dir = "./data/bbva_debit"
files = [f for f in os.listdir(data_dir) if f.endswith(".xlsx")]

print("Connecting to SQLite database...")
# Connect to SQLite database
conn = sqlite3.connect("db/database.db")
print("Connection successful.")
cursor = conn.cursor()

# load keywords
keywords = load_keywords()

for file in files:
    df = pd.read_excel(os.path.join(data_dir, file), skiprows=[0, 1, 2])
    df["FECHA"] = pd.to_datetime(df["FECHA"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["FECHA"])
    abonos_df = df[df["ABONO"].notna()]
    abonos_df = abonos_df.drop(columns=["CARGO", "SALDO", "DESCRIPCIÓN"])
    df = df.dropna(subset=["CARGO"])
    df = df.drop(columns=["ABONO", "SALDO"])
    df.rename(
        columns={"DESCRIPCIÓN": "description", "CARGO": "amount", "FECHA": "date"},
        inplace=True,
    )
    abonos_df.rename(columns={"ABONO": "amount", "FECHA": "date"}, inplace=True)
    df["TAG"] = df["description"].apply(lambda x: infer_tag(keywords, x))
    df = df[df["TAG"] != "Ignore"]
    df["amount"] = df["amount"].str.replace(",", "").astype(float).abs()
    abonos_df["amount"] = abonos_df["amount"].astype(str)
    abonos_df["amount"] = abonos_df["amount"].str.replace(",", "").astype(float).abs()
    for index, row in abonos_df.iterrows():
        fecha = row["date"].date()
        importe = row["amount"]
        cursor.execute(
            "SELECT COUNT(*) FROM imports WHERE date = ? AND amount = ?",
            (fecha, importe),
        )
        count = cursor.fetchone()[0]
        if count == 0 and importe > 0.0:
            # Insert row into PostgreSQL database
            cursor.execute(
                """
            INSERT INTO imports (date, amount) 
            VALUES (?, ?) 
            ON CONFLICT (date, amount) 
            DO NOTHING;
            """,
                (fecha, importe),
            )
            conn.commit()  # Commit the transaction
    # Insert data into the database
    for index, row in df.iterrows():
        fecha = row["date"].date()  # Assuming date is already a datetime object
        descripcion = row["description"]
        descripcion = re.sub(r"\s+", "-", descripcion)
        importe = row["amount"]
        tag = row["TAG"]
        # Check if a record with the same composite primary key exists
        cursor.execute(
            "SELECT COUNT(*) FROM transactions WHERE date = ? AND description = ? AND amount = ?",
            (fecha, descripcion, importe),
        )
        count = cursor.fetchone()[0]
        if count == 0 and importe > 0.0:
            # Insert row into PostgreSQL database
            cursor.execute(
                """
            INSERT INTO transactions (date, description, amount, tag, card) 
            VALUES (?, ?, ?, ?, 'bbva_debit') 
            ON CONFLICT (date, description, amount) 
            DO NOTHING;
            """,
                (fecha, descripcion, importe, tag),
            )
            conn.commit()  # Commit the transaction

cursor.close()  # Close the cursor
conn.close()  # Close the connection
print("Database connection closed.")
