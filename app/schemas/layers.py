from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class LayerBase(BaseModel):
    viewer_id: int
    type: str
    name: str
    title: Optional[str] = None
    url: Optional[str] = None
    layer_name: Optional[str] = None
    version: Optional[str] = None
    crs: Optional[str] = 'EPSG:3857'
    style: Optional[str] = None
    format: Optional[str] = None
    tiled: Optional[bool] = False
    opacity: Optional[float] = 1.0
    visible: Optional[bool] = True
    min_zoom: Optional[int] = None
    max_zoom: Optional[int] = None
    sort_order: Optional[int] = None
    layer_params: Optional[Any] = None
    extra_config: Optional[Any] = None
    bbox: Optional[Any] = None

class LayerCreate(LayerBase):
    pass

class LayerUpdate(LayerBase):
    pass

class Layer(LayerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

