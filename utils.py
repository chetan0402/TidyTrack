from sqlalchemy.orm import Session
from pathlib import Path
from PIL import Image
import io
import base64
import re

import constants.ReportType
import models
import time
from fastapi.exceptions import HTTPException
from starlette import status
from schema import *
from typing import Union


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


def addReport(db: Session, report_element: Union[BaseReport,WithImgReport], report_time: int, userid: str,
              local_path: str, report_type: constants.ReportType.ReportType) -> None:
    report_element = models.Report(
        ticket_id=report_element.id,
        location=report_element.location,
        selected=report_element.selected,
        other=clean_string(report_element.other),
        img=local_path,
        time=report_time,
        user=userid,
        type=report_type.value
    )
    db.add(report_element)
    if isinstance(report_element, WithImgReport):
        saveIMG(report_element.img, local_path)
    db.commit()
    db.refresh(report_element)


def saveIMG(img_string: str, local_path: str) -> None:
    img_path = Path.home().joinpath("img").joinpath(local_path)
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
