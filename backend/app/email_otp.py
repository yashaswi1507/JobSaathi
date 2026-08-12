"""
email_otp.py — Email OTP verification for registration
Uses Python's smtplib — no paid service needed (Gmail SMTP)
"""
import smtplib, random, string, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from fastapi import APIRouter

router = APIRouter()

# In-memory OTP store (use Redis in production)
_otp_store = {}  # {email: {otp, expires_at}}

SMTP_EMAIL    = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))


def _generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))


def _send_email(to_email: str, otp: str) -> bool:
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"[OTP] SMTP not configured — OTP for {to_email}: {otp}")
        return True  # Dev mode — print OTP

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "JobSaathi AI — Email Verification OTP"
        msg["From"]    = SMTP_EMAIL
        msg["To"]      = to_email

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:24px">
          <div style="background:#0EA5E9;padding:16px 24px;border-radius:10px 10px 0 0">
            <h2 style="color:#fff;margin:0">JobSaathi AI</h2>
          </div>
          <div style="background:#f9f9f9;padding:24px;border-radius:0 0 10px 10px">
            <h3 style="color:#1A1410">Verify your email</h3>
            <p style="color:#6B5E52">Your OTP for registration is:</p>
            <div style="background:#fff;border:2px solid #0EA5E9;border-radius:8px;
              padding:16px;text-align:center;margin:16px 0">
              <span style="font-size:32px;font-weight:800;letter-spacing:8px;color:#0EA5E9">
                {otp}
              </span>
            </div>
            <p style="color:#9E8E80;font-size:12px">
              Valid for 10 minutes. Do not share with anyone.
            </p>
          </div>
        </div>"""

        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[OTP] Email send failed: {e}")
        return False


@router.post("/send-otp")
def send_otp(data: dict):
    email = data.get("email", "").strip()
    if not email or "@" not in email:
        return {"success": False, "message": "Invalid email"}

    otp = _generate_otp()
    _otp_store[email] = {
        "otp": otp,
        "expires_at": datetime.now() + timedelta(minutes=10)
    }

    sent = _send_email(email, otp)
    if sent:
        return {"success": True,
                "message": "OTP sent to your email",
                "dev_otp": otp if not SMTP_EMAIL else None}
    return {"success": False, "message": "Failed to send email"}


@router.post("/verify-otp")
def verify_otp(data: dict):
    email = data.get("email", "").strip()
    otp   = data.get("otp", "").strip()

    record = _otp_store.get(email)
    if not record:
        return {"success": False, "message": "No OTP found. Please request again."}
    if datetime.now() > record["expires_at"]:
        del _otp_store[email]
        return {"success": False, "message": "OTP expired. Please request again."}
    if record["otp"] != otp:
        return {"success": False, "message": "Incorrect OTP. Try again."}

    del _otp_store[email]
    return {"success": True, "message": "Email verified successfully!"}
