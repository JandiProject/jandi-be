"""플랫폼(네이버 등) 연동용 메일 발송."""

import os

import aiosmtplib
from dotenv import load_dotenv
from email.message import EmailMessage

from app.services import email_service as _mail

load_dotenv()

PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "http://127.0.0.1:8000")


async def send_naver_platform_verification_email(email: str, verify_token: str) -> None:
    if not _mail.SMTP_USER or not _mail.SMTP_PASSWORD:
        raise RuntimeError("SMTP_USER 또는 SMTP_PASSWORD가 설정되지 않았습니다. .env를 확인하세요.")

    verify_url = f"{PUBLIC_API_URL.rstrip('/')}/api/platform/verification/naver?token={verify_token}"

    html_body = f"""
    <html>
      <body>
        <h3>네이버 블로그 연동 인증</h3>
        <p>아래 버튼을 클릭하면 블로그 소유 확인이 완료됩니다.</p>
        <p>
          <a href="{verify_url}"
             style="display:inline-block;padding:10px 20px;background:#03C75A;color:white;text-decoration:none;">
             네이버 블로그 인증하기
          </a>
        </p>
        <p style="font-size:12px;color:#666;">링크가 동작하지 않으면 다음 주소를 브라우저에 붙여 넣으세요:<br/>{verify_url}</p>
      </body>
    </html>
    """

    plain_body = f"네이버 블로그 연동 인증: {verify_url}"

    msg = EmailMessage()
    msg["From"] = _mail.MAIL_FROM
    msg["To"] = email
    msg["Subject"] = "네이버 블로그 연동 인증 메일"
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

    await aiosmtplib.send(
        msg,
        hostname=_mail.SMTP_SERVER,
        port=_mail.SMTP_PORT,
        start_tls=True,
        username=_mail.SMTP_USER,
        password=_mail.SMTP_PASSWORD,
    )
