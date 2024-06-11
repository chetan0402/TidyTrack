from fastapi import Request, Response

import re
from schema import *
import asyncio


def validUUID(string) -> bool:
    return re.fullmatch(r'[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}', string).string == string


def verifyRequestUUID(func):
    def wrapper(request: Request,response: Response, *args, **kwargs):
        ticket_id = asyncio.run(request.json())['id']
        if not validUUID(ticket_id):
            response.status_code = 400
            return Message(message="Invalid UUID")
        return func(*args, **kwargs)

    return wrapper
