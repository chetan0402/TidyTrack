from pydantic import BaseModel
from typing import Optional


class UserbaseModel(BaseModel):
    name: str
    id: str
    phone: int
    usergroup: int
    subgroup: int = -1

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

    class Config:
        from_attributes = True


class ProfileRequest(BaseModel):
    token: str

    class Config:
        from_attributes = True


class SweeperReport(BaseModel):
    uuid: str
    token: str
    location: str
    img: str

    class Config:
        from_attributes = True


class MyReportsRequest(BaseModel):
    token: str
    offset: int = 0

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


class MyReportsResponse(BaseModel):
    reports: list[MyReports]

    class Config:
        from_attributes = True


class GraphDataRequest(BaseModel):
    from_time: int
    to_time: int
    location: str
    token: str

    class Config:
        from_attributes = True


class GraphData(BaseModel):
    time: int
    rating: int

    class Config:
        from_attributes = True


class GraphDataResponse(BaseModel):
    data: list[GraphData]

    class Config:
        from_attributes = True


class ReportEditRequest(BaseModel):
    ticket_id: str
    status: int
    token: str


class GenerateReportRequest(BaseModel):
    token: str
    location: str
    from_time: int
    to_time: int
    report_type: int

    class Config:
        from_attributes = True
