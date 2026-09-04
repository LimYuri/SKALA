from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from decimal import Decimal
from datetime import datetime


class CourseCategory(str, Enum):
    BACKEND = "BACKEND"
    FRONTEND = "FRONTEND"
    DEVOPS = "DEVOPS"
    DATA_SCIENCE = "DATA_SCIENCE"
    MOBILE = "MOBILE"
    SECURITY = "SECURITY"
    DATABASE = "DATABASE"
    OTHER = "OTHER"
    DEVICE = "DEVICE"
    COMPUTER = "COMPUTER"
    SERVER_CLOUD = "SERVER_CLOUD"
    ELECTRONICS_IOT = "ELECTRONICS_IOT"
    MAKER = "MAKER"
    CAMERA_AUDIO = "CAMERA_AUDIO"
    PRESENTATION = "PRESENTATION"
    ACCESSORY = "ACCESSORY"
    ETC = "ETC"


class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: CourseCategory
    price: Decimal
    itemType: str = "OWNED"
    totalQuantity: int = 1
    availableQuantity: int = 1
    purchaseUrl: Optional[str] = None
    ownerGroupId: Optional[int] = None
    visibility: str = "ORGANIZATION"
    pickupLocation: Optional[str] = None
    maxLoanDays: int = 7
    instructorId: int
    enrollmentCount: int
    status: str
    createdAt: Optional[datetime] = None


class EnrollmentHistoryResponse(BaseModel):
    userId: int
    activeCourseIds: List[int]


class RecommendResponse(BaseModel):
    userId: int
    recommendedCourses: List[CourseResponse]
    basedOnCategory: Optional[CourseCategory] = None
    message: str


class AlternativeRecommendResponse(BaseModel):
    category: CourseCategory
    alternatives: List[CourseResponse]
    message: str


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
