import os
import csv
import psycopg2
from datetime import datetime
import re
import yaml

def load_keywords():
    with open('keywords.yaml', 'r') as file:
        return yaml.safe_load(file)

def infer_tag(description: str) -> str:
    keywords = load_keywords()
    description = descripcion.lower()
    for category, category_keywords in keywords.items():
        if any(keyword in description for keyword in category_keywords):
            return category.capitalize()
    return "Other"

print("Connecting to PostgreSQL database...")
# Connect to PostgreSQL database
conn = psycopg2.connect(
    dbname="transactions",
    user="root",
    password="secret",
    host="localhost",
    port="5432"
)
print("Connection successful.")

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Get list of CSV files in the "./data" directory
data_dir = "./data/amex"
csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

# Process each CSV file
for csv_file in csv_files:
    print(f"Processing CSV file: {csv_file}")
    with open(os.path.join(data_dir, csv_file), newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            # Parse date from string to Python date object
            fecha = datetime.strptime(row['Fecha'], '%d %b %Y').date()
            descripcion = row['Descripción']
            descripcion = re.sub(r'\s+', '-', descripcion)
            importe = float(row['Importe'])
            tag = infer_tag(descripcion)
            
            # Check if a record with the same composite primary key exists
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE date = %s AND description = %s AND amount = %s", (fecha, descripcion, importe))
            count = cursor.fetchone()[0]
            
            if count == 0 and importe > 0.0:
                # Insert row into PostgreSQL database
                cursor.execute("""
                INSERT INTO transactions (date, description, amount, tag, card) 
                VALUES (%s, %s, %s, %s, 'amex') 
                ON CONFLICT (date, description, amount) 
                DO NOTHING;
                """, (fecha, descripcion, importe, tag))

                print("Inserted:", csv_file, fecha, descripcion, importe)
            else:
                print("Skipping duplicate record:", csv_file, fecha, descripcion, importe)

# Commit changes to the database
conn.commit()
print("Changes committed to the database.")

# Close the cursor and database connection
cursor.close()
conn.close()
print("Database connection closed.")
