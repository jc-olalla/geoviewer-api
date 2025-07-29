from fastapi import FastAPI
from app.routes import layers
from app.database import engine
from app.models import models

# Create database tables (if using SQLAlchemy ORM)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Include router
app.include_router(layers.router, prefix="/layers", tags=["Layers"])

