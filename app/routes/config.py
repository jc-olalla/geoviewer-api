# app/routes/config.py
from __future__ import annotations
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud import layers as crud
from app.database import get_tenant_session
from app.schemas.layers import Layer as LayerSchema

router = APIRouter()  # no prefix here; set it in main.py


@router.get("/", response_model=List[LayerSchema])
def get_config(
    tenant: str,  # comes from the path prefix in main.py: /tenants/{tenant}/config
    viewer_id: Optional[int] = Query(
        None, description="Return layers belonging to this viewer"
    ),
    include_hidden: bool = Query(
        False, description="Include layers where visible=false"
    ),
    db: Session = Depends(get_tenant_session),
):
    """
    Return the catalog of layers for this tenant (and optionally a specific viewer).
    Reads from the tenant's catalog DB only; no GIS data is queried here.
    """
    try:
        items = crud.get_layers(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load layers: {e}")

    if viewer_id is not None:
        items = [lyr for lyr in items if lyr.viewer_id == viewer_id]

    if not include_hidden:
        items = [lyr for lyr in items if (lyr.visible is None) or (lyr.visible is True)]

    items.sort(key=lambda l: ((lyr_sort := (l.sort_order or 0)), l.id))
    return items
