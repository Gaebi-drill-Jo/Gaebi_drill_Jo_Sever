from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from passlib.context import CryptContext
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt

import schemas
import models
from database import get_db

# -----------------------------
# 공통 설정 (보안 / JWT / Router)
# -----------------------------
oauth2_scheme = HTTPBearer()

router = APIRouter(
    tags=["Users & Info"]
)


# ✅ bcrypt 대신 pbkdf2_sha256 사용 (추가 설치 필요 없음)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


SECRET_KEY = "This!Is-My#32CHAR.Secure@Code~Key"  # 실제 서비스에서는 env로 분리 추천
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.utcnow()

    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now})

    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    # Authorization 헤더가 없거나 Bearer가 아니면
    if token is None or token.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token_str = token.credentials

    try:
        payload = jwt.decode(token_str, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = db.query(models.User).filter(models.User.User_ID == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


# -----------------------------
# 1) 회원가입
# -----------------------------
@router.post("/users", response_model=schemas.UserInfo, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 이메일 중복 체크
    if db.query(models.User).filter(models.User.useremail == user.useremail).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Useremail already exists",
        )

    # 닉네임 중복 체크
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    new_user = models.User(
        username=user.username,
        useremail=user.useremail,
        userpassword=get_password_hash(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # UserInfo(response_model)가 ORM 객체에서 알아서 필드 매핑 (from_attributes=True)
    return new_user


# -----------------------------
# 2) 로그인 (JWT 발급)
# -----------------------------
@router.post("/users/login", response_model=schemas.TokenResponse)
def login_user(user_login: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = (
        db.query(models.User)
        .filter(models.User.useremail == user_login.useremail)
        .first()
    )

    if db_user is None or not verify_password(user_login.password, db_user.userpassword):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.User_ID)},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# -----------------------------
# 3) 내 정보 조회
# -----------------------------
@router.get("/user/info", response_model=schemas.UserInfo)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    # current_user는 get_current_user에서 JWT 검증 후 가져온 User ORM 객체
    return current_user


# -----------------------------
# 4) 알림 설정 변경
# -----------------------------
@router.post(
    "/user/info/alert",
    response_model=schemas.AlertResponse,
    status_code=status.HTTP_200_OK,
)
def update_alert_settings(
    settings: schemas.AlertThreshold,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # ✅ 세 항목이 전부 None이면만 에러 (여러 개 동시에 설정 허용)
    if (
        settings.pm25_check is None
        and settings.temperature_check is None
        and settings.humidity_check is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pm25_check, temperature_check, humidity_check 중 최소 하나는 설정해야 합니다.",
        )

    # 현재 유저의 AlertSetting 조회 (없으면 새로 생성)
    db_settings = (
        db.query(models.AlertSetting)
        .filter(models.AlertSetting.user_id == current_user.User_ID)
        .first()
    )
    if not db_settings:
        db_settings = models.AlertSetting(user_id=current_user.User_ID)
        db.add(db_settings)

    # 기존 값을 초기화 후, 이번에 들어온 항목만 세팅
    db_settings.pm25_threshold = None
    db_settings.temperature_threshold = None
    db_settings.humidity_threshold = None

    if settings.pm25_check is not None:
        db_settings.pm25_threshold = settings.pm25_check
    if settings.temperature_check is not None:
        db_settings.temperature_threshold = settings.temperature_check
    if settings.humidity_check is not None:
        db_settings.humidity_threshold = settings.humidity_check

    # 알림 주기(분)
    db_settings.interval_minutes = settings.minutes

    db.commit()
    db.refresh(db_settings)

    return db_settings





# -----------------------------
# 5) 계정 삭제
# -----------------------------
@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # 자기 자신만 삭제 가능
    if current_user.User_ID != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this user",
        )

    db_user_query = db.query(models.User).filter(models.User.User_ID == user_id)
    if not db_user_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db_user_query.delete(synchronize_session=False)
    db.commit()
    return {"detail": "성공"}
