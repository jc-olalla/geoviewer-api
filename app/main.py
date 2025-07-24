from fastapi import FastAPI
from app.api.routes import router
from dotenv import load_dotenv

load_dotenv()  # Load .env

app = FastAPI()
app.include_router(router)

