from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class WeeklyForecast(BaseModel):
    weekStart: date
    predictedDemand: float


class TransferSuggestion(BaseModel):
    fromGroupId: int
    category: str
    suggestedQuantity: int


class DemandForecastItem(BaseModel):
    groupId: int
    category: str
    forecastDemand: float
    averageLoanDays: float
    requiredUnits: int
    totalStock: int
    availableStock: int
    sharedStock: int
    shortageUnits: int
    riskLevel: str
    weekly: List[WeeklyForecast]
    transferSuggestions: List[TransferSuggestion] = []


class ForecastSummaryResponse(BaseModel):
    runId: int
    generatedAt: datetime
    modelName: str
    horizonWeeks: int
    groupId: int
    items: List[DemandForecastItem]


class EvaluationResponse(BaseModel):
    runId: int
    trainedAt: datetime
    modelName: str
    baselineMae: float
    modelMae: float
    baselineWape: float
    modelWape: float
    improvementPercent: float
    trainRows: int
    testRows: int
    eventCount: int
    dataStart: Optional[date] = None
    dataEnd: Optional[date] = None
    candidateMetrics: dict


class TrainResponse(BaseModel):
    runId: int
    modelName: str
    eventCount: int
    modelWape: float
    baselineWape: float
    message: str
