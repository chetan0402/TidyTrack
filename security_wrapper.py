from fastapi import HTTPException
from pydantic import BaseModel

import re
from schema import *
from functools import wraps


def validUUID(string) -> bool:
    try:
        return re.fullmatch(r'[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}',
                            string).string == string
    except AttributeError:
        return False


def verifyRequestUUID(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = None
        for arg in kwargs.values():
            if isinstance(arg, BaseModel):
                request = arg
        if request is None:
            raise HTTPException(status_code=501)

        if not validUUID(request.id):
            kwargs.get("response").status_code = 400
            return Message(message="Invalid UUID")
        return func(*args, **kwargs)

    return wrapper
