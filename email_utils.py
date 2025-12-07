# email_utils.py
import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# ⚠️ 여기는 진짜 계정/비밀번호를 코드에 직접 쓰지 말고
# 환경변수로 빼두는 게 좋습니다.
SMTP_USER = os.getenv("SMTP_USER")  # 보내는 메일 주소
SMTP_PASS = os.getenv("SMTP_PASS")  # 앱 비밀번호 등


def send_alert_email(to_email: str, subject: str, body: str):
    """
    간단한 텍스트 메일 보내기.
    SMTP_USER / SMTP_PASS 가 설정돼 있지 않으면 그냥 로그만 찍고 넘어감.
    """
    if not (SMTP_USER and SMTP_PASS):
        print("[EMAIL] SMTP 계정이 설정되어 있지 않습니다. 메일을 보내지 않습니다.")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"[EMAIL] Alert sent to {to_email}")
    except Exception as e:
        print("[EMAIL] 메일 전송 실패:", e)
