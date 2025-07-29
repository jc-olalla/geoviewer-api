from sqlalchemy.orm import Session
from app.models import models
from app.schemas.layers import LayerCreate, LayerUpdate

def get_layers(db: Session):
    return db.query(models.Layer).all()

def get_layer(db: Session, layer_id: int):
    return db.query(models.Layer).filter(models.Layer.id == layer_id).first()

def create_layer(db: Session, layer: LayerCreate):
    db_layer = models.Layer(**layer.dict())
    db.add(db_layer)
    db.commit()
    db.refresh(db_layer)
    return db_layer

def update_layer(db: Session, layer_id: int, layer: LayerUpdate):
    db_layer = db.query(models.Layer).filter(models.Layer.id == layer_id).first()
    if db_layer:
        for key, value in layer.dict(exclude_unset=True).items():
            setattr(db_layer, key, value)
        db.commit()
        db.refresh(db_layer)
    return db_layer

def delete_layer(db: Session, layer_id: int):
    db_layer = db.query(models.Layer).filter(models.Layer.id == layer_id).first()
    if db_layer:
        db.delete(db_layer)
        db.commit()
    return db_layer

