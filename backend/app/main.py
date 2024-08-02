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

# Database connection parameters
DATABASE_URL = "mysql+mysqlconnector://root:44551237895@localhost/rxnorm_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RXNCONSO(Base):
    __tablename__ = "RXNCONSO"
    RXCUI = Column(String, primary_key=True, index=True)
    LAT = Column(String)
    TS = Column(String)
    LUI = Column(String)
    STT = Column(String)
    SUI = Column(String)
    ISPREF = Column(String)
    RXAUI = Column(String)
    SAUI = Column(String)
    SCUI = Column(String)
    SDUI = Column(String)
    SAB = Column(String)
    TTY = Column(String)
    CODE = Column(String)
    STR = Column(String)
    SRL = Column(Integer)
    SUPPRESS = Column(String)
    CVF = Column(String)

Base.metadata.create_all(bind=engine)

class Medications(BaseModel):
    medication: str
    current_medications: list[str]

@app.post("/check-interactions")
async def check_interactions(request: Medications):
    try:
        session = SessionLocal()
        medication_rxcui = get_rxcui_from_db(session, request.medication)
        current_medications_rxcui = [get_rxcui_from_db(session, med) for med in request.current_medications]
        session.close()
        
        if not medication_rxcui:
            raise HTTPException(status_code=400, detail=f"RxCUI not found for medication: {request.medication}")
        
        missing_rxcuis = [med for med, rxcui in zip(request.current_medications, current_medications_rxcui) if not rxcui]
        if missing_rxcuis:
            raise HTTPException(status_code=400, detail=f"RxCUI not found for medications: {missing_rxcuis}")
        
        interactions = await get_interactions([medication_rxcui] + current_medications_rxcui)
        return {"interactions": interactions}
    except Exception as e:
        print(f"Unexpected error during interaction check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_rxcui_from_db(session, medication_name: str):
    try:
        medication = session.query(RXNCONSO).filter(
            func.lower(RXNCONSO.STR) == func.lower(medication_name)
        ).first()
        
        if medication:
            print(f"RxCUI found for {medication_name}: {medication.RXCUI}")
            return medication.RXCUI
        else:
            print(f"No RxCUI found for {medication_name}")
            return None
    except Exception as e:
        print(f"Error fetching RxCUI from DB for {medication_name}: {e}")
        return None

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
        medications = session.query(RXNCONSO).filter(
            func.lower(RXNCONSO.STR).like(func.lower(f"{query}%"))
        ).order_by(RXNCONSO.STR.asc()).limit(10).all()
        session.close()

        if not medications:
            print("No medications found matching the query.")
            raise HTTPException(status_code=404, detail="No medications found")

        suggestions = [
            f"{med.STR} ({med.RXCUI})" for med in medications
        ]
        print(f"Suggestions: {suggestions}")
        return {"suggestions": suggestions}
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Med-Checker API"}
