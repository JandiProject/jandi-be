from sqlalchemy import UUID, Column, text
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.post_models import Posts
from app.models.user_models import Platform, UserPlatform
from app.parsers.naver import NaverRSSParser
from app.parsers.tistory import TistoryRSSParser
from app.parsers.velog import VelogRSSParser
from app.repositories.platform_repository import PlatformRepository

def get_platform_info(db, platform_name: str):
    """
    플랫폼 이름을 기반으로 플랫폼 정보를 조회하는 함수
    플랫폼이 존재하면 그 정보를 반환하고, 존재하지 않으면 404 에러를 발생시킴
    """
    platform_repository = PlatformRepository(db)
    platform_info = platform_repository.get_platform_by_name(platform_name)
    
    # 플랫폼이 존재하지 않으면 404 에러 반환
    if not platform_info:
        raise HTTPException(status_code=404, detail=f"지원하지 않는 플랫폼: {platform_name}")
    return platform_info

def add_user_platform_mapping(db: Session, user_id: str, platform_id: Column, account_id: str):
    """
    유저와 플랫폼 간의 매핑을 추가하는 함수
    """
    # 이미 매핑이 존재하는지 확인
    platform_repository = PlatformRepository(db)
    existing_mapping: UserPlatform = platform_repository.get_user_platform_mapping(user_id, platform_id)
    
    # 매핑이 이미 존재하면 업데이트, 그렇지 않으면 새 매핑 생성
    if existing_mapping:
        platform_repository.update_user_platform_account(existing_mapping, account_id)
        db.commit()
        return
    
    # 새로운 매핑 생성
    platform_repository.create_user_platform_mapping(user_id, platform_id, account_id)
    db.commit()

def make_article_data(data, platform_name, account_id, user_id):
    # TODO: 메인 서버에서 파싱 로직을 처리하는 것은 분리하는 게 좋을 것 같음 (이 함수 안 쓰는 게 목표)

    platform_register_map = {
    "velog": VelogRSSParser(),
    "naver": NaverRSSParser(),
    "tistory": TistoryRSSParser()
    }

    try:
        articles = platform_register_map[platform_name].parse(account_id)
    except:
        raise HTTPException(status_code=400)

    for article in articles:
        data.append({
            "link": article.link,
            "published_at": article.published_at,
            "title": article.title,
            "user_id": user_id,
            "platform": platform_name
        })
    return data

def delete_user_platform_mapping(logger, db: Session, user_id: str, platform_id: Column, platform_name: str):
    """
    유저와 플랫폼 간의 매핑을 삭제하는 함수
    """

    try:
        platform_repository = PlatformRepository(db)
        existing_mapping = platform_repository.get_user_platform_mapping(user_id, platform_id)
        
        if not existing_mapping:
            raise HTTPException(status_code=404, detail="플랫폼이 등록되어 있지 않습니다.")

        existing_posts = platform_repository.get_posts_by_user_and_platform(user_id, platform_id)


        for post in existing_posts:
            platform_repository.delete_post(post)
        platform_repository.delete_user_platform_mapping(existing_mapping)
        # 삭제는 먼저 확정한다. 이후 Materialized View 갱신 실패가 나도 삭제 자체는 성공으로 본다.
        db.commit()

        try:
            db.execute(text('REFRESH MATERIALIZED VIEW "USER_STAT"'))
            db.execute(text('REFRESH MATERIALIZED VIEW "POST_AGG"'))
            db.commit()
        except Exception:
            db.rollback()
            logger.exception(
                    "Materialized view refresh failed after platform delete (user_id=%s, platform=%s)",
                    user_id,
                    platform_name,
                )
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("플랫폼 삭제 중 오류 발생")
        raise HTTPException(status_code=500, detail="플랫폼 삭제 처리 중 서버 오류가 발생했습니다.")

def get_user_platforms(db: Session, user_id: str):
    """
    유저가 등록한 플랫폼 정보를 조회하는 함수
    """
    platform_repository = PlatformRepository(db)
    user_platforms = platform_repository.get_user_platforms_with_platform(user_id)
    res = []
    for user_platform, platform in user_platforms:
        res.append({
            "platform_name": platform.name,
            "account_id": user_platform.account_id,
            "last_upload": user_platform.last_upload
        })
    return res