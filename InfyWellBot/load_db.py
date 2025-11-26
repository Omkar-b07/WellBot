import pandas as pd
from sqlalchemy import create_engine, text
import os


CSV_FILE_NAME = 'wellness.csv'  

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'project.db')
db_engine = create_engine(f'sqlite:///{DB_PATH}')

try:
    print(f"Reading {CSV_FILE_NAME}...")
    
    df = pd.read_csv(CSV_FILE_NAME, dtype=str)
    
    print(f"Found columns: {df.columns.tolist()}")


    print("Writing 50,000 rows to 'user_wellness_data' table in project.db...")
    df.to_sql('user_wellness_data', db_engine, if_exists='replace', index=False)
    
    print("\nSuccess! Database has been populated with your CSV data.")
    print("\nFirst 5 rows from the new 'user_wellness_data' table:")
    
  
    with db_engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM user_wellness_data LIMIT 5")).fetchall()
        for row in result:
            print(row)

except FileNotFoundError:
    print(f"ERROR: Could not find the file {CSV_FILE_NAME}. Make sure it's in the same folder as this script.")
except Exception as e:
    print(f"An error occurred: {e}")