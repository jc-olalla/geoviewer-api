from sqlalchemy.orm import Session
from app.models import models

def get_layers(db: Session):
    return db.query(models.Layer).all()

