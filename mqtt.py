# mqtt.py
import json
from typing import Optional

import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from database import SessionLocal
import models
from email_utils import send_alert_email

MQTT_BROKER: str = "broker.hivemq.com"
MQTT_PORT: int = 1883
MQTT_TOPIC: str = "slide/D~HT"


def get_air_quality(pm25: float) -> str:
    """PM2.5 값으로 공기질 등급 계산"""
    if pm25 < 15:
        return "good"
    elif pm25 < 50:
        return "normal"
    else:
        return "bad"


def check_and_send_alert(
    db: Session,
    user_id: int,
    temperature: float,
    humidity: float,
    pm25: float,
) -> None:
    """
    - 해당 user_id의 AlertSetting을 읽어서
    - pm25 / 온도 / 습도 중 하나라도 임계값 이상이면
    - 그 유저 이메일로 알림 메일 전송
    - ⚠ AlertSetting 값이 None이면 기본값으로 강제 사용 (응급처치)
    """
    try:
        # 1) 유저 조회
        user = (
            db.query(models.User)
            .filter(models.User.User_ID == user_id)
            .first()
        )
        if user is None:
            print("[ALERT] No user found for id:", user_id)
            return

        # 2) 알림 설정 조회
        setting = (
            db.query(models.AlertSetting)
            .filter(models.AlertSetting.user_id == user_id)
            .first()
        )
        if setting is None:
            print("[ALERT] No AlertSetting for user:", user_id)
            return

        # ⚠ 여기서 None 이면 기본값 강제 적용 (응급용 하드코딩)
        pm25_threshold = (
            float(setting.pm25_threshold)
            if setting.pm25_threshold is not None
            else 50.0
        )
        temp_threshold = (
            float(setting.temperature_threshold)
            if setting.temperature_threshold is not None
            else 1.0    # 🔥 온도 기준이 None이면 무조건 1도로 사용
        )
        humi_threshold = (
            float(setting.humidity_threshold)
            if setting.humidity_threshold is not None
            else 40.0
        )

        # 디버깅용: 현재 값과 임계값 로그
        print(
            "[ALERT] Current values  -> "
            f"temp={temperature}, humi={humidity}, pm25={pm25}"
        )
        print(
            "[ALERT] Thresholds(fixed) -> "
            f"temp={temp_threshold}, humi={humi_threshold}, pm25={pm25_threshold}"
        )

        alert_reason: Optional[str] = None

        # 1) 미세먼지 기준
        if pm25 is not None:
            if pm25 >= pm25_threshold:
                alert_reason = (
                    f"미세먼지(PM2.5)가 설정 기준을 초과했습니다.\n"
                    f"- 현재 값: {pm25}\n"
                    f"- 기준 값: {pm25_threshold}"
                )
                print("[ALERT] PM2.5 threshold exceeded")

        # 2) 온도 기준 (아직 알림 안 잡혔을 때만)
        if alert_reason is None and temperature is not None:
            if temperature >= temp_threshold:
                alert_reason = (
                    f"온도가 설정 기준을 초과했습니다.\n"
                    f"- 현재 값: {temperature}\n"
                    f"- 기준 값: {temp_threshold}"
                )
                print("[ALERT] Temperature threshold exceeded")

        # 3) 습도 기준
        if alert_reason is None and humidity is not None:
            if humidity >= humi_threshold:
                alert_reason = (
                    f"습도가 설정 기준을 초과했습니다.\n"
                    f"- 현재 값: {humidity}\n"
                    f"- 기준 값: {humi_threshold}"
                )
                print("[ALERT] Humidity threshold exceeded")

        # 어느 기준도 넘지 않았으면 메일 X
        if alert_reason is None:
            print("[ALERT] No threshold exceeded. No email.")
            return

        subject = "[AIRZY] 공기질 알림"
        body = (
            f"{user.username}님,\n\n"
            f"{alert_reason}\n\n"
            "실내 공기 상태를 확인해 주세요."
        )

        # email_utils.py 의 send_alert_email 사용
        send_alert_email(user.useremail, subject, body)

    except Exception as e:
        # 알림 처리 중 에러가 나도 MQTT 저장 자체는 실패시키지 않도록 로깅만
        print("[ALERT] 알림 처리 중 오류:", e)



def save_measurement_to_db(
    temperature: float,
    humidity: float,
    pm25: float,
    user_id: Optional[int] = None,
) -> None:
    """
    MQTT로 받은 측정값을 DB에 저장하고, 알림 조건을 체크한다.
    user_id가 None이면 DB에서 가장 먼저 생성된 유저를 사용한다.
    """
    db: Session = SessionLocal()
    try:
        # user_id가 명시되지 않으면 첫 번째 유저를 기본으로 사용
        if user_id is None:
            first_user = db.query(models.User).order_by(models.User.User_ID.asc()).first()
            if first_user is None:
                print("[MQTT] No user found in DB. Skip saving.")
                return
            user_id = first_user.User_ID

        print(f"[MQTT] Save measurement for user_id={user_id}")

        air_quality = get_air_quality(pm25)

        new_data = models.Data(
            temperature=temperature,
            humidity=humidity,
            pm25=pm25,
            air_quality=air_quality,
            user_id=user_id,
        )
        db.add(new_data)
        db.commit()
        db.refresh(new_data)

        # 저장 성공 후 알림 기준 체크 + 이메일 전송 시도
        check_and_send_alert(
            db=db,
            user_id=user_id,
            temperature=temperature,
            humidity=humidity,
            pm25=pm25,
        )

    except Exception as e:
        db.rollback()
        print("[MQTT] DB error:", e)
    finally:
        db.close()


def on_connect(client: mqtt.Client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Connected to broker")
        client.subscribe(MQTT_TOPIC)
        print(f"[MQTT] Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"[MQTT] Connection failed with code {rc}")


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    try:
        payload_str = msg.payload.decode("utf-8")
        payload = json.loads(payload_str)
        print(f"[MQTT] Received on {msg.topic}: {payload}")

        # raw 값 먼저 꺼내서 None 여부 검사
        temp_raw = payload.get("temperature")
        humi_raw = payload.get("humidity")
        pm25_raw = payload.get("pm25")

        if temp_raw is None or humi_raw is None or pm25_raw is None:
            print("[MQTT] Missing fields in payload. Skip.")
            return

        temperature = float(temp_raw)
        humidity = float(humi_raw)
        pm25 = float(pm25_raw)

        save_measurement_to_db(
            temperature=temperature,
            humidity=humidity,
            pm25=pm25,
            user_id=None,  # None이면 save_measurement_to_db에서 첫 번째 유저 사용
        )

    except Exception as e:
        print("[MQTT] Error handling message:", e)


_client: Optional[mqtt.Client] = None


def start_mqtt() -> None:
    """애플리케이션 시작 시 한 번만 호출해서 MQTT 클라이언트를 구동한다."""
    global _client

    if _client is not None:
        # 이미 시작되어 있으면 재시작하지 않음
        return

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    _client = client
    print("[MQTT] MQTT client started")
