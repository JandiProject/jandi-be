from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

import app.models.user_models  # noqa: F401
import app.models.trend_models  # noqa: F401

from app.routers.auth_router import router as auth_router
from app.dependencies.database import Base, engine, init_fields, init_view
from app.routers.platform_router import router as platform_router
from app.routers.jandi_router import router as jandi_router
from app.routers.user_router import router as user_router
from app.routers.ui import router as ui_router
from app.routers.trend_router import router as trend_router

import app.models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    Base.metadata.create_all(bind=engine)
    init_view()
    init_fields()
    yield
    # shutdown
    engine.dispose()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://136.110.239.66:80",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=auth_router)
app.include_router(router=jandi_router)
app.include_router(router=platform_router)
app.include_router(router=user_router)
app.include_router(router=ui_router)
app.include_router(router=trend_router)

@app.get("/")
async def root():
    return {"message": "Jandi Main Server is Running!"}
