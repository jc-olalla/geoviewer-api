# app/schemas/catalog.py
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AccessMode(str, Enum):
    direct = "direct"
    proxy = "proxy"


class ClientAuth(str, Enum):
    public = "public"
    supabase_user = "supabase_user"
    none = "none"


class ProviderKind(str, Enum):
    supabase_rest = "supabase_rest"
    wfs = "wfs"
    ogc_features = "ogc_features"
    xyz = "xyz"
    http = "http"


class AccessSchema(BaseModel):
    mode: AccessMode
    provider: ProviderKind
    endpoint: Optional[str] = None
    auth: Optional[ClientAuth] = None
    proxy_url: Optional[str] = None
    read: Dict[str, Any] = Field(default_factory=dict)
    write: Optional[Dict[str, Any]] = None


class LayerType(str, Enum):
    vector = "vector"
    raster = "raster"


class GeometryType(str, Enum):
    point = "point"
    line = "line"
    polygon = "polygon"
    any = "any"


class LayerConfigSchema(BaseModel):
    id: str
    title: str
    type: LayerType
    geometry: GeometryType
    access: AccessSchema
    order: int = 0
    visible: bool = True
    style: Dict[str, Any] = Field(default_factory=dict)


class CatalogResponseSchema(BaseModel):
    tenant: str
    app: str
    version: str
    layers: List[LayerConfigSchema]
