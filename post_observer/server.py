import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from app.routers.observer_router import router as observer_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="Post Observer Server")

app.include_router(observer_router)


@app.get("/")
def root() -> dict:
    return {"message": "Post Observer Server is Running!"}
