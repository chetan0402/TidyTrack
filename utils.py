from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pathlib import Path
from PIL import Image
import io
import base64
import re
import time
from datetime import datetime

from sqlalchemy.sql.operators import and_

import constants.ReportType
import models
import time
from fastapi.exceptions import HTTPException
from starlette import status
from schema import *
from typing import Union, Type
from fastapi import Header, Depends
from database import get_db

ExceptionReturnDocs = {"model": ExceptionReturn}
ReportReturnDocs = {400: ExceptionReturnDocs, 403: ExceptionReturnDocs}


def getSubGroup(db: Session, user_id: str):
    return db.query(models.UserbaseAttr).filter(models.UserbaseAttr.id == user_id).first().subgroup


def getUserInHeaderVerified(user_groups: list):
    def dependency(authorization: str = Header(None), db: Session = Depends(get_db)) -> str:
        if authorization is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization Required")
        if getUserFromToken(db, re.search(r"Bearer (\S+)", authorization).group(1)).usergroup in user_groups:
            return re.search(r"Bearer (\S+)", authorization).group(1)

    return dependency


def convertTime(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def validUUID(string) -> bool:
    try:
        return re.fullmatch(r'[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}',
                            string).string == string
    except AttributeError:
        return False


def clean_string(string) -> str:
    return re.sub(r'[^\x00-\x20\x2C\x2E\x30-\x39\x41-\x5A\x61-\x7A]', '', string)


def clean_otp(db: Session):
    db.query(models.OTP).filter(models.OTP.deleteTime < int(time.time())).delete()
    db.commit()


def getUserFromID(db: Session, user_id: str) -> models.Userbase:
    return db.query(models.Userbase).filter(models.Userbase.id == user_id).first()


def getUserFromPhone(db: Session, phone: int) -> models.Userbase:
    return db.query(models.Userbase).filter(models.Userbase.phone == phone).first()


def getUserFromToken(db: Session, token: str) -> models.Userbase:
    user_session: models.Tokens = db.query(models.Tokens).filter(models.Tokens.idtokens == token).first()
    if user_session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user: models.Userbase = db.query(models.Userbase).filter(models.Userbase.id == user_session.user).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return user


def verifyGroup(user: models.Userbase, group_to_verify: int):
    if user.usergroup != group_to_verify:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User Group mismatch")


def addReport(db: Session, report_element: Union[BaseReport, WithImgReport],
              report_type: constants.ReportType.ReportType) -> Message:
    if not validUUID(report_element.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    user = getUserFromToken(db, report_element.token)
    verifyGroup(user, 0)

    report_time = int(time.time())
    local_path = ""

    if report_type == constants.ReportType.ReportType.FOOD:
        local_path = "food.png"
    elif report_type == constants.ReportType.ReportType.WATER:
        local_path = "water.png"
    elif report_type == constants.ReportType.ReportType.OTHER:
        local_path = "other.png"
    if isinstance(report_element, WithImgReport):
        local_path = f"{report_type.name.lower()}-{report_time}-{user.id}.png"
    report = models.Report(
        ticket_id=report_element.id,
        location=report_element.location,
        selected=report_element.selected,
        other=clean_string(report_element.other),
        img=local_path,
        time=report_time,
        user=user.id,
        type=report_type.value,
        rating=report_element.rating
    )
    try:
        db.add(report)
        db.commit()
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please report to the developer.")
    if isinstance(report_element, WithImgReport):
        saveIMG(report_element.img, local_path)
        if not imgExist(local_path):
            print("===IMG-SAVE-FAIL===")
            print(report_element.model_dump_json())
            print("===================")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    db.refresh(report)

    return Message(message=report_element.id)


def getReport(db: Session, location: Union[str, None], from_time: int, to_time: int,
              report_type: constants.ReportType.ReportType, limit: int = 20, offset: int = 0) -> list[
    Type[models.Report]]:
    if location is None:
        return db.query(models.Report).filter(and_(
            models.Report.time.between(from_time, to_time),
            models.Report.type == report_type.value)).offset(offset * 20).limit(limit).all()
    else:
        return db.query(models.Report).filter(and_(and_(
            models.Report.time.between(from_time, to_time),
            models.Report.type == report_type.value),
            models.Report.location == location)).offset(offset * 20).limit(limit).all()


def getReportFromUser(db: Session, token: str, limit: int = 20, offset: int = 0) -> list[Type[models.Report]]:
    user = getUserFromToken(db, token)
    return db.query(models.Report).filter(models.Report.user == user.id).offset(offset * 20).limit(limit).all()


def saveIMG(img_string: str, local_path: str) -> None:
    img_path = Path.home().joinpath("img").joinpath(local_path.lower())
    img = Image.open(io.BytesIO(base64.b64decode(img_string.replace("\\n", "").replace("\\", ""))))
    img_buffer = io.BytesIO()
    quality = 100
    while quality > 0:
        img.save(img_buffer, "PNG", quality=quality)
        from fastapi_app import config
        if img_buffer.tell() <= config.TARGET_PHOTO_SIZE * 1024 * 1024:
            break
        quality -= 5
        img_buffer.seek(0)
        img_buffer.truncate()

    img.save(img_path, "PNG", quality=quality)


def imgExist(local_path: str) -> bool:
    return Path.home().joinpath("img").joinpath(local_path.lower()).exists()
