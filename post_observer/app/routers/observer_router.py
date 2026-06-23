from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from app.dependencies.internal_auth import require_internal_token
from app.schemas.observer_schemas import (
    CheckInactiveUsersResponse,
    CheckNewPostsResponse,
    CrawlContentsRequest,
    CrawlContentsResponse,
    CrawlResultItem,
    RegisterPlatformRequest,
    RegisterPlatformResponse,
    RssUrlsResponse,
)
from app.services.crawl_service import crawl_contents, validate_crawl_url
from app.services.observer_service import check_inactive_users, check_new_posts
from app.services.register_service import register_platform
from app.services.rss_service import fetch_rss

router = APIRouter(prefix="/api/observer", tags=["Observer"])


@router.get(
    "/rss/urls",
    response_model=RssUrlsResponse,
    status_code=status.HTTP_200_OK,
)
def get_rss_urls(
    platform: str = Query(..., description="플랫폼 이름 (naver, tistory, velog)"),
    account_id: str = Query(..., description="플랫폼 계정 ID"),
) -> RssUrlsResponse:
    """
    RSS를 파싱하여 글 목록을 반환합니다.

    :param platform: 플랫폼 이름.
    :param account_id: 플랫폼 계정 ID.
    :return: RSS 파싱 결과.
    """
    articles = fetch_rss(platform, account_id)
    return RssUrlsResponse(
        platform=platform,
        account_id=account_id,
        articles=articles,
    )


@router.post(
    "/crawl/contents",
    response_model=CrawlContentsResponse,
    status_code=status.HTTP_200_OK,
)
def post_crawl_contents(
    req: CrawlContentsRequest,
    _: None = Depends(require_internal_token),
) -> CrawlContentsResponse:
    """
    URL 목록을 받아 각 페이지의 본문을 크롤링합니다.

    :param req: 크롤링할 URL 목록.
    :return: URL별 본문 크롤링 결과.
    """
    try:
        validated_urls = [validate_crawl_url(url) for url in req.urls]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    raw_results = crawl_contents(validated_urls)
    results = [CrawlResultItem(url=r["url"], content=r["content"]) for r in raw_results]
    return CrawlContentsResponse(results=results)


@router.post(
    "/register-platform",
    response_model=RegisterPlatformResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def run_register_platform(
    req: RegisterPlatformRequest,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_internal_token),
) -> RegisterPlatformResponse:
    """
    플랫폼 등록 시 해당 유저의 기존 글 수집을 백그라운드에서 시작합니다.

    :param req: 플랫폼 등록 요청 (user_id, platform_name, account_id).
    :param background_tasks: FastAPI BackgroundTasks.
    :return: 수집 시작 메시지.
    """
    background_tasks.add_task(
        register_platform,
        user_id=req.user_id,
        platform_name=req.platform_name,
        account_id=req.account_id,
    )
    return RegisterPlatformResponse(message="수집이 시작되었습니다.")


@router.post("/check-new-posts", response_model=CheckNewPostsResponse, status_code=status.HTTP_200_OK)
def run_check_new_posts(
    _: None = Depends(require_internal_token),
) -> CheckNewPostsResponse:
    """
    모든 유저-플랫폼의 새 글을 수집하고 RabbitMQ에 발행합니다.

    :return: 수집된 새 글 수.
    """
    total_new_posts = check_new_posts()
    return CheckNewPostsResponse(total_new_posts=total_new_posts)


@router.post(
    "/check-inactive-users",
    response_model=CheckInactiveUsersResponse,
    status_code=status.HTTP_200_OK,
)
def run_check_inactive_users(
    _: None = Depends(require_internal_token),
) -> CheckInactiveUsersResponse:
    """
    1달 이상 글을 올리지 않은 비활성 유저를 조회하고 메일 알림을 발행합니다.

    :return: 발송된 알림 수.
    """
    total_reminders = check_inactive_users()
    return CheckInactiveUsersResponse(total_reminders=total_reminders)


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> dict:
    """
    서버 헬스체크 엔드포인트.

    :return: 서버 상태.
    """
    return {"status": "ok"}
