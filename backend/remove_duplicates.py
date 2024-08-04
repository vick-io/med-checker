from sqlalchemy import create_engine, Column, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database connection parameters
DATABASE_URL = "mysql+mysqlconnector://root:44551237895@localhost/rxnorm_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the MedscapeDrug model
class MedscapeDrug(Base):
    __tablename__ = 'medscape_drugs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    medscape_id = Column(String(255))

Base.metadata.create_all(bind=engine)

def remove_duplicates():
    session = SessionLocal()
    try:
        # Find duplicates based on name and medscape_id
        subquery = session.query(
            MedscapeDrug.name,
            MedscapeDrug.medscape_id,
            func.count(MedscapeDrug.id).label('count')
        ).group_by(MedscapeDrug.name, MedscapeDrug.medscape_id).having(func.count(MedscapeDrug.id) > 1).subquery()

        duplicates = session.query(MedscapeDrug).join(
            subquery,
            (MedscapeDrug.name == subquery.c.name) & (MedscapeDrug.medscape_id == subquery.c.medscape_id)
        ).order_by(MedscapeDrug.name, MedscapeDrug.medscape_id, MedscapeDrug.id).all()

        current_name = None
        current_medscape_id = None
        to_delete = []

        for drug in duplicates:
            if drug.name == current_name and drug.medscape_id == current_medscape_id:
                to_delete.append(drug.id)
            else:
                current_name = drug.name
                current_medscape_id = drug.medscape_id

        if to_delete:
            session.query(MedscapeDrug).filter(MedscapeDrug.id.in_(to_delete)).delete(synchronize_session=False)
            session.commit()
            logging.info(f"Removed {len(to_delete)} duplicate entries.")
        else:
            logging.info("No duplicates found.")

    except Exception as e:
        logging.error(f"Error removing duplicates: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    remove_duplicates()
