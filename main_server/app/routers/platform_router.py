import jwt
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import os
from app.dependencies.database import get_db
from app.models.user_models import UserPlatform, Platform, UserPlatformRequest
from app.models.post_models import Posts
from app.dependencies.verify_jwt import get_current_user_id
from app.parsers.velog import VelogRSSParser
from app.parsers.naver import NaverRSSParser
from app.parsers.tistory import TistoryRSSParser
from app.dependencies.rabbitmq import publish_message
from app.models.schemas import ArticleSchema
import time
import logging
from datetime import datetime, timedelta
from app.parsers.rss_service import fetch_rss
from typing import List

logger = logging.getLogger(__name__)
PLATFORM_VERIFY_SECRET = os.getenv("PLATFORM_VERIFY_SECRET", "jandi-secret-key")

router = APIRouter(
    prefix="/api/platform",
    tags=["Platform"]
)

platform_register_map = {
    "velog": VelogRSSParser(),
    "naver": NaverRSSParser(),
    "tistory": TistoryRSSParser()
}

@router.put("")
def register_platform(
    req: UserPlatformRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
    ):
    platform_info = db.query(Platform).filter(Platform.name == req.platform_name).first()
    
    if not platform_info:
        raise HTTPException(status_code=404, detail=f"지원하지 않는 플랫폼: {req.platform_name}")

    is_verified = verify_ownership_via_post_title(
        platform_name=req.platform_name,
        account_id=req.account_id,
        expected_user_id=user_id,
        expected_platform_id=platform_info.platform_id
    )

    if not is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="블로그 소유권 인증에 실패했습니다. 제목에 인증 코드가 포함된 글을 올렸는지 확인해주세요."
        )
    
    existing_mapping = db.query(UserPlatform).filter(
        UserPlatform.user_id == user_id,
        UserPlatform.platform_id == platform_info.platform_id
    ).first()

    # 3. Upsert
    if existing_mapping:
        existing_mapping.account_id = req.account_id
        message = "업데이트 및 인증 완료"
    else:
        new_mapping = UserPlatform(
            user_id=user_id,
            platform_id=platform_info.platform_id,
            account_id=req.account_id,
            last_upload=None
        )
        db.add(new_mapping)
        message = "등록 및 인증 완료"

    db.commit()

    articles = platform_register_map[req.platform_name].parse(req.account_id)
    data = []
    for article in articles:
        data.append({
            "link": article.link,
            "published_at": article.published_at,
            "title": article.title,
            "user_id": user_id,
            "platform": req.platform_name
        })

    # publish_message("platform_register", data)

    return {
        "message": message
    }

@router.delete("")
def delete_platform(
    req: UserPlatformRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
    ):
    try: 
        platform_info = db.query(Platform).filter(Platform.name == req.platform_name).first()
        
        if not platform_info:
            raise HTTPException(status_code=404, detail=f"지원하지 않는 플랫폼: {req.platform_name}")

        existing_mapping = db.query(UserPlatform).filter(
            UserPlatform.user_id == user_id,
            UserPlatform.platform_id == platform_info.platform_id
        ).first()

        existing_posts = db.query(Posts).filter(
            Posts.user_id == user_id,
            Posts.platform_id == platform_info.platform_id
        ).all()

        if not existing_mapping:
            raise HTTPException(status_code=404, detail="플랫폼이 등록되어 있지 않습니다.")

        for post in existing_posts:
            db.delete(post)
        db.delete(existing_mapping)
        db.commit()
        db.execute(text('REFRESH MATERIALIZED VIEW "USER_STAT"'))
        db.execute(text('REFRESH MATERIALIZED VIEW "POST_AGG"'))
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"플랫폼 삭제 중 오류 발생: {e}")

    return {
        "message": "삭제 완료"
    }

@router.get("")
def get_platforms(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
    ):
    user_platforms = db.query(UserPlatform, Platform).filter(UserPlatform.platform_id == Platform.platform_id, UserPlatform.user_id == user_id).all()
    res = []
    for user_platform, platform in user_platforms:
        res.append({
            "platform_name": platform.name,
            "account_id": user_platform.account_id,
            "last_upload": user_platform.last_upload
        })
    return res

def generate_token(user_id: str, platform_id: int):
    payload = {
        "user_id": str(user_id),
        "platform_id": str(platform_id),
        "exp": datetime.utcnow() + timedelta(hours=1) 
    }
    return jwt.encode(payload, PLATFORM_VERIFY_SECRET, algorithm="HS256")

@router.get("/token")
def show_token(
    platform_name: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """사용자에게 블로그에 올릴 인증 토큰을 발급"""
    platform_info = db.query(Platform).filter(Platform.name == platform_name).first()
    if not platform_info:
        raise HTTPException(status_code=404, detail="지원하지 않는 플랫폼")
    
    token = generate_token(user_id, platform_info.platform_id)
    
    return {
        "verification_token": f"JANDI-AUTH-{token}",
        "instructions": "이 코드를 블로그 소개글(Bio)에 붙여넣고 인증 버튼을 눌러주세요."
    }

def verify_ownership_via_post_title(
    platform_name: str, 
    account_id: str, 
    expected_user_id: str,
    expected_platform_id: int
) -> bool:
    """
    사용자의 최근 게시글 제목을 확인하여 블로그 소유권을 검증합니다.
    """
    articles: List[ArticleSchema] = fetch_rss(platform_name, account_id)
    
    if not articles:
        logger.warning(f"검증 실패: {platform_name}/{account_id} 에서 게시글을 찾을 수 없습니다.")
        return False

    auth_prefix = "JANDI-AUTH-"
    
    for article in articles[:3]:  # 최근 3개의 글까지 확인
        logger.info(f"검사 중인 제목: {article.title}")
        if auth_prefix in article.title:
            try:             
                start_idx = article.title.find(auth_prefix) + len(auth_prefix)
                token = article.title[start_idx:].split()[0].strip()
                logger.info(f"추출된 토큰: {token[:10]}...") # 보안상 앞부분만 출력

                decoded = jwt.decode(
                    token, 
                    PLATFORM_VERIFY_SECRET, 
                    algorithms=["HS256"]
                )
 
                if (str(decoded.get("user_id")) == str(expected_user_id) and 
                    str(decoded.get("platform_id")) == str(expected_platform_id)):
                    logger.info(f"검증 성공: 유저 {expected_user_id} 가 {platform_name} 소유권을 증명함.")
                    return True
                
            except jwt.ExpiredSignatureError:
                logger.error("검증 에러: 인증 토큰의 시간이 만료되었습니다.")
            except jwt.InvalidTokenError:
                logger.error("검증 에러: 유효하지 않은 JWT 토큰입니다.")
            except Exception as e:
                logger.error(f"검증 에러: 토큰 처리 중 알 수 없는 오류 발생: {e}")

    logger.warning(f"검증 실패: 유효한 인증 코드가 제목에 포함된 글을 찾을 수 없습니다.")
    return False