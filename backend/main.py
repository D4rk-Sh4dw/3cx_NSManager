from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import auth, plans, audit, users, export, integration
from init_db import init_db

# Create tables
Base.metadata.create_all(bind=engine)
# Initialize Data
init_db()

app = FastAPI(title="Emergency Service Manager API")

# CORS
origins = ["*"]

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
app.include_router(users.router)
app.include_router(plans.router)
app.include_router(audit.router)
app.include_router(export.router)
app.include_router(integration.router)
