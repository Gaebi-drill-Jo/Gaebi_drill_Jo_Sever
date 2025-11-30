from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import schemas  
import models   
from database import get_db 
from typing import Optional
from datetime import datetime

router = APIRouter(
    tags=["Graph Data"]
)

@router.get("/graph", response_model=schemas.GraphResponse)
def get_data_for_graph(
    start_date: Optional[datetime] = Query(None, description="조회 시작 날짜/시간 (ISO 8601 형식)"), 
    end_date: Optional[datetime] = Query(None, description="조회 종료 날짜/시간 (ISO 8601 형식)"), 
    db: Session = Depends(get_db)
):
    
    query = db.query(models.Data)
    
    if start_date:
        query = query.filter(models.Data.created_at >= start_date)
    if end_date:
        query = query.filter(models.Data.created_at <= end_date)
        
    data_list = query.order_by(models.Data.created_at.desc()).limit(100).all()

    return {"points": data_list}