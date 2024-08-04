# backend/app/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, UniqueConstraint
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

class MedscapeDrug(Base):
    __tablename__ = "medscape_drugs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), index=True)
    medscape_id = Column(String(255), index=True)

Base.metadata.create_all(bind=engine)

class Medications(BaseModel):
    medication: dict
    current_medications: list[dict]

@app.post("/check-interactions")
async def check_interactions(request: Medications):
    try:
        session = SessionLocal()
        medication_medscape_id = request.medication['medscape_id']
        current_medications_medscape_id = [med['medscape_id'] for med in request.current_medications]
        session.close()
        
        if not medication_medscape_id:
            raise HTTPException(status_code=400, detail=f"Medscape ID not found for medication: {request.medication['name']}")
        
        missing_medscape_ids = [med for med in request.current_medications if not med['medscape_id']]
        if missing_medscape_ids:
            raise HTTPException(status_code=400, detail=f"Medscape ID not found for medications: {missing_medscape_ids}")
        
        interactions = await get_interactions([medication_medscape_id] + current_medications_medscape_id)
        return {"interactions": interactions}
    except Exception as e:
        print(f"Unexpected error during interaction check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_interactions(medscape_ids: list[str]) -> list[dict]:
    try:
        print(f"Fetching interactions for Medscape IDs: {medscape_ids}")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://reference.medscape.com/druginteraction.do?action=getMultiInteraction&ids={','.join(medscape_ids)}"
            )
            print(f"Interaction API response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            print(f"Fetched data: {data}")  # Added log to show the fetched data
            if 'multiInteractions' not in data:
                raise ValueError("No interaction data found")
            interactions = []
            for interaction in data['multiInteractions']:
                interactions.append({
                    "medication1": interaction["subject"],
                    "medication2": interaction["object"],
                    "interaction": interaction["text"],
                    "severity": interaction["severity"]
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
        medications = session.query(MedscapeDrug).filter(
            func.lower(MedscapeDrug.name).like(func.lower(f"{query}%"))
        ).order_by(MedscapeDrug.name.asc()).limit(10).all()
        session.close()

        if not medications:
            print("No medications found matching the query.")
            raise HTTPException(status_code=404, detail="No medications found")

        suggestions = [
            {"name": med.name, "medscape_id": med.medscape_id} for med in medications
        ]
        print(f"Suggestions: {suggestions}")
        return {"suggestions": suggestions}
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Med-Checker API"}
