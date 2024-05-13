from pydantic import BaseModel


class AdminModel(BaseModel):
    user: str
    pswd: str

    class Config:
        from_attributes = True


class MainModel(BaseModel):
    feedback: str
    imgpath: str
    rating: int
    locationcode: str
    time: int
    schno: str

    class Config:
        from_attributes = True


class TokensModel(BaseModel):
    idtokens: str
    time: int
    user: str

    class Config:
        from_attributes = True


class UserbaseModel(BaseModel):
    name: str
    id: str
    phone: int

    class Config:
        from_attributes = True


class OTPRequest(BaseModel):
    id: str

    class Config:
        from_attributes = True


class LoginVerifyRequest(BaseModel):
    id: str
    otp: int
    name: str

    class Config:
        from_attributes = True


class SignupRequest(BaseModel):
    id: str
    name: str
    phone: int

    class Config:
        from_attributes = True
