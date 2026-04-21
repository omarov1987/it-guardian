from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText

import models
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

EMAIL_SENDER = "omar.hlehel@gmail.com"
EMAIL_PASSWORD = "sginjqxgngyncvbs"
EMAIL_RECEIVER = "omar.hlehel@gmail.com"


def send_email(subject, message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print("Email error:", e)


class Device(BaseModel):
    hostname: str
    os_version: str
    disk_free: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"status": "IT Guardian API running 🚀"}


@app.get("/dashboard")
def dashboard():
    return FileResponse("dashboard.html")


@app.get("/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    user = models.User(username=username, password=password)
    db.add(user)
    db.commit()
    return {"status": "user created"}


@app.get("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="wrong credentials")

    return {"message": "login ok", "user_id": user.id}


def get_current_user(token: str = Header(None), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="No token")

    try:
        user_id = int(token)
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@app.post("/device")
def receive_device(device: Device, user=Depends(get_current_user), db: Session = Depends(get_db)):

    db_device = db.query(models.Device).filter(
    models.Device.hostname == device.hostname
).first()

    if db_device:
        db_device.os = device.os_version
        db_device.disk_free = device.disk_free
        db_device.last_seen = datetime.utcnow()
        db_device.offline_alert_sent = False
        db_device.disk_alert_sent = False
    else:
        db_device = models.Device(
            hostname=device.hostname,
            os=device.os_version,
            disk_free=device.disk_free,
            last_seen=datetime.utcnow(),
            owner_id=user.id,
            offline_alert_sent=False,
            disk_alert_sent=False
        )
        db.add(db_device)

    db.commit()

    return {"status": "stored"}


@app.get("/devices")
def get_devices(user=Depends(get_current_user), db: Session = Depends(get_db)):

    devices = db.query(models.Device).filter(
        models.Device.owner_id == user.id
    ).all()

    return [
        {
            "hostname": d.hostname,
            "os": d.os,
            "disk_free": d.disk_free,
            "last_seen": d.last_seen.isoformat()
        }
        for d in devices
    ]


@app.get("/alerts")
def check_alerts(db: Session = Depends(get_db)):
    alerts = []
    devices = db.query(models.Device).all()

    for device in devices:

        if datetime.utcnow() - device.last_seen > timedelta(minutes=10):
            alerts.append({
                "device": device.hostname,
                "type": "offline"
            })

            if not device.offline_alert_sent:
                send_email(
                    "🚨 Device Offline",
                    f"{device.hostname} is offline!"
                )
                device.offline_alert_sent = True
                db.commit()
        else:
            if device.offline_alert_sent:
                device.offline_alert_sent = False
                db.commit()

        if device.disk_free < 10 * 1024 * 1024 * 1024:
            alerts.append({
                "device": device.hostname,
                "type": "low_disk"
            })

            if not device.disk_alert_sent:
                send_email(
                    "⚠️ Low Disk Space",
                    f"{device.hostname} has low disk space!"
                )
                device.disk_alert_sent = True
                db.commit()
        else:
            if device.disk_alert_sent:
                device.disk_alert_sent = False
                db.commit()

    return alerts