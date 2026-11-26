import os

from bcrypt import gensalt, hashpw
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.AI.generate_tableAI import router as table_gen
from src.auth.otp import generate_otp, save_otp, verify_otp
from src.auth.redis_client import redis_client
from src.deps import get_db
from src.email_service import send_otp_email
from src.models import User
from src.routes.login import router as login_router
from src.routes.studentlog import route as student_login
from src.routes.subjects import router as subjects_router
from src.routes.topics import router as topics_router
from src.schemas import OTPRequest, OTPVerify, UserCreate, UserOut


app = FastAPI(
    title="StudyFlow API",
    version="0.2.0",
    description="Study planning API for courses, topics, and learning progress.",
)

cors_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(table_gen, tags=["table generation"])
app.include_router(login_router, tags=["login"])
app.include_router(student_login, prefix="", tags=["student login"])
app.include_router(subjects_router, tags=["subjects"])
app.include_router(topics_router, tags=["topics"])


@app.get("/", tags=["health"])
def user():
    return {"hello": "world"}


@app.get("/health/live", tags=["health"])
def liveness():
    """Confirm that the API process is running."""
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def readiness(db: Session = Depends(get_db)):
    """Check whether the database and Redis dependencies are reachable."""
    checks = {}

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"

    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"

    ready = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ready" if ready else "not_ready",
            "checks": checks,
        },
    )


@app.post("/users", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = User(
            username=user.username,
            email=user.email,
            password_hash=hashpw(user.password.encode("utf-8"), gensalt(12)).decode(
                "utf-8"
            ),
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    except IntegrityError as e:
        db.rollback()

        if "username" in str(e.orig):
            raise HTTPException(400, "Username already exists")

        if "email" in str(e.orig):
            raise HTTPException(400, "Email already exists")

        raise HTTPException(400, "Duplicate entry")


@app.get("/users/{user_id}", response_model=UserOut)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/request-otp")
async def request_otp(otp_request: OTPRequest):
    otp = generate_otp()
    await save_otp(otp_request.email, otp)
    send_otp_email(otp_request.email, otp)
    return {"message": "OTP sent to email"}


@app.post("/verify-otp")
async def verify_otp_endpoint(otp_verify: OTPVerify):
    is_valid = await verify_otp(otp_verify.email, otp_verify.otp)
    if is_valid:
        return {"message": "OTP verified successfully"}
    raise HTTPException(status_code=400, detail="Invalid OTP")
