from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Person
from schemas import Person as PersonSchema, PersonCreate
from routers.auth import get_current_user

router = APIRouter(prefix="/plans", tags=["plans"]) 
# Wait, this file is users.py, let's stick to users/persons
# Let's rename router tag to persons for this file or create separate persons router?
# The user asked for "CRUD fur Benutzer/Personen".
# Users = System Users (Login)
# Persons = Emergency Contacts
# I will put Persons CRUD here for now or separate? 
# Let's do Persons CRUD here.

router = APIRouter(prefix="/persons", tags=["persons"])

@router.get("/", response_model=List[PersonSchema])
def read_persons(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    persons = db.query(Person).offset(skip).limit(limit).all()
    return persons

@router.post("/", response_model=PersonSchema)
def create_person(person: PersonCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_person = Person(**person.dict())
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person

@router.delete("/{person_id}")
def delete_person(person_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_person = db.query(Person).filter(Person.id == person_id).first()
    if not db_person:
        raise HTTPException(status_code=404, detail="Person not found")
    db.delete(db_person)
    db.commit()
    return {"ok": True}
