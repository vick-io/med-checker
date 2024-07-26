# backend/display_db.py
import sqlite3
import os

# Create an absolute path for the SQLite database
db_path = os.path.join(os.path.dirname(__file__), 'medications.db')

# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Query to select a few rows from the medications table
query = "SELECT * FROM medications LIMIT 5"

cursor.execute(query)
rows = cursor.fetchall()

# Print the rows
for row in rows:
    print(row)

# Close the connection
conn.close()
