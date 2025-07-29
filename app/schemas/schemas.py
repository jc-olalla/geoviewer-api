from pydantic import BaseModel
from typing import Optional

class LayerOut(BaseModel):
    id: int
    viewer_id: int
    type: str
    name: str
    title: Optional[str]
    url: Optional[str]
    layer_name: Optional[str]
    version: Optional[str]
    crs: Optional[str]
    style: Optional[str]
    format: Optional[str]
    tiled: Optional[bool]
    opacity: Optional[float]
    visible: Optional[bool]
    min_zoom: Optional[int]
    max_zoom: Optional[int]
    sort_order: Optional[int]
    layer_params: Optional[dict]
    extra_config: Optional[dict]
    bbox: Optional[dict]

    class Config:
        orm_mode = True

