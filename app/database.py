# app/database.py
from __future__ import annotations
from contextlib import contextmanager
import json
import os
import socket
import threading
from typing import Dict, Generator, Iterable, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit

import yaml

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# ------------------------------------------------------------------------------
# SQLAlchemy base (models import this)
# ------------------------------------------------------------------------------
Base = declarative_base()

# ------------------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------------------

def _normalize_host(dsn: str) -> str:
    """
    If DSN host is 'host.docker.internal' but that hostname is NOT resolvable
    (typical when running outside Docker), replace with 'localhost'.
    """
    try:
        parts = urlsplit(dsn)
    except Exception:
        return dsn
    host = parts.hostname or ""
    if host == "host.docker.internal":
        try:
            socket.gethostbyname(host)  # raises if not resolvable
        except socket.gaierror:
            netloc = parts.netloc.replace("host.docker.internal", "localhost", 1)
            return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    return dsn

# ------------------------------------------------------------------------------
# Tenant registry: maps tenant slug -> DSN
#
# Sources (later entries override earlier):
#   1) YAML file (CATALOG_TENANTS_FILE, default 'tenants.yaml')
#      - Supports BOTH:
#          tenants:
#            - { slug: brandweer, dsn: ... }
#            - { slug: vik,       dsn: ... }
#        AND:
#          tenants:
#            brandweer: { dsn: ... }
#            vik:       { dsn: ... }
#   2) TENANT_DSN_MAP='{"brandweer":"postgresql://...","vik":"postgresql://..."}'
#   3) TENANT_<SLUG>_DSN env vars, e.g. TENANT_BRANDWEER_DSN=postgresql://...
# Fallback (single-tenant): DATABASE_URL -> slug 'default'
# ------------------------------------------------------------------------------

class TenantRegistry:
    def __init__(self, path: Optional[str] = None) -> None:
        self._lock = threading.Lock()
        self._map: Dict[str, str] = {}
        self._yaml_path = path or os.getenv("CATALOG_TENANTS_FILE", "tenants.yaml")
        self._yaml_mtime: Optional[float] = None
        self._load_all()

    # ---- loaders ----

    def _load_yaml(self) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        if not self._yaml_path:
            return mapping
        try:
            mt = os.path.getmtime(self._yaml_path)
        except FileNotFoundError:
            return mapping

        with open(self._yaml_path, "r") as f:
            data = yaml.safe_load(f) or {}

        tenants = data.get("tenants", data) or {}
        if isinstance(tenants, dict):
            # mapping form
            for k, v in tenants.items():
                if isinstance(v, dict) and "dsn" in v:
                    mapping[k.lower()] = _normalize_host(str(v["dsn"]))
                elif isinstance(v, str):
                    mapping[k.lower()] = _normalize_host(v)
        elif isinstance(tenants, list):
            # list form
            for item in tenants:
                if not isinstance(item, dict):
                    continue
                slug = str(item.get("slug") or "").lower()
                dsn = item.get("dsn") or item.get("url")
                if slug and dsn:
                    mapping[slug] = _normalize_host(str(dsn))
        else:
            # unknown shape -> ignore
            pass

        self._yaml_mtime = mt
        return mapping

    def _load_env_json(self) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        raw = os.getenv("TENANT_DSN_MAP", "").strip()
        if not raw:
            return mapping
        try:
            data = json.loads(raw)
            for k, v in data.items():
                if isinstance(k, str) and isinstance(v, str):
                    mapping[k.lower()] = _normalize_host(v)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid TENANT_DSN_MAP JSON: {e}") from e
        return mapping

    def _load_env_vars(self) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        prefix, suffix = "TENANT_", "_DSN"
        for k, v in os.environ.items():
            if k.startswith(prefix) and k.endswith(suffix) and v:
                slug = k[len(prefix) : -len(suffix)].lower()
                mapping[slug] = _normalize_host(v)
        return mapping

    def _load_default_single(self) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        default = os.getenv("DATABASE_URL")
        if default:
            mapping["default"] = _normalize_host(default)
        return mapping

    def _load_all(self) -> None:
        # base from YAML
        m = self._load_yaml()
        # overlay env JSON
        m.update(self._load_env_json())
        # overlay per-tenant env
        m.update(self._load_env_vars())
        # add default (single-tenant) only if not already set
        m.setdefault("default", self._load_default_single().get("default", None))
        # remove None values
        self._map = {k: v for k, v in m.items() if v}

    # ---- public API ----

    def _maybe_reload_yaml(self) -> None:
        if not self._yaml_path:
            return
        try:
            mt = os.path.getmtime(self._yaml_path)
        except FileNotFoundError:
            return
        if self._yaml_mtime is None or mt != self._yaml_mtime:
            # only re-merge YAML; keep env overlays
            with self._lock:
                yaml_map = self._load_yaml()
                # rebuild with overlays to keep precedence rules
                base = yaml_map
                base.update(self._load_env_json())
                base.update(self._load_env_vars())
                base.setdefault("default", self._load_default_single().get("default", None))
                self._map = {k: v for k, v in base.items() if v}

    def refresh(self) -> None:
        """Force full reload of YAML + env."""
        with self._lock:
            self._yaml_mtime = None
            self._load_all()

    def get_dsn(self, tenant: Optional[str]) -> str:
        """
        Resolve DSN for a tenant. If tenant is None, try 'default'.
        Raises ValueError if not found; message lists available keys.
        """
        self._maybe_reload_yaml()
        key = (tenant or "default").lower()
        dsn = self._map.get(key)
        if not dsn:
            available = ", ".join(sorted(self._map)) or "(none)"
            raise ValueError(f"No DSN configured for tenant '{tenant}'. Available: {available}")
        return dsn

    def tenants(self) -> Iterable[str]:
        self._maybe_reload_yaml()
        return list(self._map.keys())

