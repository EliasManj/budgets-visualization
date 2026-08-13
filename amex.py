import os
import csv
import sqlite3
from datetime import datetime
import utils


def import_amex():
    # Connect to SQLite database
    conn = sqlite3.connect('db/database.db')

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Get list of CSV files in the "./data" directory
    data_dir = "./data/amex"
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

    data = utils.load_keywords()

    # Process each CSV file
    for csv_file in csv_files:
        with open(os.path.join(data_dir, csv_file), newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                # Parse date from string to Python date object
                fecha = datetime.strptime(row['Fecha'], '%d %b %Y').date()
                descripcion = row['Descripción']
                descripcion = ' '.join(descripcion.split())
                importe = float(row['Importe'])
                tag = utils.infer_tag(data, descripcion)
                utils.insert_transaction(cursor, conn, fecha, descripcion, importe, tag, 'amex')

    # Commit changes to the database
    conn.commit()

    # Close the cursor and database connection
    cursor.close()
    conn.close()

if __name__ == "__main__":
    import_amex()