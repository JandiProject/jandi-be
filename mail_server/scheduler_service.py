# scheduler_service.py (새 파일)
import asyncio
import os
import json
import pika # 메시지 발행은 Pika 동기 클라이언트 사용
import asyncpg # 비동기 DB 접근
import time

# 환경 변수 로드
DB_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@host:5432/db")
MQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
MQ_PORT = os.getenv('RABBITMQ_PORT', 5672)
MQ_USER = os.getenv('RABBITMQ_USER', 'guest')
MQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')
EMAIL_QUEUE_NAME = "mail_send_queue"

# ERD 기반 쿼리: 최근 7일 동안 POSTS 테이블에 글을 작성하지 않은 사용자 목록 조회
SQL_QUERY = """
SELECT 
    u.email
FROM 
    "user" u  
LEFT JOIN 
    posts p 
    ON u.user_id = p.user_id 
    AND p.date >= NOW() - INTERVAL '7 days'  -- [ERD 반영] POSTS.date 사용
WHERE 
    p.user_id IS NULL;  -- 7일 내 게시물이 없는 사용자 필터링
"""

#db에서 7일 이상 미작성 사용자를 조회하고 rabbit mq에 메일 발송 메시지 발행
#apscheduler에 의해 비동기적으로 호출됨
async def check_and_publish_inactivity():
    # 1. DB 연결 및 쿼리 (비동기)
    print("⏰ Starting inactivity check...")
    conn = None
    
    # 7일 이상 미작성 사용자 이메일 목록 조회 (위의 SQL 쿼리 사용)
    inactive_users = await conn.fetchval(SQL_QUERY) 
    await conn.close()
    
    try:
        # 1. DB 연결 및 쿼리 (비동기)
        conn = await asyncpg.connect(DB_URL)
        inactive_users_records = await conn.fetch(SQL_QUERY)
        
        # 2. RabbitMQ 메시지 발행 (동기 Pika는 발행 시 성능 문제가 적어 직접 사용)
        mq_url = f"amqp://{MQ_USER}:{MQ_PASS}@{MQ_HOST}:{MQ_PORT}/%2f"
        params = pika.URLParameters(mq_url)
        
        # 발행은 트랜잭션이 짧으므로 BlockingConnection을 사용하고 바로 닫기
        mq_conn = pika.BlockingConnection(params)
        channel = mq_conn.channel()
        channel.queue_declare(queue=EMAIL_QUEUE_NAME, durable=True)
        
        published_count = 0
        for record in inactive_users_records:
            email = record['email']
            message = {
                "recipient": email,
                "subject": "활동 재개를 위한 알림",
                "body": f"안녕하세요, {email}님. 일주일 넘게 활동이 없어 알려드립니다. 새로운 글을 작성해보세요!"
            }
            channel.basic_publish(exchange='', routing_key=EMAIL_QUEUE_NAME, body=json.dumps(message))
            published_count += 1
        
        mq_conn.close()
        print(f"✅ Inactivity check complete. Published {published_count} messages.")

    except Exception as e:
        print(f"❌ Failed to run scheduled task (DB/MQ Error): {e}")
    finally:
        if conn:
            await conn.close()