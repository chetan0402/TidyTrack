import secrets

from fastapi import FastAPI, Depends, Response, status, HTTPException
from fastapi.responses import FileResponse
from database import SessionLocal
from sqlalchemy.orm import Session
from schema import *
import json
import requests
import models
import random
import time
from contextlib import asynccontextmanager
import asyncio
from global_config import *


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.create_task(clean_otp())
    yield


app = FastAPI(lifespan=lifespan)


# TODO - implement validation rule
def isValidId(id: str) -> bool:
    return True


@app.get("/")
def homePage():
    return FileResponse("templates/index.html")


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
