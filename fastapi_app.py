import json
import random
import secrets
import subprocess
import time

import requests
from fastapi import FastAPI, Depends, Response, status, Request
from fastapi.responses import FileResponse

import settings.config
import models
from database import SessionLocal
from schema import *
from utils import *
from constants.ReportType import *


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# TODO - implement validation rule
def isValidId(id: str) -> bool:
    return True


app = FastAPI()
config = settings.config.get_config()
if not config.loaded:
    raise Exception("Config not loaded")


@app.get("/")
def homePage():
    return FileResponse("templates/index.html")


@app.post("/internet/report", tags=["report"], response_model=Message, responses=ReportReturnDocs)
def internetReport(internet_report: WithImgReport, response: Response, db: Session = Depends(get_db)):
    return addReport(db, report_element=internet_report, report_type=ReportType.INTERNET)


@app.post("/food/report", tags=["report"], response_model=Message, responses=ReportReturnDocs)
def foodReport(food_report_request: BaseReport, db: Session = Depends(get_db)):
    return addReport(db, report_element=food_report_request, report_type=ReportType.FOOD)


@app.post("/washroom/report", tags=["report"], response_model=Message, responses=ReportReturnDocs)
def washroomReport(washroom_report: WithImgReport, db: Session = Depends(get_db)):
    return addReport(db, report_element=washroom_report, report_type=ReportType.WASHROOM)


@app.post("/water/report", tags=["report"], response_model=Message, responses=ReportReturnDocs)
def waterReport(water_report_request: BaseReport, db: Session = Depends(get_db)):
    return addReport(db, report_element=water_report_request, report_type=ReportType.WATER)


@app.post("/cleaning/report", tags=["report"], response_model=Message, responses=ReportReturnDocs)
def cleaningReport(cleaning_report: WithImgReport, db: Session = Depends(get_db)):
    return addReport(db, report_element=cleaning_report, report_type=ReportType.WASHROOM)


@app.post("/other/report", tags=["report"], response_model=Message, responses=ReportReturnDocs)
def otherReport(other_report: BaseReport, db: Session = Depends(get_db)):
    return addReport(db, report_element=other_report, report_type=ReportType.WASHROOM)


@app.post("/otp/send", tags=["account"], response_model=Message, responses={
    400: {
        "model": Message
    },
    429: {
        "model": Message
    }
})
def otpSend(otp_request: OTPRequest, response: Response, db: Session = Depends(get_db)):
    # Commenting everything cuz this workflow is hard to understand.
    clean_otp(db)
    # If there is no id in the request, it means that the request must be a login request
    if otp_request.id is None:
        # Login workflow
        # Verify if the user exists
        user = getUserFromPhone(db, otp_request.phone)
        if user is None:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return Message(message="Signup First")

        # Verify the role
        if user.usergroup != otp_request.role:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return Message(message="Invalid Role")

        otp_request.id = user.id
    else:
        # Signup Workflow
        # verify if the ID is allowed to register
        if not isValidId(otp_request.id):
            response.status_code = status.HTTP_400_BAD_REQUEST
            return Message(message="Invalid ID")

        # Check if the user already exists in the userbase and reject if it does
        user = getUserFromID(db, otp_request.id)
        if user is not None:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return Message(message="Account already exists. Please login instead")

    otp_element = db.query(models.OTP).filter(models.OTP.id == otp_request.id).first()
    if otp_element is None:
        otp_element = models.OTP(
            id=otp_request.id,
            role=otp_request.role,
            tries=1,
            otp=random.randint(100000, 999999),
            firstTime=int(time.time()),
            deleteTime=int(time.time()) + (60 * 60),
            nextSendTime=int(time.time()) + (2 * 60)
        )
        db.add(otp_element)
    else:
        if int(time.time()) < otp_element.nextSendTime:
            response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
            return Message(message="Wait for a few seconds. Try again later")
        otp_element.tries += 1
        otp_element.nextSendTime = int(time.time()) + (2 * 60)
        if otp_element.tries == 4:
            response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
            return Message(message="Too many requests. Please try again in an hour")
    db.commit()
    db.refresh(otp_element)

    url = "https://bulksms.bsnl.in:5010/api/Send_SMS"

    response_bsnl = requests.post(url, headers={
        "Authorization": f"Bearer {config.BSNL_AUTH}",
        "Content-Type": "application/json;charset=utf-8"
    }, data=json.dumps({
        "Header": "NITBPL",
        "Target": otp_request.phone,
        "Is_Unicode": "0",
        "Is_Flash": "0",
        "Message_Type": "SI",
        "Entity_Id": config.ENTITY_ID,
        "Content_Template_Id": config.TEMPLATE_ID,
        "Template_Keys_and_Values": [{
            "Key": "var",
            "Value": otp_element.otp
        }]
    }))

    response.status_code = response_bsnl.status_code
    return Message(message=str(otp_request.phone))


@app.post("/login/verify", tags=["account"], response_model=Message, responses={
    400: {
        "model": Message
    },
    401: {
        "description": "Wrong OTP",
        "model": Message
    }
})
def verifyLogin(login_verify_request: LoginVerifyRequest, response: Response, db: Session = Depends(get_db)):
    userbase = getUserFromPhone(db, login_verify_request.phone)
    if userbase is None:
        # 400
        response.status_code = status.HTTP_400_BAD_REQUEST
        return Message(message="Account does not exist")
    else:
        if userbase.usergroup != login_verify_request.role:
            # 400
            response.status_code = status.HTTP_400_BAD_REQUEST
            return Message(message="Selected Role - Registered Role mismatch")

    otp_element: models.OTP = db.query(models.OTP).filter(models.OTP.id == userbase.id).first()
    if login_verify_request.otp == otp_element.otp:
        token = secrets.token_hex(32)
        user: models.Tokens = db.query(models.Tokens).filter(models.Tokens.user == userbase.id).first()
        if user is None:
            user = models.Tokens(
                idtokens=token,
                time=int(time.time()) + 31556926,
                user=userbase.id
            )
            db.add(user)
        else:
            user.idtokens = token
            user.time = int(time.time()) + 31556926

        db.query(models.OTP).filter(models.OTP.id == userbase.id).delete()
        db.commit()
        db.refresh(user)
        # 200
        return Message(message=token)
    else:
        # 401
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return Message(message="Wrong OTP")


@app.post("/signup/verify", tags=["account"], response_model=Message,
          responses={
              401: {
                  "model": Message
              }
          })
def signup(signup_request: SignupRequest, response: Response, db: Session = Depends(get_db)):
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
        return Message(message=token)
    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return Message(message="Wrong OTP")


@app.post("/profile", tags=["account"], response_model=UserbaseModel, responses={
    401: ExceptionReturnDocs,
    422: ExceptionReturnDocs
})
def profile(profile_request: ProfileRequest, db: Session = Depends(get_db)):
    return getUserFromToken(db, profile_request.token)


@app.get("/get/locations")
def getLocation():
    return FileResponse("locations.json")


@app.get("/locations/mess")
def messLocation():
    return FileResponse(Path.home().joinpath("constants").joinpath("location_mess.json"))


@app.get("/download")
def download():
    return FileResponse(config.LATEST_APP_PATH)


@app.get("/version")
def version():
    return FileResponse(config.VERSION_FILE)


@app.post("/test", description="Use this endpoint to test that your application is sending uuid correctly and the "
                               "server is reading it")
def test(test_request: Test):
    validUUID(test_request.id)
    return Message(message="successful!")


@app.post("/update/code", include_in_schema=False)
async def reloadCode():
    subprocess.run(["git", "pull"])
    return Message(message="Updated!")
