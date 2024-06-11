from fastapi import Request, Response

import re
from schema import *
import asyncio
from functools import wraps


def validUUID(string) -> bool:
    try:
        return re.fullmatch(r'[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}', string).string == string
    except AttributeError:
        return False


def verifyRequestUUID(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(args)
        print(kwargs)
        if not validUUID(kwargs.get('test_request').id):
            kwargs.get("response").status_code = 400
            return Message(message="Invalid UUID")
        return func(*args, **kwargs)

    return wrapper
