from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String

# Database connection parameters
DATABASE_URL = "mysql+mysqlconnector://root:44551237895@localhost/rxnorm_db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Define the MedscapeDrug model
class MedscapeDrug(Base):
    __tablename__ = 'medscape_drugs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, index=True)
    medscape_id = Column(String(255), unique=True, index=True)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Query all records
drugs = session.query(MedscapeDrug).all()

if not drugs:
    print("No records found in the medscape_drugs table.")
else:
    for drug in drugs:
        print(f"Drug: {drug.name}, ID: {drug.medscape_id}")

# Close the database connection
session.close()
