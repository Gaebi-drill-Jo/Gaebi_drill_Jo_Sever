from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, Union


class UserCreate(BaseModel):
    username: str
    useremail: EmailStr
    password: str 

class UserLogin(BaseModel):
    useremail: EmailStr
    password: str 

class UserInfo(BaseModel):
    id: int = Field(alias="User_ID")
    username: str = Field(alias="user_name")
    email: EmailStr = Field(alias="useremail")
    create_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class MeasurementCreate(BaseModel):
    temperature: float = Field(..., ge=0)
    humidity: float = Field(..., ge=0)
    pm25: float = Field(..., ge=0)

class StorageCreate(MeasurementCreate):
    note: Optional[str] = None
    
class DataPoint(BaseModel):
    id: int
    timestamp: datetime = Field(alias="created_at")
    temperature: float
    humidity: float
    pm25: float
    air_quality: Optional[str] = None
    note: Optional[str] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True

class GraphResponse(BaseModel):
    points: List[DataPoint]

class AlertThreshold(BaseModel):
    pm25_check: Optional[int] = Field(None, gt=0)
    tempature_check: Optional[int] = Field(None, gt=0)
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