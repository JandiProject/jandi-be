from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.routers.auth_router import router as auth_router
from app.dependencies.database import Base, engine, init_fields, init_view
from app.routers.platform_router import router as platform_router
from app.routers.jandi_router import router as jandi_router
from app.routers.user_router import router as user_router
from app.routers.ui import router as ui_router
from app.routers.trend_router import router as trend_router
from app.routers.analytics_router import router as analytics_router

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
app.include_router(router=analytics_router)

def _is_analytics_path(request: Request) -> bool:
    """
    analytics API 경로 여부를 반환합니다.

    :param request: FastAPI 요청 객체.
    :return: analytics 경로면 True.
    """
    return request.url.path.startswith("/api/analytics")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTPException 응답 형식을 처리합니다.

    :param request: FastAPI 요청 객체.
    :param exc: 발생한 HTTPException.
    :return: JSON 응답.
    """
    if _is_analytics_path(request):
        detail = exc.detail
        if isinstance(detail, str):
            message = detail
        elif isinstance(detail, dict) and "message" in detail:
            message = str(detail["message"])
        else:
            message = "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": message},
            headers=exc.headers,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    요청 검증 오류 응답 형식을 처리합니다.

    :param request: FastAPI 요청 객체.
    :param exc: 발생한 RequestValidationError.
    :return: JSON 응답.
    """
    if _is_analytics_path(request):
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid request parameters"},
        )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/")
async def root():
    return {"message": "Jandi Main Server is Running!"}
