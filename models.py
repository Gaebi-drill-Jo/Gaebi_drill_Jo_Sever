from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "User" 
    
    User_ID = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    useremail = Column(String(50), unique=True, nullable=False, index=True)
    userpassword = Column(String(100), nullable=False)
    create_at = Column(DateTime, default=func.now())
    
    data_points = relationship("Data", back_populates="owner")
    alert_setting = relationship("AlertSetting", back_populates="owner", uselist=False)

class Data(Base):
    __tablename__ = "data" 
    
    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float)
    humidity = Column(Float)
    pm25 = Column(Float)
    air_quality = Column(String(20))
    note = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    
    user_id = Column(Integer, ForeignKey("User.User_ID"))
    owner = relationship("User", back_populates="data_points")

class AlertSetting(Base):
    __tablename__ = "alert_setting"
    
    user_id = Column(Integer, ForeignKey("User.User_ID"), primary_key=True)
    pm25_threshold = Column(Integer, default=35)
    temperature_threshold = Column(Integer, default=30)
    humidity_threshold = Column(Integer, default=60)
    interval_minutes = Column(Integer, default=1)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    owner = relationship("User", back_populates="alert_setting")