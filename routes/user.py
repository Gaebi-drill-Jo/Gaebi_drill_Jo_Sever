from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import schemas  
import models  
from database import get_db 
from passlib.context import CryptContext
from typing import List

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
oauth2_scheme = HTTPBearer()

router = APIRouter(
    tags=["Users & Info"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password):
    return pwd_context.hash(password)

def get_current_user(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    user = db.query(models.User).first() 
    if not user:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user 

@router.post("/users", response_model=schemas.UserInfo, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.useremail == user.useremail).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usereamil already exists")
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    
    new_user = models.User(
        username=user.username,
        useremail=user.useremail,
        userpassword=get_password_hash(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/users/login", response_model=schemas.TokenResponse)
def login_user(user_login: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.useremail == user_login.useremail).first()
    
    if not db_user or not verify_password(user_login.password, db_user.userpassword):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return {
        "access_token": "fake_jwt_token_for_" + str(db_user.User_ID), 
        "token_type": "bearer", 
        "expires_in": 3600
    }

@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.User_ID != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this user")

    db_user_query = db.query(models.User).filter(models.User.User_ID == user_id)
    if not db_user_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db_user_query.delete(synchronize_session=False)
    db.commit()
    return {"detail": "성공"} 

@router.get("/user/info", response_model=schemas.UserInfo)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    return current_user 

@router.post("/user/info/alert", response_model=schemas.AlertResponse, status_code=status.HTTP_200_OK)
def update_alert_settings(settings: schemas.AlertThreshold, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    
    active_checks = [settings.pm25_check, settings.tempature_check, settings.humidity_check]
    provided_checks = [c for c in active_checks if c is not None]
    
    if len(provided_checks) != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="pm25_check, tempature_check, or humidity_check 중 하나만 설정해야 합니다.")
    
    db_settings = db.query(models.AlertSetting).filter(models.AlertSetting.user_id == current_user.User_ID).first()
    if not db_settings:
        db_settings = models.AlertSetting(user_id=current_user.User_ID)
        db.add(db_settings)

    db_settings.pm25_threshold = None
    db_settings.temperature_threshold = None
    db_settings.humidity_threshold = None
    
    if settings.pm25_check is not None:
        db_settings.pm25_threshold = settings.pm25_check
    if settings.tempature_check is not None:
        db_settings.temperature_threshold = settings.tempature_check
    if settings.humidity_check is not None:
        db_settings.humidity_threshold = settings.humidity_check
        
    db_settings.interval_minutes = settings.minutes
    
    db.commit()
    db.refresh(db_settings)
    
    return db_settings