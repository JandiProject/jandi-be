from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .routers.auth_router import router as auth_router
from .dependencies.database import Base, engine
from .routers.platform_router import router as platform_router
from .routers.jandi_router import router as jandi_router
from .routers.user_router import router as user_router
from .routers.ui import router as ui_router

import dotenv
dotenv.load_dotenv('../.env')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
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
app.include_router(user_router)
app.include_router(ui_router)

@app.get("/")
async def root():
    return {"message": "Jandi Main Server is Running!"}
