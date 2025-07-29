from sqlalchemy import Column, DateTime, func, Integer, String, Boolean, Text, JSON, Float
from app.database import Base

class Layer(Base):
    __tablename__ = "layers"

    id = Column(Integer, primary_key=True, index=True)
    viewer_id = Column(Integer)
    type = Column(String)
    name = Column(String)
    title = Column(String)
    url = Column(String)
    layer_name = Column(String)
    version = Column(String)
    crs = Column(String)
    style = Column(String)
    format = Column(String)
    tiled = Column(Boolean)
    opacity = Column(Float)
    visible = Column(Boolean)
    min_zoom = Column(Integer)
    max_zoom = Column(Integer)
    sort_order = Column(Integer)
    layer_params = Column(JSON)
    extra_config = Column(JSON)
    bbox = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

