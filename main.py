from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from models import Contact
from db import get_db
from schemas import Contact, ContactCreate

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    try:
        # Make request
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")


@app.get("/contacts/")
async def get_all_contacts(db: Session = Depends(get_db)):
    contacts = db.query(Contact).all()
    if not contacts:
        return {"message": "База пуста"}
    return contacts


@app.post("/newcontact/", response_model=Contact)
async def create_contact(new_contact: ContactCreate, db: Session = Depends(get_db)):
    try:
        # Створення нового контакту
        contact = Contact(**new_contact.model_dump())
        db.add(contact)
        db.commit()
        return contact
    except Exception as e:
        # Якщо виникла помилка при створенні контакту
        raise HTTPException(status_code=400, detail="Помилка створення контакту")


# Endpoint для отримання одного контакту за ідентифікатором
@app.get("/contacts/{contact_id}", response_model=Contact)
async def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Контакт не знайдено")
    return contact


# Endpoint для оновлення контакту за ідентифікатором
@app.put("/contacts/{contact_id}", response_model=ContactCreate)
async def update_contact(contact_id: int, updated_contact: Contact, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Контакт не знайдено")

    contact_data = vars(updated_contact)
    for field, value in contact_data.items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)

    return contact


#
#
# Endpoint для видалення контакту за ідентифікатором
@app.delete("/contacts/{contact_id}", response_model=Contact)
async def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Контакт не знайдено")
    db.delete(contact)
    db.commit()
    return {"message": "Контакт видалено успішно"}


#
#
@app.get("/contacts/search/", response_model=Contact)
async def search_contacts(
        query: str = Query(..., min_length=1, description="Пошуковий запит (ім'я, прізвище або email)"),
        db: Session = Depends(get_db)
):
    contacts = (
        db.query(Contact)
        .filter(
            (Contact.first_name.ilike(f"%{query}%")) |
            (Contact.last_name.ilike(f"%{query}%")) |
            (Contact.email.ilike(f"%{query}%"))
        )
        .all()
    )
    return contacts


# Endpoint для отримання контактів з днями народження на найближчі 7 днів
@app.get("/contacts/birthdays/", response_model=Contact)
async def upcoming_birthdays(db: Session = Depends(get_db)):
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    birthdays = (
        db.query(Contact)
        .filter(
            (Contact.birthday >= today) &
            (Contact.birthday <= next_week)
        )
        .order_by(Contact.birthday)
        .all()
    )
    return birthdays
