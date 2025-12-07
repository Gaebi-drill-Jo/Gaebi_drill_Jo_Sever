# main.py
from fastapi import FastAPI
from fastapi.security import HTTPBearer
from routes import user, measurement, graph 
from database import engine, Base 
from mqtt import start_mqtt
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# ✅ CORS 설정 (개발용: 일단 전부 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 모든 origin 허용 (개발 중이라면 이렇게 두는게 속 편합니다)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 라우터 등록 (한 번만)
app.include_router(user.router)
app.include_router(measurement.router)
app.include_router(graph.router)

@app.on_event("startup")
def startup_event():
    # 서버 올라갈 때 MQTT도 같이 시작
    start_mqtt()

@app.get("/")
def read_root():
    return {"Hello": "Airlzy FastAPI Server is running!"}
