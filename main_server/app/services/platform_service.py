import logging
import uuid
from sqlalchemy import Column, text
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.platform_models import UserPlatformVerification
from app.models.platform_models import Platform, UserPlatform
from app.models.user_models import User, AuthUser
from app.parsers.naver import NaverRSSParser
from app.parsers.tistory import TistoryRSSParser
from app.parsers.velog import VelogRSSParser
from app.repositories.platform_repository import PlatformRepository
from app.services.email_service import FRONTEND_URL
from app.services.platform_email import send_naver_platform_verification_email

logger = logging.getLogger(__name__)


def get_platform_info(db: Session, platform_name: str) -> Platform:
    """
    플랫폼 이름을 기반으로 플랫폼 정보를 조회하는 함수
    플랫폼이 존재하면 그 정보를 반환하고, 존재하지 않으면 404 에러를 발생시킴
    """
    platform_repository = PlatformRepository(db)
    platform_info = platform_repository.get_platform_by_name(platform_name)

    # 플랫폼이 존재하지 않으면 404 에러 반환
    if not platform_info:
        raise HTTPException(
            status_code=404, detail=f"지원하지 않는 플랫폼: {platform_name}"
        )
    return platform_info

def add_user_platform_mapping(
    db: Session, user_id: str, platform_id: Column, account_id: str, *, commit: bool = True
):
    """
    유저와 플랫폼 간의 매핑을 추가하는 함수
    """
    platform_repository = PlatformRepository(db)
    existing_mapping: UserPlatform|None = platform_repository.get_user_platform_mapping(
        user_id, platform_id
    )

    # 매핑이 이미 존재하면 업데이트, 그렇지 않으면 새 매핑 생성
    if existing_mapping:
        platform_repository.update_user_platform_account(existing_mapping, account_id)
        if commit:
            db.commit()
        return

    # 새로운 매핑 생성
    platform_repository.create_user_platform_mapping(user_id, platform_id, account_id)
    db.commit()


# def make_article_data(
#     platform_name: str, account_id: str, user_id: str
# ) -> PlatformRegisterMessage:
#     # TODO: 메인 서버에서 파싱 로직을 처리하는 것은 분리하는 게 좋을 것 같음 (이 함수 안 쓰는 게 목표)

#     platform_register_map = {
#         "velog": VelogRSSParser(),
#         "naver": NaverRSSParser(),
#         "tistory": TistoryRSSParser(),
#     }

#     try:
#         articles = platform_register_map[platform_name].parse(account_id)
#     except Exception:
#         raise HTTPException(status_code=400)

#     message_items: list[PlatformRegisterArticleMessage] = []
#     for article in articles:
#         message_items.append(
#             PlatformRegisterArticleMessage(
#                 link=article.link,
#                 published_at=article.published_at,
#                 user_id=user_id,
#                 platform=platform_name,
#             )
#         )

#     return PlatformRegisterMessage(message_items)


def delete_user_platform_mapping(
    db: Session, user_id: str, platform_id: Column, platform_name: str
):
    """
    유저와 플랫폼 간의 매핑을 삭제하는 함수
    """

    try:
        platform_repository = PlatformRepository(db)
        existing_mapping = platform_repository.get_user_platform_mapping(
            user_id, platform_id
        )

        if not existing_mapping:
            raise HTTPException(
                status_code=404, detail="플랫폼이 등록되어 있지 않습니다."
            )

        existing_posts = platform_repository.get_posts_by_user_and_platform(
            user_id, platform_id
        )

        for post in existing_posts:
            platform_repository.delete_post(post)
        platform_repository.delete_user_platform_mapping(existing_mapping)
        # 삭제는 먼저 확정한다. 이후 Materialized View 갱신 실패가 나도 삭제 자체는 성공으로 본다.
        db.commit()
        try:
            platform_repository.refresh_materialized_view()
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
        raise HTTPException(
            status_code=500, detail="플랫폼 삭제 처리 중 서버 오류가 발생했습니다."
        )


def get_user_platforms(db: Session, user_id: str) -> list[dict]:
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
        })
    return res

def get_user_verification_token(db: Session, user_id: str, platform_name: str) -> str:
    """
    18번 명세: 외부 파드(크롤러)에 보낼 토큰 값만 가져오기
    """
    platform_repository = PlatformRepository(db)
    platform_info = get_platform_info(db, platform_name)
    
    token_record = platform_repository.get_verification_token(user_id, platform_info.platform_id)
    
    if not token_record:
        return None
        
    return token_record.token

def update_verification_status(db: Session, user_id: str, platform_name: str, account_id: str):
    """
    인증 성공 시
    1) 임시 테이블(Verification)에서 레코드 조회
    2) 정식 테이블(UserPlatform)에 추가 또는 업데이트
    3) 임시 테이블 레코드 삭제 (Transaction)
    """
    platform_repository = PlatformRepository(db)
    platform_info = get_platform_info(db, platform_name)

    verification_record = platform_repository.get_verification_token(
        user_id,
        platform_info.platform_id,
    )

    if not verification_record:
        raise HTTPException(status_code=404, detail="인증 시도 기록이 없습니다.")

    try:
        add_user_platform_mapping(
            db=db,
            user_id=user_id,
            platform_id=platform_info.platform_id,
            account_id=account_id,
            commit=False,
        )

        platform_repository.delete_verification_record(verification_record)
        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"인증 상태 업데이트 중 오류: {e}")
        raise HTTPException(status_code=500, detail="인증 처리 중 서버 오류 발생")
    
