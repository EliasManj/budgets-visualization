import pandas as pd
import os
import sqlite3
import utils

def import_bbva_debit():
    # Get list of CSV files in the "./data" directory
    data_dir = "./data/bbva_debit"
    files = [f for f in os.listdir(data_dir) if f.endswith(".xlsx")]

    print("Connecting to SQLite database...")
    # Connect to SQLite database
    conn = sqlite3.connect("db/database.db")
    print("Connection successful.")
    cursor = conn.cursor()
    data = utils.load_keywords()

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
        df["TAG"] = df["description"].apply(lambda x: utils.infer_tag(data, x))
        df["description"] = df["description"].str.lower()
        df['description'] = df['description'].apply(lambda x: ' '.join(x.split()))
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



def import_bbva_credit():
    # Assuming df is your DataFrame
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)

    # Get list of CSV files in the "./data" directory
    data_dir = "./data/bbva"
    files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]

    # Connect to SQLite database
    conn = sqlite3.connect('db/database.db')
    cursor = conn.cursor()

    data = utils.load_keywords()

    for file in files:
        df = pd.read_excel(os.path.join(data_dir, file), skiprows=[0, 1, 3])
        df['FECHA'] = pd.to_datetime(df['FECHA'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['FECHA'])
        df = df.dropna(subset=['CARGO'])
        df = df[df['CARGO'] >= 0]
        df = df.drop(columns=['ABONO', 'SALDO'])
        df.rename(columns={'DESCRIPCIÓN': 'description', 'CARGO': 'amount', 'FECHA': 'date'}, inplace=True)
        df['TAG'] = df['description'].apply(lambda x: utils.infer_tag(data, x))
        # Insert data into the database
        for index, row in df.iterrows():
            fecha = row['date'].date()  # Assuming date is already a datetime object
            descripcion = row['description']
            descripcion = ' '.join(descripcion.split())
            importe = float(row['amount'])
            tag = row['TAG']
            # Check if a record with the same composite primary key exists
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE date = ? AND description = ? AND amount = ?", (fecha, descripcion, importe))
            count = cursor.fetchone()[0]
            if count == 0 and importe > 0.0:
                # Insert row into PostgreSQL database
                cursor.execute("""
                INSERT INTO transactions (date, description, amount, tag, card) 
                VALUES (?, ?, ?, ?, 'bbva_credit') 
                ON CONFLICT (date, description, amount) 
                DO NOTHING;
                """, (fecha, descripcion, importe, tag))
                conn.commit()  # Commit the transaction

    cursor.close()  # Close the cursor
    conn.close()  # Close the connection
    print("Database connection closed.")

if __name__ == "__main__":
    import_bbva_credit()
    import_bbva_debit()