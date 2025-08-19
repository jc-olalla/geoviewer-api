# === app/providers/base.py ===
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

# ---------------------------------------------------------------------------
# Control‑plane models for your CATALOG (NOT data fetching)
# ---------------------------------------------------------------------------
# These types describe what the viewer needs to know to fetch/visualize a layer
# (who, where, how). Your API will return these models as JSON from /config.
# They do not query any GIS databases.
# ---------------------------------------------------------------------------


class AccessMode(str, Enum):
    """How the client should access the datasource for this layer."""

    DIRECT = (
        "direct"  # Browser calls provider directly (e.g., Supabase Auth, public tiles)
    )
    PROXY = "proxy"  # Browser calls YOUR API, which calls the provider (keeps secrets serverside)


class ClientAuth(str, Enum):
    """How the CLIENT authenticates (only relevant for mode=DIRECT)."""

    PUBLIC = "public"  # no auth needed (e.g., public tiles)
    SUPABASE_USER = "supabase_user"  # client uses Supabase Auth (JWT) + anon key
    NONE = "none"  # discouraged; same as PUBLIC but explicit


class ProviderKind(str, Enum):
    """Logical provider types your viewer understands."""

    SUPABASE_REST = "supabase_rest"  # Supabase REST/RPC
    WFS = "wfs"  # OGC WFS (or OGC API – Features)
    OGC_FEATURES = "ogc_features"
    XYZ = "xyz"  # raster/tiles
    HTTP = "http"  # generic HTTP JSON/GeoJSON endpoint (e.g., your Option‑B API)


@dataclass(frozen=True)
class BBox3857:
    """Axis‑aligned bbox in EPSG:3857.

    Useful for validating incoming query params in your routes (not part of the
    catalog per se, but shared across the API).
    """

    minx: float
    miny: float
    maxx: float
    maxy: float

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.minx, self.miny, self.maxx, self.maxy)

    @property
    def width(self) -> float:
        return float(self.maxx - self.minx)

    @property
    def height(self) -> float:
        return float(self.maxy - self.miny)

    @property
    def area(self) -> float:
        return self.width * self.height

    def validate(self, max_area: Optional[float] = None) -> None:
        if self.minx >= self.maxx or self.miny >= self.maxy:
            raise ValueError("Invalid bbox: min must be < max on both axes")
        if max_area is not None and self.area > max_area:
            raise ValueError(f"BBox area {self.area:.0f} exceeds limit {max_area:.0f}")


# ----------------------------
# Access configuration (what the client should call)
# ----------------------------
@dataclass(frozen=True)
class Access:
    """How the viewer should access this layer's datasource.

    - mode=direct: the client calls `endpoint` itself (e.g., Supabase REST, public WMS).
                   `auth` tells the client how to authenticate (e.g., supabase_user).
    - mode=proxy:  the client must call YOUR API at `proxy_url` and never touch the
                   upstream provider directly. Your server holds secrets.

    `read`/`write` are *provider‑specific* descriptors (free‑form mappings) the
    adapter on the client (or your proxy) can interpret (e.g., RPC names, bbox param names).
    """

    mode: AccessMode
    provider: ProviderKind

    # DIRECT mode fields
    endpoint: Optional[str] = None  # e.g., https://<ref>.supabase.co
    auth: Optional[ClientAuth] = None  # e.g., SUPABASE_USER or PUBLIC

    # PROXY mode field
    proxy_url: Optional[str] = (
        None  # e.g., /layers/buildings/features (served by YOUR API)
    )

    # Provider‑specific descriptors
    read: Mapping[str, Any] = field(default_factory=dict)
    write: Optional[Mapping[str, Any]] = None

    def validate(self) -> None:
        if self.mode == AccessMode.DIRECT:
            if not self.endpoint:
                raise ValueError("DIRECT access requires 'endpoint'")
            if not self.auth:
                raise ValueError("DIRECT access requires 'auth'")
            if self.proxy_url:
                raise ValueError("DIRECT access must not set 'proxy_url'")
        elif self.mode == AccessMode.PROXY:
            if not self.proxy_url:
                raise ValueError("PROXY access requires 'proxy_url'")
            if self.endpoint or self.auth:
                raise ValueError("PROXY access must not set 'endpoint' or 'auth'")
        else:
            raise ValueError(f"Unknown access mode: {self.mode}")


# ----------------------------
# Layer definition for the catalog
# ----------------------------
class LayerType(str, Enum):
    VECTOR = "vector"
    RASTER = "raster"


class GeometryType(str, Enum):
    POINT = "point"
    LINE = "line"
    POLYGON = "polygon"
    ANY = "any"


@dataclass(frozen=True)
class LayerConfig:
    id: str
    title: str
    type: LayerType
    geometry: GeometryType
    access: Access
    order: int = 0
    visible: bool = True
    style: Mapping[str, Any] = field(
        default_factory=dict
    )  # simple style hints for the viewer

    def validate(self) -> None:
        self.access.validate()

    def to_dict(self) -> Dict[str, Any]:  # handy for JSON responses
        d = asdict(self)
        # Enums → plain strings
        d["type"] = self.type.value
        d["geometry"] = self.geometry.value
        d["access"]["mode"] = self.access.mode.value
        d["access"]["provider"] = self.access.provider.value
        if d["access"].get("auth"):
            d["access"]["auth"] = self.access.auth.value  # type: ignore[union-attr]
        return d


@dataclass(frozen=True)
class CatalogResponse:
    tenant: str
    app: str
    version: str
    layers: List[LayerConfig]

    def validate(self) -> None:
        for lyr in self.layers:
            lyr.validate()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant": self.tenant,
            "app": self.app,
            "version": self.version,
            "layers": [lyr.to_dict() for lyr in self.layers],
        }


# ---------------------------------------------------------------------------
# Minimal exceptions for your API layer (mapping to HTTP codes)
# ---------------------------------------------------------------------------
class CatalogError(Exception):
    pass


class ForbiddenError(CatalogError):
    pass


class NotFoundError(CatalogError):
    pass
