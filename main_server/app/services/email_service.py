#로그인 인증 메일 발송
#fastapi-mail 사용
# app/internal/email_service.py

import os
from dotenv import load_dotenv
from email.message import EmailMessage
import aiosmtplib
from app.templates.email_templates import get_verification_html, get_password_reset_html, get_verify_success_page_html

load_dotenv()

# env에서 읽어옴
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")            
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")   
FRONTEND_URL = "http://136.110.239.66"
MAIL_FROM = os.getenv("MAIL_FROM", SMTP_USER)  

async def _send_email(to_email: str, subject: str, html_body: str, plain_body: str) -> None:
    """
    공통 메일 발송 처리 함수 (내부 전용).

    :param to_email: 수신자 이메일 주소
    :param subject: 메일 제목
    :param html_body: HTML 형식의 메일 본문
    :param plain_body: 텍스트 형식의 메일 본문
    :raises RuntimeError: SMTP 설정이 누락되었을 경우 발생
    :raises Exception: 메일 발송 중 발생하는 네트워크 및 SMTP 오류
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError("SMTP_USER 또는 SMTP_PASSWORD가 설정되지 않았습니다. .env를 확인하세요.")

    msg = EmailMessage()
    msg["From"] = MAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
        )
    except Exception:
        raise

async def send_verification_email(email: str, token: str) -> None:
    """이메일 인증 메일 발송 로직"""
    verify_url = f"{FRONTEND_URL.rstrip('/')}/api/auth/verify-email?token={token}"
    
    subject = "[잔디] 이메일 인증 요청"
    html_body = get_verification_html(verify_url) # 템플릿 호출
    plain_body = f"이메일 인증 링크: {verify_url}"
    
    await _send_email(email, subject, html_body, plain_body)

async def send_password_reset_email(email: str, token: str) -> None:
    """비밀번호 재설정 메일 발송 로직"""
    reset_url = f"{FRONTEND_URL.rstrip('/')}/password-reset?token={token}"
    
    subject = "[잔디] 비밀번호 재설정 안내"
    html_body = get_password_reset_html(reset_url) # 템플릿 호출
    plain_body = f"비밀번호 재설정 링크: {reset_url}"
    
    await _send_email(email, subject, html_body, plain_body)
