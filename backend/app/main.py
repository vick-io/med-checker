# backend/app/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import os
import httpx
import xml.etree.ElementTree as ET

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create an absolute path for the SQLite database
db_path = os.path.join(os.path.dirname(__file__), '../medications.db')
print(f"Database path: {os.path.abspath(db_path)}")

engine = create_engine(f'sqlite:///{db_path}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True, index=True)
    proprietary_name = Column(String, index=True)
    nonproprietary_name = Column(String, index=True)

Base.metadata.create_all(bind=engine)

class Medications(BaseModel):
    medication: str
    current_medications: list[str]

@app.post("/check-interactions")
async def check_interactions(request: Medications):
    try:
        medication_rxcui = await get_rxcui(request.medication)
        current_medications_rxcui = [
            await get_rxcui(med) for med in request.current_medications
        ]
        interactions = await get_interactions(
            [medication_rxcui] + current_medications_rxcui
        )
        return {"interactions": interactions}
    except Exception as e:
        print(f"Unexpected error during interaction check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_rxcui(medication_name: str) -> str:
    try:
        # Extract proprietary name only
        proprietary_name = medication_name.split(" (")[0]
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://rxnav.nlm.nih.gov/REST/rxcui?name={proprietary_name}"
            )
            response.raise_for_status()
            if "application/json" in response.headers.get("Content-Type", ""):
                data = response.json()
                if 'idGroup' in data and 'rxnormId' in data['idGroup']:
                    return data['idGroup']['rxnormId'][0]
                else:
                    raise ValueError(f"No RxNorm ID found for {medication_name}")
            elif "application/xml" in response.headers.get("Content-Type", ""):
                root = ET.fromstring(response.text)
                rxcui = root.find(".//rxnormId")
                if rxcui is not None:
                    return rxcui.text
                else:
                    raise ValueError(f"No RxNorm ID found for {medication_name}")
            else:
                print(f"Unexpected response content type: {response.headers.get('Content-Type')}")
                print(f"Response content: {response.text}")
                raise ValueError(f"Unexpected response format for {medication_name}")
    except Exception as e:
        print(f"Error fetching RxCUI for {medication_name}: {e}")
        raise

async def get_interactions(rxcuis: list[str]) -> list[dict]:
    try:
        print(f"Fetching interactions for RxCUIs: {rxcuis}")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={','.join(rxcuis)}"
            )
            print(f"Interaction API response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            if 'fullInteractionTypeGroup' not in data:
                raise ValueError("No interaction data found")
            interactions = []
            for interaction_group in data['fullInteractionTypeGroup']:
                for interaction in interaction_group["fullInteractionType"]:
                    for pair in interaction["interactionPair"]:
                        interactions.append({
                            "medication1": pair["interactionConcept"][0]["sourceConceptItem"]["name"],
                            "medication2": pair["interactionConcept"][1]["sourceConceptItem"]["name"],
                            "interaction": pair["description"]
                        })
            return interactions
    except httpx.HTTPStatusError as http_err:
        print(f"HTTP error during interaction check: {http_err}")
        raise HTTPException(status_code=response.status_code, detail=f"HTTP error occurred: {http_err}")
    except Exception as e:
        print(f"Error fetching interactions: {e}")
        raise

@app.get("/search-medications")
def search_medications(query: str = Query(..., min_length=1)):
    try:
        print(f"Received query: {query}")
        session = SessionLocal()

        # Perform the search query
        medications = session.query(Medication).filter(
            (func.lower(Medication.proprietary_name).like(func.lower(f"{query}%"))) |
            (func.lower(Medication.nonproprietary_name).like(func.lower(f"{query}%")))
        ).order_by(Medication.proprietary_name.asc(), Medication.nonproprietary_name.asc()).limit(10).all()
        session.close()

        if not medications:
            print("No medications found matching the query.")
            raise HTTPException(status_code=404, detail="No medications found")

        suggestions = [
            f"{med.proprietary_name} ({med.nonproprietary_name})" for med in medications
        ]
        print(f"Suggestions: {suggestions}")
        return {"suggestions": suggestions}
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Med-Checker API"}
