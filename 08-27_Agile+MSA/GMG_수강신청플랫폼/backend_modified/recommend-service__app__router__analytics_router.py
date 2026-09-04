from fastapi import APIRouter, Depends, HTTPException, Query

from app.config.security import verify_token
from app.model.analytics_schemas import (
    EvaluationResponse,
    ForecastSummaryResponse,
    TrainResponse,
)
from app.service.analytics_service import demand_analytics_service


router = APIRouter(prefix="/api/recommend/analytics", tags=["demand-analytics"])


@router.post("/train", response_model=TrainResponse)
async def train_forecast(token_payload: dict = Depends(verify_token)):
    try:
        return demand_analytics_service.train()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"수요 예측 학습 실패: {exc}") from exc


@router.get("/evaluation", response_model=EvaluationResponse)
async def get_evaluation(token_payload: dict = Depends(verify_token)):
    try:
        return demand_analytics_service.evaluation()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"평가 결과 조회 실패: {exc}") from exc


@router.get("/forecast", response_model=ForecastSummaryResponse)
async def get_forecast(
    group_id: int = Query(alias="groupId", gt=0),
    token_payload: dict = Depends(verify_token),
):
    try:
        return await demand_analytics_service.summary(group_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"수요 예측 조회 실패: {exc}") from exc
