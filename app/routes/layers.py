from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.layers import Layer, LayerCreate, LayerUpdate 
from app.crud import layers as crud

router = APIRouter()

@router.get("/", response_model=list[Layer])
def list_layers(db: Session = Depends(get_db)):
    return crud.get_layers(db)

@router.get("/{layer_id}", response_model=Layer)
def get_layer(layer_id: int, db: Session = Depends(get_db)):
    layer = crud.get_layer(db, layer_id)
    if not layer:
        raise HTTPException(status_code=404, detail="Layer not found")
    return layer

@router.post("/", response_model=Layer)
def create_layer(layer: LayerCreate, db: Session = Depends(get_db)):
    return crud.create_layer(db, layer)

@router.put("/{layer_id}", response_model=Layer)
def update_layer(layer_id: int, layer: LayerUpdate, db: Session = Depends(get_db)):
    db_layer = crud.update_layer(db, layer_id, layer)
    if not db_layer:
        raise HTTPException(status_code=404, detail="Layer not found")
    return db_layer

@router.delete("/{layer_id}", response_model=Layer)
def delete_layer(layer_id: int, db: Session = Depends(get_db)):
    db_layer = crud.delete_layer(db, layer_id)
    if not db_layer:
        raise HTTPException(status_code=404, detail="Layer not found")
    return db_layer

