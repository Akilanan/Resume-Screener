from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token, generate_otp, hash_password
from app.core.config import settings
from app.core.encryption import encrypt
from app.schemas.auth import LoginRequest, OTPVerifyRequest, RefreshRequest, TokenResponse
import redis
import smtplib
from email.mime.text import MIMEText

router = APIRouter()
redis_client = redis.Redis(host=settings.REDIS_HOST, port=6379, decode_responses=True)


@router.post("/setup-admin")
def setup_admin(db: Session = Depends(get_db)):
    """Create admin user if not exists"""
    from app.db.models import UserRole
    user = db.query(User).filter(User.email == 'admin@talentai.com').first()
    if user:
        return {"message": "Admin already exists"}
    
    admin = User(
        email='admin@talentai.com',
        name_encrypted=encrypt('Admin User'),
        hashed_password=hash_password('Admin@123'),
        role=UserRole.admin,
        is_active=True
    )
    db.add(admin)
    db.commit()
    return {"message": "Admin created successfully", "email": "admin@talentai.com", "password": "Admin@123"}


def send_otp_email(to_email: str, otp: str):
    """Send OTP via email (SMTP)"""
    try:
        msg = MIMEText(f"Your TalentAI verification code is: {otp}\n\nValid for 5 minutes.")
        msg["Subject"] = "TalentAI - Your OTP Code"
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.send_message(msg)
    except Exception as e:
        # Log but don't block — for hackathon, print OTP to console as fallback
        print(f"[MAIL FALLBACK] OTP for {to_email}: {otp}")


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    print(f"Login attempt for: {request.email}")
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        print("User not found")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(request.password, user.hashed_password):
        print("Password verification failed")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        print("User account disabled")
        raise HTTPException(status_code=403, detail="Account disabled")
    
    # Generate OTP
    otp = generate_otp()
    redis_client.setex(f"otp:{request.email}", 300, otp)
    
    # Try to send email, but also return OTP in response for demo
    send_otp_email(request.email, otp)
    
    # Return OTP in response for DEMO ONLY - REMOVE IN PRODUCTION
    import os
    is_demo = os.getenv("DEMO_MODE", "true").lower() == "true"
    return {
        "mfa_required": True,
        "message": "OTP sent to your email",
        "otp": otp if is_demo else None,  # Hidden in production
        "access_token": None,
        "refresh_token": None,
        "token_type": None,
        "role": None
    }


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    stored_otp = redis_client.get(f"otp:{request.email}")
    if not stored_otp or stored_otp != request.otp:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    redis_client.delete(f"otp:{request.email}")
    user = db.query(User).filter(User.email == request.email).first()

    access_token = create_access_token({"sub": user.id, "role": user.role.value})
    refresh_token = create_refresh_token({"sub": user.id, "role": user.role.value})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role.value,
    }


@router.post("/refresh")
def refresh_token(request: RefreshRequest):
    try:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        access_token = create_access_token({"sub": payload["sub"], "role": payload["role"]})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
