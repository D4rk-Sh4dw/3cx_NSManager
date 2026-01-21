import subprocess
import sys

# DEBUG: Print installed packages
try:
    print("--- PIP FREEZE ---")
    subprocess.run([sys.executable, "-m", "pip", "freeze"], check=False)
    print("------------------")
except Exception as e:
    print(f"Error checking pip: {e}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import auth, persons, plans, audit
from init_db import init_db

# Create tables
Base.metadata.create_all(bind=engine)
# Initialize Data
init_db()

app = FastAPI(title="Emergency Service Manager API")

# CORS
origins = [
    "http://localhost:3000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Emergency Service Manager API is running"}

app.include_router(auth.router)
app.include_router(persons.router)
app.include_router(plans.router)
app.include_router(audit.router)
