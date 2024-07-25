from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

class Medications(BaseModel):
    medications: list[str]

@app.post("/check-interactions")
async def check_interactions(medications: Medications):
    try:
        # Example payload and API call to DrugBank (replace with real API call)
        payload = {
            "drugbank_id": medications.medications  # Assuming drugbank_id is provided
        }
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.drugbank.com/v1/ddi", json=payload)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Welcome to the Med-Checker API"}
