from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas import schemas
from app.crud import layers as crud_layers
from app.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[schemas.LayerOut])
def read_layers(db: Session = Depends(get_db)):
    return crud_layers.get_layers(db)

