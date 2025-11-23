# mail_server/email_service.py
# 실제 이메일 전송

import smtplib
import os
from email.mime.text import MIMEText

# SMTP 정보를 환경 변수에서 로드
# 워커가 사용하는 서비스 계정의 자격증명임(발신자)
SMTP_USER = os.getenv("SMTP_USER", "myemail@gmail.com")       
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "abcd efgh ijkl mnop") 
SMTP_SERVER = "smtp.gmail.com"


#실제 smtp전송(consumer.py의 요청 받아서)
def send_email(to_addr: str, subject: str, body: str):

    if not SMTP_USER or not SMTP_PASSWORD:
        print("❌ Cannot send email: SMTP credentials are not available.")
        return False
    
    # Subject:제목\n\n내용 구조로 메시지 입력. 
    msg_string = f"Subject:{subject}\n\n{body}"

    try:
        with smtplib.SMTP(SMTP_SERVER) as connection:
            connection.starttls() # 메시지 암호화 & 보안연결설정
            connection.login(user=SMTP_USER, password=SMTP_PASSWORD)
            connection.sendmail(
                from_addr=SMTP_USER, 
                to_addrs=to_addr, 
                msg=msg_string 
            )
        print(f"✅ Email sent successfully to {to_addr}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_addr}: {e}")
        return False