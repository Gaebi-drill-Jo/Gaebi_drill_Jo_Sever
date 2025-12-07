# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, Session

# SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:12345678@localhost/science_project"

# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL, 
#     pool_pre_ping=True
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db 
#     finally:
#         db.close()
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# SQLite 파일 DB 사용 (프로젝트 폴더에 science_project.db 파일이 생깁니다)
SQLALCHEMY_DATABASE_URL = "sqlite:///./science_project.db"

# SQLite는 check_same_thread 옵션 필요
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
