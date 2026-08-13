import os
import csv
import sqlite3
from datetime import datetime
import utils

months = {
    "Ene": "Jan", "Feb": "Feb", "Mar": "Mar", "Abr": "Apr",
    "May": "May", "Jun": "Jun", "Jul": "Jul", "Ago": "Aug",
    "Sep": "Sep", "Oct": "Oct", "Nov": "Nov", "Dic": "Dec"
}

def parse_amount(value):
    value = value.replace("$", "").replace(" ", "").replace(",", "")
    return float(value) if value else 0.0

def import_banamex_credit():

    conn = sqlite3.connect('db/database.db')

    cursor = conn.cursor()

    data_dir = "./data/banamex_credit"
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

    data = utils.load_keywords()

    for csv_file in csv_files:
        print(f"Processing CSV file: {csv_file}")
        with open(os.path.join(data_dir, csv_file), newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                date_str = row['Fecha']
                for es, en in months.items():
                    date_str = date_str.replace(es, en)
                fecha = datetime.strptime(date_str, '%d %b %Y').date()
                descripcion = row['Descripción']
                descripcion = ' '.join(descripcion.split())
                retiro_str = row.get('Compras', '').strip()
                if retiro_str:
                    importe = parse_amount(retiro_str)
                    if importe > 0.0:
                        tag = utils.infer_tag(data, descripcion)
                        utils.insert_transaction(cursor, conn, fecha, descripcion, importe, tag, 'banamex_credit')

    conn.commit()

    cursor.close()
    conn.close()

def import_banamex_debit():

    conn = sqlite3.connect('db/database.db')

    cursor = conn.cursor()

    data_dir = "./data/banamex"
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

    data = utils.load_keywords()

    for csv_file in csv_files:
        print(f"Processing CSV file: {csv_file}")
        with open(os.path.join(data_dir, csv_file), newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                date_str = row['Fecha']
                for es, en in months.items():
                    date_str = date_str.replace(es, en)
                fecha = datetime.strptime(date_str, '%d %b %Y').date()
                descripcion = row['Descripción']
                descripcion = ' '.join(descripcion.split())
                deposito_str = row.get('Depósitos', '').strip()
                retiro_str = row.get('Retiros', '').strip()

                if deposito_str:
                    importe = parse_amount(deposito_str)
                    utils.insert_import(cursor, conn, fecha, importe)

                if retiro_str:
                    importe = parse_amount(retiro_str)
                    if importe > 0.0:
                        tag = utils.infer_tag(data, descripcion)
                        if tag.lower() != "ignore":
                            utils.insert_transaction(cursor, conn, fecha, descripcion, importe, tag, 'banamex_debit')

    conn.commit()

    cursor.close()
    conn.close()

if __name__ == "__main__":
    import_banamex_debit()
    import_banamex_credit()