# mail_server/consumer.py
# pika 컨슈머

import pika
import os
import json
from mail_server import email_service
import time

# 환경 변수에서 RabbitMQ 접속 정보 로드
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = os.getenv('RABBITMQ_PORT', 5672)
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')
EMAIL_QUEUE_NAME = "mail_send_queue"


# 메시지 수신 콜백 함수
#메시지 1개 도착할 때마다 pika라이브러리 떄문에 자동 호출됨
#수신된 바이트 데이터 파싱해서 email_service호출
def callback(ch, method, properties, body):
    print("--- 📥 Received Message ---")
    try:
        message_data = json.loads(body.decode())
        recipient = message_data.get("recipient")
        subject = message_data.get("subject", "자동 알림")
        body_content = message_data.get("body", "내용 없음")

        if recipient:
            email_service.send_email(recipient, subject, body_content)
        else:
            print("❗ Recipient not specified in message.")

    except json.JSONDecodeError:
        print(f"🚨 Error decoding JSON: {body}")
    except Exception as e:
        print(f"🔥 An unexpected error occurred: {e}")
    finally:
        print("--- ✅ Message Processed ---")
    return

# pika연결 & 구독시작
#메인의 startup이벤트에서 별도 백그라운드 스레드로 호출됨
#워커기능활성화

def start_pika_consumer():
    print("👂 Pika Consumer thread starting...")

    global pika_connection

    # RabbitMQ URL 구성
    url = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/%2f"
    
    # 주의: Pika의 BlockingConnection은 스레드 내에서만 안전하다고 함
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel() 

        # 큐를 선언
        channel.queue_declare(queue=EMAIL_QUEUE_NAME, durable=True)
        
        # 구독 설정
        channel.basic_consume(
            queue=EMAIL_QUEUE_NAME,
            on_message_callback=callback,
            auto_ack=True
        )

        print(f"👂 Worker is consuming messages on {EMAIL_QUEUE_NAME}...")

        # 이 함수가 이 스레드를 블로킹(대기 유지)하고 무한 루프 돌게 함
        #-> 워커 프로세스 죽지 않게 유지하며 실시간으로 메시지 받아 처리하기 위해
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        print(f"❌ Error connecting to RabbitMQ: {e}. Retrying in 5s...")
        time.sleep(5)
    except KeyboardInterrupt:
        print("🛑 Pika Consumer thread stopped manually.")
    except Exception as e:
        print(f"🔥 Fatal error in consumer thread: {e}")
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close()