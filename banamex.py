import os
import csv
import sqlite3
from datetime import datetime
import re
import yaml
import utils

def parse_amount(value):
    value = value.replace("$", "").replace(" ", "").replace(",", "")
    return float(value) if value else 0.0

def import_banamex():

    print("Connecting to SQLite database...")
    conn = sqlite3.connect('db/database.db')
    print("Connection successful.")

    cursor = conn.cursor()

    data_dir = "./data/banamex"
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

    data = utils.load_keywords()

    for csv_file in csv_files:
        print(f"Processing CSV file: {csv_file}")
        with open(os.path.join(data_dir, csv_file), newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                fecha = datetime.strptime(row['Fecha'], '%d %b %Y').date()
                descripcion = row['Descripción']
                descripcion = ' '.join(descripcion.split())
                deposito_str = row.get('Depósitos', '').strip()
                retiro_str = row.get('Retiros', '').strip()

                if deposito_str:
                    importe = parse_amount(deposito_str)
                    if importe > 0.0:
                        cursor.execute("""
                            INSERT INTO imports (date, amount) 
                            VALUES (?, ?) 
                            ON CONFLICT (date, amount) 
                            DO NOTHING;
                        """, (fecha, importe))

                if retiro_str:
                    importe = parse_amount(retiro_str)
                    if importe > 0.0:
                        tag = utils.infer_tag(data, descripcion)
                        cursor.execute("""
                            INSERT INTO transactions (date, description, amount, tag, card) 
                            VALUES (?, ?, ?, ?, 'banamex') 
                            ON CONFLICT (date, description, amount) 
                            DO NOTHING;
                        """, (fecha, descripcion, importe, tag))

    conn.commit()
    print("Changes committed to the database.")

    cursor.close()
    conn.close()
    print("Database connection closed.")

if __name__ == "__main__":
    import_banamex()