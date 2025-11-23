from fastapi import FastAPI
from app.routers.auth_router import auth_router
from app.routers.jandi_router import jandi_router
from app.routers.platform_router import platform_router
from app.routers.user_router import user_router

app = FastAPI()
app.include_router(router=auth_router)
app.include_router(router=jandi_router)
app.include_router(router=platform_router)
app.include_router(router=user_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}