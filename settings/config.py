import json

from pydantic import BaseModel


class Config(BaseModel):
    BSNL_AUTH: str
    TEMPLATE_ID: str
    ENTITY_ID: str
    LATEST_APP_PATH: str
    TARGET_PHOTO_SIZE: int
    VERSION_FILE: str
    loaded: bool = False


def get_config() -> Config:
    with open("config.json", "r") as file:
        config = json.load(file)
        return Config(**config)
