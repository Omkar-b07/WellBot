import pandas as pd
from sqlalchemy import create_engine, text
import os

# --- CONFIGURATION ---
CSV_FILE_NAME = 'health_knowledge.csv'  # The new file you just created
TABLE_NAME = 'health_knowledge'         # The new table we will create
# ---------------------

# Path to the database
DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'project.db')
db_engine = create_engine(f'sqlite:///{DB_PATH}')

try:
    print(f"Reading {CSV_FILE_NAME}...")
    df = pd.read_csv(CSV_FILE_NAME)
    
    # All columns in the CSV are already named perfectly
    # 'intent', 'entity', 'response_en', 'response_hi'
    print(f"Found columns: {df.columns.tolist()}")

    # Load data into the new 'health_knowledge' table
    print(f"Writing data to '{TABLE_NAME}' table in project.db...")
    df.to_sql(TABLE_NAME, db_engine, if_exists='replace', index=False)
    
    print("\nSuccess! Your Health Knowledge Base is now in the database.")
    print(f"\nFirst 5 rows from the new '{TABLE_NAME}' table:")
    
    # Verify by reading back from the DB
    with db_engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {TABLE_NAME} LIMIT 5")).fetchall()
        for row in result:
            print(row)

except FileNotFoundError:
    print(f"ERROR: Could not find the file {CSV_FILE_NAME}. Make sure it's in the same folder.")
except Exception as e:
    print(f"An error occurred: {e}")