import httpx
import logging
from typing import List
from app.config.settings import settings
from app.model.schemas import CourseResponse, CourseCategory

logger = logging.getLogger(__name__)


class CourseServiceClient:
    """
    Course Service REST 클라이언트
    - 카테고리별 미수강 강의 목록 조회
    """

    def __init__(self):
        self.base_url = settings.course_service_url

    async def get_recommend_courses(
        self,
        category: CourseCategory,
        exclude_ids: List[int]
    ) -> List[CourseResponse]:
        """
        GET /courses/internal/recommend
        카테고리 기반 미수강 강의 목록 조회 (수강생 수 기준 정렬)
        """
        url = f"{self.base_url}/api/courses/internal/recommend"
        params = {"category": category.value}
        if exclude_ids:
            params["excludeIds"] = ",".join(str(i) for i in exclude_ids)

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return [CourseResponse(**c) for c in response.json()]
        except httpx.HTTPError as e:
            logger.error(f"[CourseClient] 추천 강의 조회 실패 - category: {category}, error: {e}")
            return []

    async def get_all_courses(self) -> List[CourseResponse]:
        """
        GET /courses - 전체 강의 목록 조회
        수강 이력이 없는 신규 사용자 추천용
        """
        url = f"{self.base_url}/api/courses"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                courses = data.get("data", [])
                return [CourseResponse(**c) for c in courses]
        except httpx.HTTPError as e:
            logger.error(f"[CourseClient] 전체 강의 조회 실패 - error: {e}")
            return []

    async def get_analytics_assets(self) -> List[CourseResponse]:
        """관리자 수요 예측의 현재 재고 계산용 전체 활성 자산."""
        url = f"{self.base_url}/api/courses/internal/analytics/assets"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return [CourseResponse(**item) for item in response.json()]
        except httpx.HTTPError as exc:
            logger.error(f"[CourseClient] 분석용 자산 조회 실패 - error: {exc}")
            return []


course_client = CourseServiceClient()
