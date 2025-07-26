import os
import csv
import sqlite3
from datetime import datetime
import re
import yaml
import utils


def import_amex():
    print("Connecting to SQLite database...")
    # Connect to SQLite database
    conn = sqlite3.connect('db/database.db')
    print("Connection successful.")

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Get list of CSV files in the "./data" directory
    data_dir = "./data/amex"
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

    data = utils.load_keywords()

    # Process each CSV file
    for csv_file in csv_files:
        print(f"Processing CSV file: {csv_file}")
        if "2025" in csv_file:
            print()
        with open(os.path.join(data_dir, csv_file), newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            print(f"Fieldnames in CSV: {reader.fieldnames}")
            for row in reader:
                # Parse date from string to Python date object
                fecha = datetime.strptime(row['Fecha'], '%d %b %Y').date()
                descripcion = row['Descripción']
                descripcion = ' '.join(descripcion.split())
                importe = float(row['Importe'])
                tag = utils.infer_tag(data, descripcion)

                # Check if a record with the same composite primary key exists
                cursor.execute("SELECT COUNT(*) FROM transactions WHERE date = ? AND description = ? AND amount = ?", (fecha, descripcion, importe))
                count = cursor.fetchone()[0]

                if count == 0 and importe > 0.0:
                    # Insert row into database
                    cursor.execute("""
                    INSERT INTO transactions (date, description, amount, tag, card) 
                    VALUES (?, ?, ?, ?, 'amex') 
                    ON CONFLICT (date, description, amount) 
                    DO NOTHING;
                    """, (fecha, descripcion, importe, tag))

    # Commit changes to the database
    conn.commit()
    print("Changes committed to the database.")

    # Close the cursor and database connection
    cursor.close()
    conn.close()
    print("Database connection closed.")

if __name__ == "__main__":
    import_amex()