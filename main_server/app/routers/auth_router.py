# app/routers/auth_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import jwt
import os
from app.dependencies.database import get_db
from app.services.email_service import send_verification_email
from app.models.user_models import User, AuthUser
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from app.schemas.auth_schemas import SignUpRequest, SignInRequest, SignInResponse
from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/signup")
async def signup(data: SignUpRequest, db: Session = Depends(get_db)):

    """
    회원가입 API 엔드포인트

    :param data: JSON 요청 바디 데이터
    :type data: SignUpRequest
    :param db: DB 세션 주입
    :type db: Session
    :return: 회원가입 처리 결과
    :rtype: dict
    """

    repo = AuthRepository(db)
    service = AuthService(repo)
    return await service.register_new_user(data)

@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):

    """
    이메일 인증 토큰을 검증하여 계정을 활성화.

    사용자가 메일로 받은 링크를 클릭했을 때 호출되며, 토큰이 유효하면 
    AuthUser의 인증 상태를 완료로 변경하고 통계 뷰를 갱신.

    :param token: 이메일에 포함된 JWT 인증 토큰
    :type token: str
    :param db: 데이터베이스 세션 (Depends를 통해 주입)
    :type db: Session
    :return: 인증 완료 메시지
    :rtype: dict
    """

    repo = AuthRepository(db)
    service = AuthService(repo)
    return service.verify_email(token)

@router.post("/signin")
def signin(data: SignInRequest, db: Session = Depends(get_db)):

    """
    사용자 로그인을 처리하고 액세스 토큰을 발급.

    이메일과 비밀번호를 검증하고, 모든 조건(계정 존재, 비밀번호 일치, 이메일 인증 완료)이 
    충족되면 향후 API 요청에 사용할 JWT 액세스 토큰을 반환.

    :param data: 로그인 요청 정보 (이메일, 비밀번호)
    :type data: SignInRequest
    :param db: 데이터베이스 세션 (Depends를 통해 주입)
    :type db: Session
    :return: 발급된 액세스 토큰 정보
    :rtype: dict
    """

    repo = AuthRepository(db)
    service = AuthService(repo)
    return service.sign_in(data)