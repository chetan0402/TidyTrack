import asyncio
import base64
import io
import json
import random
import secrets
import time
import re
from pathlib import Path

import requests
from PIL import Image
from fastapi import FastAPI, Depends, Response, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import global_config
import models
from database import SessionLocal
from global_config import *
from schema import *


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def clean_otp():
    while True:
        db = SessionLocal()
        db.query(models.OTP).filter(models.OTP.deleteTime < int(time.time())).delete()
        db.commit()
        db.close()
        await asyncio.sleep(1)


def clean_string(string) -> str:
    return re.sub(r'[^\x00-\x20\x2C\x2E\x30-\x39\x41-\x5A\x61-\x7A]', '', string)


def validUUID(string) -> bool:
    return re.fullmatch(r'[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}', string).string == string


# TODO - implement validation rule
def isValidId(id: str) -> bool:
    return True


def saveIMG(img_string: str, local_path: str) -> None:
    img_path = Path.home().joinpath("img").joinpath(local_path)
    img = Image.open(io.BytesIO(base64.b64decode(img_string.replace("\\n", "").replace("\\", ""))))
    img_buffer = io.BytesIO()
    quality = 100
    while quality > 0:
        img.save(img_buffer, "PNG", quality=quality)
        if img_buffer.tell() <= global_config.TARGET_PHOTO_SIZE * 1024 * 1024:
            break
        quality -= 5
        img_buffer.seek(0)
        img_buffer.truncate()

    img.save(img_path, "PNG", quality=quality)


app = FastAPI()


@app.on_event("startup")
async def startup():
    asyncio.create_task(clean_otp())


@app.get("/")
def homePage():
    return FileResponse("templates/index.html")


@app.post("/internet/report")
def internetReport(internet_report: InternetReport, db: Session = Depends(clean_otp)):
    if not validUUID(internet_report.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID")

    user: models.Tokens = db.query(models.Tokens).filter(models.Tokens.idtokens == internet_report.token).first()
    user: models.Userbase = db.query(models.Userbase).filter(models.Userbase.id == user.user).first()
    if user.usergroup != 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # TODO - rate limit number of reports in a day

    time_rn = int(time.time())
    local_path = f"internet-report-{time_rn}-{user.id}.png"

    internet_complain = models.InternetComplain(
        ticket_id=internet_report.id,
        location=internet_report.location,
        selected=internet_report.selected,
        other=clean_string(internet_report.other),
        img=local_path,
        time=time_rn,
        user=user.id
    )
    db.add(internet_complain)
    saveIMG(internet_report.img, local_path)
    db.commit()
    db.refresh(internet_complain)

    return {"ticket_id": internet_report.id}


@app.post("/otp/send")
def otpSend(otp_request: OTPRequest, response: Response, db: Session = Depends(get_db)):
    if not isValidId(otp_request.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID")

    otpElement = db.query(models.OTP).filter(models.OTP.id == otp_request.id).first()
    if otpElement is None:
        otpElement = models.OTP(
            id=otp_request.id,
            tries=1,
            otp=random.randint(100000, 999999),
            firstTime=int(time.time()),
            deleteTime=int(time.time()) + (60 * 60),
            nextSendTime=int(time.time()) + (2 * 60)
        )
        db.add(otpElement)
    else:
        if int(time.time()) < otpElement.nextSendTime:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        otpElement.tries += 1
        otpElement.nextSendTime = int(time.time()) + (2 * 60)
        if otpElement.tries == 4:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS)
    db.commit()
    db.refresh(otpElement)

    url = "https://bulksms.bsnl.in:5010/api/Send_SMS"

    responseBSNL = requests.post(url, headers={
        "Authorization": f"Bearer {BSNL_AUTH}",
        "Content-Type": "application/json;charset=utf-8"
    }, data=json.dumps({
        "Header": "NITBPL",
        "Target": otp_request.phone,
        "Is_Unicode": "0",
        "Is_Flash": "0",
        "Message_Type": "SI",
        "Entity_Id": ENTITY_ID,
        "Content_Template_Id": TEMPLATE_ID,
        "Template_Keys_and_Values": [{
            "Key": "var",
            "Value": otpElement.otp
        }]
    }))

    response.status_code = responseBSNL.status_code

    return otp_request.phone


@app.post("/login/verify")
def verifyLogin(login_verify_request: LoginVerifyRequest, db: Session = Depends(get_db)):
    if db.query(models.Userbase).filter(models.Userbase.id == login_verify_request.user_id).first() is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Signup first.")
    otp_element: models.OTP = db.query(models.OTP).filter(models.OTP.id == login_verify_request.id).first()
    if login_verify_request.otp == otp_element.otp:
        token = secrets.token_hex(32)
        user: models.Tokens = db.query(models.Tokens).filter(models.Tokens.user == login_verify_request.id).first()
        if user is None:
            user = models.Tokens(
                idtokens=token,
                time=int(time.time()) + 31556926,
                user=login_verify_request.id
            )
            db.add(user)
        else:
            user.idtokens = token
            user.time = int(time.time()) + 31556926

        db.query(models.OTP).filter(models.OTP.id == login_verify_request.id).delete()
        db.commit()
        db.refresh(user)
        return token
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@app.post("/signup/verify")
def signup(signup_request: SignupRequest, db: Session = Depends(get_db)):
    otp_element: models.OTP = db.query(models.OTP).filter(models.OTP.id == signup_request.id).first()
    if signup_request.otp == otp_element.otp:
        userbase_element = models.Userbase(
            id=signup_request.id,
            name=signup_request.name,
            phone=signup_request.phone,
            usergroup=0
        )
        db.add(userbase_element)
        db.commit()
        db.refresh(userbase_element)
        token = secrets.token_hex(32)
        user: models.Tokens = db.query(models.Tokens).filter(models.Tokens.user == signup_request.id).first()
        if user is None:
            user = models.Tokens(
                idtokens=token,
                time=int(time.time()) + 31556926,
                user=signup_request.id
            )
            db.add(user)
        else:
            user.idtokens = token
        db.commit()
        db.refresh(user)
        return token
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@app.get("/get/locations")
def getLocation():
    return FileResponse("locations.json")


@app.get("/download")
def download():
    return FileResponse(LATEST_APP_PATH)


@app.get("/version")
def version():
    return FileResponse(VERSION_FILE)
