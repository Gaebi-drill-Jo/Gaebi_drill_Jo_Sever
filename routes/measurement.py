from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import schemas  
import models   
from database import get_db 
from routes.user import get_current_user 

router = APIRouter(
    tags=["Measurement & Storage"]
)

@router.post("/measurement", response_model=schemas.DataPoint, status_code=status.HTTP_201_CREATED)
def record_measurement(data: schemas.MeasurementCreate, db: Session = Depends(get_db),  current_user: models.User = Depends(get_current_user)):
    
    air_quality = "good" if data.pm25 < 15 else ("normal" if data.pm25 < 50 else "bad")
    
    new_data = models.Data(
        temperature=data.temperature,
        humidity=data.humidity,
        pm25=data.pm25,
        air_quality=air_quality,
        user_id=current_user.User_ID
    )
    
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    
    return new_data

@router.post("/storage", response_model=schemas.DataPoint, status_code=status.HTTP_200_OK)
def store_data(data: schemas.StorageCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    

    air_quality = "good" if data.pm25 < 15 else ("normal" if data.pm25 < 50 else "bad")
    
    new_data = models.Data(
        temperature=data.temperature,
        humidity=data.humidity,
        pm25=data.pm25,
        note=data.note,
        air_quality=air_quality,
        user_id=current_user.User_ID 
    )
    
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    
    return new_data