_registry = TenantRegistry()

# ------------------------------------------------------------------------------
# Engine/session cache per tenant
# ------------------------------------------------------------------------------

_engine_lock = threading.Lock()
_engines: Dict[str, Engine] = {}
_sessions: Dict[str, sessionmaker] = {}

def _create_engine(dsn: str) -> Engine:
    # Tune pooling for small services; ensure pre_ping to avoid stale connections.
    return create_engine(
        dsn,
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "5")),
        pool_pre_ping=True,
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "300")),
        future=True,
    )

def _get_engine_for_tenant(tenant: str) -> Engine:
    slug = (tenant or "default").lower()
    with _engine_lock:
        if slug in _engines:
            return _engines[slug]
        dsn = _registry.get_dsn(slug)
        engine = _create_engine(dsn)
        _engines[slug] = engine
        _sessions[slug] = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        return engine

def dispose_all_engines() -> None:
    """Call this from your app shutdown to cleanly dispose pooled connections."""
    with _engine_lock:
        for eng in _engines.values():
            try:
                eng.dispose()
            except Exception:
                pass
        _engines.clear()
        _sessions.clear()

# ------------------------------------------------------------------------------
# FastAPI-style dependencies (generators)
# ------------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    Single-tenant fallback dependency.
    Uses DATABASE_URL or TENANT_DSN_MAP['default'].
    Keep this for legacy routes not yet tenant-scoped.
    """
    _get_engine_for_tenant("default")
    SessionLocal = _sessions["default"]
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_tenant_session(tenant: str) -> Generator[Session, None, None]:
    """
    Tenant-aware dependency for routes like:
        @router.get("/tenants/{tenant}/layers")
        def list_layers(tenant: str, db: Session = Depends(get_tenant_session)): ...
    """
    _get_engine_for_tenant(tenant)
    slug = (tenant or "default").lower()
    SessionLocal = _sessions[slug]
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------------------------------------------------------
# Helpers you might use in admin/ops scripts
# ------------------------------------------------------------------------------

def list_tenant_dsns() -> Iterable[Tuple[str, str]]:
    """Return (tenant, dsn) pairs currently configured."""
    return [(t, _registry.get_dsn(t)) for t in sorted(_registry.tenants())]

