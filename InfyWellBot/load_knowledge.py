import pandas as pd
from sqlalchemy import create_engine, text
import os

# --- CONFIGURATION ---
CSV_FILE_NAME = 'health_knowledge.csv'
TABLE_NAME = 'health_knowledge'
DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'project.db')
# ---------------------

# Create engine
db_engine = create_engine(f'sqlite:///{DB_PATH}')

try:
    print(f"Reading {CSV_FILE_NAME}...")
    df = pd.read_csv(CSV_FILE_NAME)
    
    print(f"Found columns: {df.columns.tolist()}")

    # --- THIS IS THE CHANGE ---
    # We use 'append' to add data to the table created by app.py
    # We set 'if_exists='append''
    # We set index=False so pandas doesn't create its own index column
    print(f"Appending data to '{TABLE_NAME}' table in project.db...")
    df.to_sql(TABLE_NAME, db_engine, if_exists='append', index=False)
    # --- END CHANGE ---

    print(f"\nSuccess! Health Knowledge Base has been populated.")
    
    # Verify by reading back from the DB
    with db_engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME}")).fetchone()
        print(f"Total rows in '{TABLE_NAME}': {result[0]}")

except FileNotFoundError:
    print(f"ERROR: Could not find the file {CSV_FILE_NAME}.")
except Exception as e:
    print(f"An error occurred: {e}")
    print("This can happen if the 'health_knowledge' table doesn't exist.")
    print("Please run 'python app.py' once to create the tables before running this script.")