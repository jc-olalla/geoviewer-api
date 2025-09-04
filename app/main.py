# app/main.py
from __future__ import annotations

from app.routes.config import router as config_router
from app.routes.layers import router as layers_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Geoviewer Viewer API")

# (optional) CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://geoviewer-app.onrender.com"],  # adjust
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# mount routers
app.include_router(layers_router, prefix="/tenants/{tenant}/layers", tags=["layers"])
app.include_router(config_router, prefix="/tenants/{tenant}/config", tags=["config"])
# app.include_router(users_router, prefix="/tenants/{tenant}/users", tags=["users"])
# app.include_router(viewers_router, prefix="/tenants/{tenant}/viewers", tags=["viewers"])


# quick health check
@app.get("/healthz")
def health():
    return {"ok": True}
