"""
개발용: 이메일 인증 완료 상태의 USER + AUTH_USER 한 세트 삽입.
실행: docker compose exec -T main-server python scripts/seed_verified_user.py

환경변수(선택):
  SEED_EMAIL   기본 dev@local.test
  SEED_NAME    기본 Dev
  SEED_PASSWORD 기본 testpass
"""
import os

from passlib.context import CryptContext
from sqlalchemy import create_engine, text

EMAIL = os.getenv("SEED_EMAIL", "dev@gmail.com")
NAME = os.getenv("SEED_NAME", "Dev")
PASSWORD = os.getenv("SEED_PASSWORD", "testpass")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL is not set")

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto").hash(PASSWORD)
engine = create_engine(DATABASE_URL)

sql = text(
    """
    WITH u AS (
      INSERT INTO "USER" (user_id, email, name, created_at, is_public, notify_email)
      VALUES (gen_random_uuid(), :email, :name, NOW(), false, false)
      RETURNING user_id
    )
    INSERT INTO "AUTH_USER" (auth_id, user_id, email, hashed_password, is_verified, verification_token)
    SELECT gen_random_uuid(), user_id, :email, :hpw, true, NULL
    FROM u
    """
)

with engine.begin() as conn:
    conn.execute(sql, {"email": EMAIL, "name": NAME, "hpw": pwd})

print(f"OK: {EMAIL} / password={PASSWORD!r} (is_verified=true)")