def get_tistory_token_logic(db: Session, user_id: str, account_id: str) -> str:
    """티스토리 인증용 헤더 문자열 발급 및 중복 검사."""
    platform_repository = PlatformRepository(db)
    platform_info = platform_repository.get_platform_by_name("tistory")

    if not platform_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="티스토리 플랫폼 정보가 없습니다.")

    if platform_repository.get_user_platform_mapping(user_id, platform_info.platform_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 등록된 티스토리 계정이 있습니다.",
        )

    if platform_repository.get_user_platform_by_platform_and_account(
        platform_info.platform_id, account_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="다른 사용자가 이미 등록한 블로그 계정입니다.",
        )

    token_record = platform_repository.get_verification_token(user_id, platform_info.platform_id)
    new_token_value = (
        token_record.token
        if token_record
        and token_record.pending_account_id == account_id
        else f"tistory-auth-{uuid.uuid4().hex[:8]}"
    )

    platform_repository.upsert_verification_token(
        user_id=user_id,
        platform_id=platform_info.platform_id,
        token=new_token_value,
        pending_account_id=account_id,
    )
    db.commit()
    return new_token_value


async def issue_naver_verification_token(db: Session, user_id: str, account_id: str) -> tuple[str | None, str]:
    """네이버 인증 토큰 발급 및 인증 메일 발송. (verification_token, message)"""
    platform_repository = PlatformRepository(db)
    platform_info = platform_repository.get_platform_by_name("naver")
    if not platform_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="네이버 플랫폼 정보가 없습니다.")

    if platform_repository.get_user_platform_mapping(user_id, platform_info.platform_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 등록된 네이버 블로그가 있습니다.",
        )

    if platform_repository.get_user_platform_by_platform_and_account(
        platform_info.platform_id, account_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="다른 사용자가 이미 등록한 블로그 계정입니다.",
        )
    account_id = account_id.strip()
    email = f"{account_id}@naver.com"

    verify_token = f"nv-{uuid.uuid4().hex}"
    platform_repository.upsert_verification_token(
        user_id=user_id,
        platform_id=platform_info.platform_id,
        token=verify_token,
        pending_account_id=account_id,
    )
    db.commit()

    try:
        await send_naver_platform_verification_email(email, verify_token)
    except Exception:
        logger.exception("네이버 플랫폼 인증 메일 발송 실패")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="인증 메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.",
        )

    return verify_token, "인증 메일이 발송되었습니다. 메일의 링크를 클릭해 주세요."


def complete_naver_verification_by_token(
    db: Session, token: str
) -> tuple[bool, str, str | None, str | None]:
    """
    이메일 링크 클릭 시 토큰으로 등록 완료.
    Returns: (success, html_body, user_id_for_event, account_id_for_event)
    """
    platform_repository = PlatformRepository(db)
    record = platform_repository.get_verification_by_token(token)
    if not record or not record.pending_account_id:
        return False, _naver_verify_html(False, "유효하지 않거나 만료된 인증 링크입니다."), None, None

    platform_info = platform_repository.get_platform_by_name("naver")
    if not platform_info or record.platform_id != platform_info.platform_id:
        return False, _naver_verify_html(False, "유효하지 않은 인증 요청입니다."), None, None

    account_id = record.pending_account_id
    user_id = str(record.user_id)

    if platform_repository.get_user_platform_mapping(user_id, platform_info.platform_id):
        return False, _naver_verify_html(False, "이미 등록된 네이버 블로그가 있습니다."), None, None

    if platform_repository.get_user_platform_by_platform_and_account(
        platform_info.platform_id, account_id
    ):
        return False, _naver_verify_html(False, "이미 등록된 블로그 계정입니다."), None, None

    try:
        add_user_platform_mapping(
            db,
            user_id,
            platform_info.platform_id,
            account_id,
            commit=False,
        )
        platform_repository.delete_verification_record(record)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("네이버 플랫폼 인증 처리 실패")
        return False, _naver_verify_html(False, "인증 처리 중 오류가 발생했습니다."), None, None

    return True, _naver_verify_html(True, None), user_id, account_id


def _naver_verify_html(success: bool, error_message: str | None) -> str:
    dashboard_url = f"{FRONTEND_URL.rstrip('/')}/"
    if success:
        body = """
        <h2>네이버 블로그 연동이 완료되었습니다.</h2>
        <p>아래 버튼에서 플랫폼 관리 화면으로 이동할 수 있습니다.</p>
        """
    else:
        body = f"<h2>인증에 실패했습니다</h2><p>{error_message or ''}</p>"

    return f"""
<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"/><title>블로그 연동</title></head>
<body style="font-family:sans-serif;max-width:480px;margin:48px auto;">
{body}
<p><a href="{dashboard_url}" style="display:inline-block;padding:10px 20px;background:#03C75A;color:white;text-decoration:none;border-radius:4px;">플랫폼 관리로 이동</a></p>
</body>
</html>
"""

def trigger_platform_added_event(user_id: str, platform_name: str, account_id: str):
    """ 플랫폼 추가 완료 후 발생하는 내부 이벤트 (Background Task용) """
    logger.info(f"[EVENT PUBLISHED] 플랫폼 추가 완료 - user: {user_id}, platform: {platform_name}, account: {account_id}")
    # TODO: 여기에 알림 이메일 전송이나 통계 데이터 갱신, 메시지 큐 발행 등의 후속 로직을 추가할 수 있어.
