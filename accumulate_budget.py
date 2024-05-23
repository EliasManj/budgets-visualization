import psycopg2
from psycopg2 import sql
from datetime import datetime
import argparse
from datetime import datetime
import pandas as pd
import yaml

# Database connection parameters
params = {
    "dbname": "transactions",
    "user": "root",
    "password": "secret",
    "host": "localhost",
    "port": "5432"
}

def get_previous_month(year, month):
    if month == 1:
        previous_month = 12
        previous_year = year - 1
    else:
        previous_month = month - 1
        previous_year = year
    
    return previous_year, previous_month

def get_transactions_for_month(year, month):
    """Fetch all rows from the transactions table for a given month."""
    # Ensure month is formatted as two digits
    month = f"{int(month):02d}"
    
    # Connect to the database
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    
    # Create the query
    query = sql.SQL("""
        SELECT *
        FROM transactions
        WHERE DATE_TRUNC('month', date) = %s::date;
    """)
    
    # Format the date for the first day of the month
    date_str = f"{year}-{month}-01"
    
    # Execute the query
    cur.execute(query, [date_str])
    
    # Fetch all rows
    rows = cur.fetchall()

    # Fetch column names
    colnames = [desc[0] for desc in cur.description]
    
    # Create DataFrame with column names
    df = pd.DataFrame(rows, columns=colnames)
    
    # Close the connection
    cur.close()
    conn.close()
    
    return df

def get_accumulated_budget_from_month_before(year, month):
    year, month = get_previous_month(year, month)
    """Fetch the accumulated budget from the previous month."""
    # Ensure month is formatted as two digits
    month = f"{int(month):02d}"
    
    # Connect to the database
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    
    # Create the query
    query = sql.SQL("""
        SELECT *
        FROM budget_accumulations
        WHERE DATE_TRUNC('month', date) = DATE_TRUNC('month', %s::date);
    """)
    
    # Format the date for the first day of the month
    date_str = f"{year}-{month}-01"
    
    # Execute the query
    cur.execute(query, [date_str])
    
    # Fetch the accumulated budget
    accumulated_budget = cur.fetchall()

    # Fetch column names
    colnames = [desc[0] for desc in cur.description]

    accumulated_budget =  pd.DataFrame(accumulated_budget, columns=colnames) if accumulated_budget else None
    
    # Close the connection
    cur.close()
    conn.close()
    
    return accumulated_budget

def open_budget_defs():
    file_path = 'budgets.yaml'
    # Open and read the YAML file
    with open(file_path, 'r') as file:
        yaml_data = yaml.safe_load(file)
    # Extract the 'budgets' dictionary and convert it into a list of tuples
    budget_items = list(yaml_data['budgets'].items())
    # Create a DataFrame
    budget_df = pd.DataFrame(budget_items, columns=['tag', 'budget'])
    return budget_df

def accumulate_transactions(transactions, accumulations):
    budgets = open_budget_defs().sort_values(by='tag')
    df = pd.DataFrame(transactions).sort_values(by='tag')
    df['date'] = pd.to_datetime(df['date'], format='%d-%m-%y', errors='coerce') # Convert to datetime
    accumulations_per_tag = df.groupby('tag')['amount'].sum().reset_index()
    accumulations_per_tag.columns = ['tag', 'amount']
    print(budgets)
    print(accumulations_per_tag)

    # operations
    ##
    merged_df = pd.merge(budgets, accumulations_per_tag, on='tag', how='left')
    # Fill NaN values in the 'amount' column with 0
    merged_df['amount'] = merged_df['amount'].fillna(0)
    # Subtract the 'amount' column from the 'budget' column
    merged_df['amount'] = merged_df['budget'] - merged_df['amount']
    # Drop the 'amount' column as it is no longer needed
    result_df = merged_df.drop(columns=['budget'])
    print(result_df)
    ##
    # end operations

    if accumulations is None:
        return result_df
    else:
        # Merge the two DataFrames, using 'outer' join to include all tags
        new_merge = pd.merge(result_df, accumulations, on='tag', how='left')
        new_merge['amount'] = new_merge['amount'].fillna(0)
        new_merge['amount'] = new_merge['amount_df1'] + new_merge['amount_df2']
        final_df = merged_df[['tag', 'amount']]
        return final_df
    
def insert_to_db(df):
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO budget_accumulations (tag, amount, date)
            VALUES (%s, %s, %s)
            ON CONFLICT (date, tag) 
            DO NOTHING;
        """, (row['tag'], row['amount'], datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    # Argument parser setup
    parser = argparse.ArgumentParser(description="Fetch transactions for a given month and year.")
    parser.add_argument('--month', type=int, required=True, help="Month (MM)")
    parser.add_argument('--year', type=int, required=True, help="Year (YYYY)")
    
    ## Parse arguments
    args = parser.parse_args()
    try:
        accumulations = get_accumulated_budget_from_month_before(args.year, args.month)
        transactions = get_transactions_for_month(args.year, args.month)
        new_accumulations = accumulate_transactions(transactions, accumulations)
        insert_to_db(new_accumulations)
        for row in transactions:
            print(row)
    except Exception as e:
        print(f"An error occurred: {e}")