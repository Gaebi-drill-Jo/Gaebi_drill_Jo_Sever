from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List


# -----------------------------
# 1) 회원 관련
# -----------------------------
class UserCreate(BaseModel):
    username: str
    useremail: EmailStr
    password: str


class UserLogin(BaseModel):
    useremail: EmailStr
    password: str


class UserInfo(BaseModel):
    # DB: User.User_ID  -> 응답: id
    id: int = Field(alias="User_ID")

    # DB: User.username -> 응답: username (alias 필요 없음)
    username: str

    # DB: User.useremail -> 응답: email
    email: EmailStr = Field(alias="useremail")

    # DB: User.create_at -> 응답: created_at
    created_at: datetime = Field(alias="create_at")

    class Config:
        from_attributes = True
        populate_by_name = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


# -----------------------------
# 2) 측정/그래프 관련
# -----------------------------
class MeasurementCreate(BaseModel):
    temperature: float = Field(..., ge=0)
    humidity: float = Field(..., ge=0)
    pm25: float = Field(..., ge=0)


class StorageCreate(MeasurementCreate):
    note: Optional[str] = None


class DataPoint(BaseModel):
    id: int
    created_at: datetime
    temperature: float
    humidity: float
    pm25: float
    air_quality: str
    note: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class GraphResponse(BaseModel):
    points: List[DataPoint]


# -----------------------------
# 3) 알림 설정 관련
# -----------------------------
class AlertThreshold(BaseModel):
    pm25_check: Optional[int] = Field(None, gt=0)
    temperature_check: Optional[int] = Field(None, gt=0)
    humidity_check: Optional[int] = Field(None, gt=0)
    minutes: int = Field(..., ge=1, le=60)


class AlertResponse(BaseModel):
    pm25_threshold: Optional[int] = None
    temperature_threshold: Optional[int] = None
    humidity_threshold: Optional[int] = None
    interval_minutes: int
    updated_at: datetime

    class Config:
        from_attributes = True
