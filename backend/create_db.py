# backend/create_db.py
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Read the cleaned CSV file
df = pd.read_csv('medications_cleaned.csv')

# Select relevant columns
df = df[['PROPRIETARYNAME', 'NONPROPRIETARYNAME']]

# Rename columns for consistency
df.rename(columns={'PROPRIETARYNAME': 'proprietary_name', 'NONPROPRIETARYNAME': 'nonproprietary_name'}, inplace=True)

# Create an absolute path for the SQLite database
db_path = os.path.join(os.path.dirname(__file__), 'medications.db')
engine = create_engine(f'sqlite:///{db_path}')
Base = declarative_base()

# Define the Medication model
class Medication(Base):
    __tablename__ = 'medications'
    id = Column(Integer, primary_key=True, autoincrement=True)
    proprietary_name = Column(String, index=True)
    nonproprietary_name = Column(String, index=True)

# Drop the existing table if it exists
Base.metadata.drop_all(engine)

# Create the medications table
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Insert data into the medications table
for index, row in df.iterrows():
    medication = Medication(proprietary_name=row['proprietary_name'], nonproprietary_name=row['nonproprietary_name'])
    session.add(medication)

# Commit the transaction
session.commit()
session.close()
