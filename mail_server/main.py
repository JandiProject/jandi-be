# mail_server/main.py
#워커진입점, api서버

import uvicorn
from fastapi import FastAPI
import os
import logging
import threading 
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv 

# Pika컨슈머 로직
from .consumer import start_pika_consumer 
from .scheduler_service import (check_and_publish_inactivity,
    check_and_publish_inactivity, 
    init_db_pool,
    close_db_pool 
)


# 환경 변수 로드 (.env 파일 사용)
load_dotenv() 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="Mail Worker API",
    version="1.0.0",
)

scheduler = AsyncIOScheduler()

#fast api이벤트 핸들러
#fast api가 비동기 메인 스레드라 그거 블로킹 안하려고 
#동기 방식인 pika 컨슈머를 별도 백그라운드 스레드로 분리

@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Mail Worker is starting FastAPI server...")

    # Psycopg3 DB Pool 초기화 추가
    await init_db_pool()

    #분리된 백그라운드 스레드로. 
    threading.Thread(target=start_pika_consumer, daemon=True).start()
    logger.info("🔗 RabbitMQ Consumer started in a background thread.")

    #APScheduler 스케줄러 시작
    scheduler.add_job(check_and_publish_inactivity, 'cron', hour=3, minute=0, id='inactivity_check')
    scheduler.start()
    logger.info("⏰ Inactivity check scheduler started.")

#서버 종료 시 호출됨
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Service Stopping...")
    if scheduler.running:
        scheduler.shutdown()
    await close_db_pool()

#상태 확인 엔드포인트
#외부의 로드밸런서가 확인할 수 있다고 함
@app.get("/health", tags=["status"])
async def read_health():
    return {"status": "ok", "message": "Mail Worker is running"}

#프로그램 진입
#uvicorn호출해서 fast api서버와 비동기 이벤트 루프 시작

if __name__ == "__main__":
    #서버구동
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=False 
    )