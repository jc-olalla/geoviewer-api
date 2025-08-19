# === app/providers/credentials.py ===
from __future__ import annotations
import base64
from dataclasses import dataclass
import os
from typing import Dict, Mapping, Optional, Tuple

# ---------------------------------------------------------------------------
# Server‑side credentials for PROXY layers only
# ---------------------------------------------------------------------------
# Your catalog/API should never leak secrets to the browser. For layers that
# require secrets (e.g., Basic/Bearer/API‑key), you set Access.mode=PROXY and
# have your API talk to the upstream provider. This module helps attach those
# secrets to outgoing server‑side HTTP requests.
# ---------------------------------------------------------------------------


class Credentials:
    """Base credential that can apply itself to headers/query params.

    Implementations MUST NOT expose secrets in __repr__ / __str__.
    """

    def apply(self, headers: Dict[str, str], params: Dict[str, str]) -> None:
        raise NotImplementedError


@dataclass
class BearerToken(Credentials):
    token: str

    def apply(self, headers: Dict[str, str], params: Dict[str, str]) -> None:
        headers["Authorization"] = f"Bearer {self.token}"

    def __repr__(self) -> str:
        return "BearerToken(token=***redacted***)"


@dataclass
class BasicAuth(Credentials):
    username: str
    password: str

    def apply(self, headers: Dict[str, str], params: Dict[str, str]) -> None:
        userpass = f"{self.username}:{self.password}".encode("utf-8")
        headers["Authorization"] = "Basic " + base64.b64encode(userpass).decode("ascii")

    def __repr__(self) -> str:
        return f"BasicAuth(username={self.username!r}, password=***redacted***)"


@dataclass
class ApiKeyHeader(Credentials):
    header_name: str
    value: str

    def apply(self, headers: Dict[str, str], params: Dict[str, str]) -> None:
        headers[self.header_name] = self.value

    def __repr__(self) -> str:
        return f"ApiKeyHeader(header_name={self.header_name!r}, value=***redacted***)"


@dataclass
class ApiKeyQuery(Credentials):
    param_name: str
    value: str

    def apply(self, headers: Dict[str, str], params: Dict[str, str]) -> None:
        params[self.param_name] = self.value

    def __repr__(self) -> str:
        return f"ApiKeyQuery(param_name={self.param_name!r}, value=***redacted***)"


@dataclass(frozen=True)
class AuthConfig:
    """Config describing HOW to auth to a datasource (no secrets here).

    kind: one of "bearer", "basic", "api_key_header", "api_key_query".
    ref:  alias to locate actual secrets in the environment (e.g., WFS_PROD).

    You can override default env var names via explicit *_env fields if desired.
    """

    kind: str
    ref: Optional[str] = None

    # For bearer
    token_env: Optional[str] = None  # e.g. "SECRET_SUPABASE_SERVICE_KEY"

    # For basic
    username_env: Optional[str] = None
    password_env: Optional[str] = None

    # For API key in header/query
    header: Optional[str] = None  # e.g. "X-API-Key"
    query_param: Optional[str] = None  # e.g. "key"
    value_env: Optional[str] = None  # env var holding the key value


class CredentialsResolver:
    """Resolve concrete credentials from environment variables.

    Resolution rules (in order):
    - If explicit *_env names are provided, read them.
    - Else if a ref is provided, use sensible defaults based on the kind:
        * bearer:   SECRET_<REF>_TOKEN or SECRET_<REF>_KEY
        * basic:    SECRET_<REF>_USER and SECRET_<REF>_PASS
        * api_key_: SECRET_<REF>_KEY (and header/query name must be provided)
    - Else raise ValueError with a helpful message.
    """

    def __init__(self, env: Optional[Mapping[str, str]] = None) -> None:
        self._env: Mapping[str, str] = env or os.environ

    def resolve(self, cfg: AuthConfig):
        kind = cfg.kind.lower()
        if kind == "bearer":
            token = self._get_token(cfg)
            return BearerToken(token)
        if kind == "basic":
            username, password = self._get_basic(cfg)
            return BasicAuth(username, password)
        if kind == "api_key_header":
            if not cfg.header:
                raise ValueError("api_key_header requires 'header' name in AuthConfig")
            value = self._get_value(cfg)
            return ApiKeyHeader(cfg.header, value)
        if kind == "api_key_query":
            if not cfg.query_param:
                raise ValueError(
                    "api_key_query requires 'query_param' name in AuthConfig"
                )
            value = self._get_value(cfg)
            return ApiKeyQuery(cfg.query_param, value)
        raise ValueError(f"Unsupported auth kind: {cfg.kind}")

    # ---- internals ----
    def _get_token(self, cfg: AuthConfig) -> str:
        if cfg.token_env and (val := self._env.get(cfg.token_env)):
            return val
        if cfg.ref:
            for suffix in ("TOKEN", "KEY"):
                name = f"SECRET_{cfg.ref}_{suffix}"
                if val := self._env.get(name):
                    return val
        raise ValueError("Bearer token not found in environment for given AuthConfig")

    def _get_basic(self, cfg: AuthConfig) -> Tuple[str, str]:
        user = self._env.get(cfg.username_env) if cfg.username_env else None
        pw = self._env.get(cfg.password_env) if cfg.password_env else None
        if user and pw:
            return user, pw
        if cfg.ref:
            user = self._env.get(f"SECRET_{cfg.ref}_USER")
            pw = self._env.get(f"SECRET_{cfg.ref}_PASS")
            if user and pw:
                return user, pw
        raise ValueError(
            "Basic auth credentials not found in environment for given AuthConfig"
        )

    def _get_value(self, cfg: AuthConfig) -> str:
        if cfg.value_env and (val := self._env.get(cfg.value_env)):
            return val
        if cfg.ref and (val := self._env.get(f"SECRET_{cfg.ref}_KEY")):
            return val
        raise ValueError("API key value not found in environment for given AuthConfig")
