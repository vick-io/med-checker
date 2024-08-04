import requests
from bs4 import BeautifulSoup
import time
from sqlalchemy import create_engine, Column, Integer, String
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

# Base URL for Medscape
base_url = "https://reference.medscape.com"

# List of categories and their URLs
categories = [
    "allergy-cold", "anesthetics", "antidotes", "antimicrobials", "blood-components", "cardiovascular",
    "critical-care", "dental-oral-care", "dermatologics", "gastrointestinal", "hematologics", "herbals-supplements",
    "imaging-agents", "immunologics", "metabolic-endocrine", "neurologics", "nutritionals", "oncology",
    "ophthalmics", "otics", "pain-management", "psychiatrics", "pulmonary", "rheumatologics", "urologics",
    "vaccinations", "womens-health-reproduction"
]

def get_drug_ids(category):
    category_url = f"{base_url}/drugs/{category}"
    response = requests.get(category_url)
    if response.status_code != 200:
        logging.error(f"Failed to retrieve {category_url}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    # Find all alphabetical sections
    alpha_sections = soup.select('div.alpha-select-wrap div.alpha-select')
    
    for section in alpha_sections:
        alpha = section.get('data-alpha')
        if 'disabled' in section.get('class', []):
            continue

        alpha_url = f"{category_url}?alpha={alpha}"
        alpha_response = requests.get(alpha_url)
        if alpha_response.status_code != 200:
            logging.error(f"Failed to retrieve {alpha_url}")
            continue

        alpha_soup = BeautifulSoup(alpha_response.text, 'html.parser')
        drug_links = alpha_soup.select('ul li.alpha-item a')
        for link in drug_links:
            drug_name = link.text.strip()
            drug_url = link.get('href')
            if drug_url:
                drug_id = drug_url.split('-')[-1]
                logging.info(f"Drug: {drug_name}, ID: {drug_id}")
                try:
                    session = SessionLocal()
                    drug = MedscapeDrug(name=drug_name, medscape_id=drug_id)
                    session.add(drug)
                    session.commit()
                    session.close()
                except Exception as e:
                    logging.error(f"Error inserting {drug_name} with ID {drug_id}: {e}")
        time.sleep(1)  # Add a delay to avoid overwhelming the server

# Scrape each category
for category in categories:
    logging.info(f"Scraping category: {category}")
    get_drug_ids(category)
