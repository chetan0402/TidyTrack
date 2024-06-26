from pydantic import BaseModel
from typing import Optional


class AdminModel(BaseModel):
    user: str
    pswd: str

    class Config:
        from_attributes = True


class UserbaseModel(BaseModel):
    name: str
    id: str
    phone: int
    usergroup: int

    class Config:
        from_attributes = True


class OTPRequest(BaseModel):
    id: Optional[str] = None
    role: int
    phone: int

    class Config:
        from_attributes = True


class LoginVerifyRequest(BaseModel):
    phone: int
    otp: int
    role: int

    class Config:
        from_attributes = True


class SignupRequest(BaseModel):
    id: str
    name: str
    phone: int
    otp: int

    class Config:
        from_attributes = True


class BaseReport(BaseModel):
    id: str
    token: str
    location: str
    selected: int
    other: str
    rating: int

    class Config:
        from_attributes = True


class WithImgReport(BaseReport):
    img: str

    class Config:
        from_attributes = True


class Message(BaseModel):
    message: str

    class Config:
        from_attributes = True


class ExceptionReturn(BaseModel):
    detail: str

    class Config:
        from_attributes = True


class Test(BaseModel):
    id: str


class ProfileRequest(BaseModel):
    token: str


class SweeperReport(BaseModel):
    uuid: str
    token: str
    location: str
    img: str


class MyReportsRequest(BaseModel):
    token: str
    offset: int = 0


class MyReports(BaseModel):
    ticket_id: str
    location: str
    selected: int
    other: str
    img: str
    time: int
    type: int
    rating: int
    status: int


class MyReportsResponse(BaseModel):
    reports: list[MyReports]
