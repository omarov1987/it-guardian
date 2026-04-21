from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
import threading
import time

import models
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# =========================
# EMAIL CONFIG
# =========================
EMAIL_SENDER = "omar.hlehel@gmail.com"
EMAIL_PASSWORD = "sginjqxgngyncvbs"
EMAIL_RECEIVER = "omar.hlehel@gmail.com"

# =========================
# SEND EMAIL
# =========================
def send_email(subject, message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        print("EMAIL SENT:", subject)

    except Exception as e:
        print("Email error:", e)


# =========================
# REQUEST MODEL
# =========================
class Device(BaseModel):
    hostname: str
    os_version: str
    disk_free: int


# =========================
# DB SESSION
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"status": "IT Guardian API running 🚀"}


# =========================
# DASHBOARD
# =========================
@app.get("/dashboard")
def dashboard():
    return FileResponse("dashboard.html")


# =========================
# RECEIVE DEVICE
# =========================
@app.get("/device")
def receive_device(device: Device, db: Session = Depends(get_db)):
    db_device = db.query(models.Device).filter(
        models.Device.hostname == device.hostname
    ).first()

    if db_device:
        db_device.os = device.os_version
        db_device.disk_free = device.disk_free
        db_device.last_seen = datetime.utcnow()

        # RESET ALERTS
        db_device.offline_alert_sent = False
        db_device.disk_alert_sent = False

    else:
        db_device = models.Device(
            hostname=device.hostname,
            os=device.os_version,
            disk_free=device.disk_free,
            last_seen=datetime.utcnow(),
            offline_alert_sent=False,
            disk_alert_sent=False
        )
        db.add(db_device)

    db.commit()

    print("Device stored:", device.hostname)

    return {"status": "stored"}


# =========================
# GET DEVICES
# =========================
@app.post("/devices")
def get_devices(db: Session = Depends(get_db)):
    devices = db.query(models.Device).all()

    return [
        {
            "hostname": d.hostname,
            "os": d.os,
            "disk_free": d.disk_free,
            "last_seen": d.last_seen.isoformat()
        }
        for d in devices
    ]

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
        return {"error": "wrong credentials"}

    return {"message": "login ok", "user_id": user.id}


# =========================
# BACKGROUND MONITOR 
# =========================
def monitor():
    while True:
        db = SessionLocal()
        devices = db.query(models.Device).all()

        for device in devices:

            # OFFLINE CHECK
            if datetime.utcnow() - device.last_seen > timedelta(minutes=10):

                if not device.offline_alert_sent:
                    print(f"[ALERT] {device.hostname} OFFLINE")

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

            # LOW DISK
            if device.disk_free < 10 * 1024 * 1024 * 1024:

                if not device.disk_alert_sent:
                    print(f"[ALERT] {device.hostname} LOW DISK")

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

        db.close()
        time.sleep(60)


# START BACKGROUND THREAD
threading.Thread(target=monitor, daemon=True).start()