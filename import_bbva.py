import pandas as pd
import psycopg2
from datetime import datetime
import yaml
import os

def load_keywords():
    with open('keywords.yaml', 'r') as file:
        return yaml.safe_load(file)

def infer_tag(description: str) -> str:
    keywords = load_keywords()
    description = description.lower()
    for category, category_keywords in keywords.items():
        if any(keyword in description for keyword in category_keywords):
            return category.capitalize()
    return "Other"

# Assuming df is your DataFrame
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Get list of CSV files in the "./data" directory
data_dir = "./data/bbva"
files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]

# Database connection parameters
params = {
    "dbname": "transactions",
    "user": "root",
    "password": "secret",
    "host": "localhost",
    "port": "5432"
}

# Connect to your PostgreSQL database
conn = psycopg2.connect(dbname=params['dbname'], user=params['user'], password=params['password'], host=params['host'], port=params['port'])
cursor = conn.cursor()

for file in files:
    df = pd.read_excel(os.path.join(data_dir, file), skiprows=[0, 1, 3])
    df['FECHA'] = pd.to_datetime(df['FECHA'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['FECHA'])
    df = df.dropna(subset=['CARGO'])
    df = df[df['CARGO'] >= 0]
    df = df.drop(columns=['ABONO', 'SALDO'])
    df.rename(columns={'DESCRIPCIÓN': 'description', 'CARGO': 'amount', 'FECHA': 'date'}, inplace=True)
    df['TAG'] = df['description'].apply(lambda x: infer_tag(x))
    # Insert data into the database
    for index, row in df.iterrows():
        fecha = row['date'].date()  # Assuming date is already a datetime object
        descripcion = row['description']
        importe = float(row['amount'])
        tag = row['TAG']
        # Check if a record with the same composite primary key exists
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE date = %s AND description = %s AND amount = %s", (fecha, descripcion, importe))
        count = cursor.fetchone()[0]
        if count == 0 and importe > 0.0:
            # Insert row into PostgreSQL database
            cursor.execute("""
            INSERT INTO transactions (date, description, amount, tag, card) 
            VALUES (%s, %s, %s, %s, 'bbva_credit') 
            ON CONFLICT (date, description, amount) 
            DO NOTHING;
            """, (fecha, descripcion, importe, tag))
            conn.commit()  # Commit the transaction
            print("Row inserted successfully!")

cursor.close()  # Close the cursor
conn.close()  # Close the connection
print("Database connection closed.")
