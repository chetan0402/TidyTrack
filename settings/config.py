import json
from pathlib import Path

from pydantic import BaseModel


class Config(BaseModel):
    BSNL_AUTH: str
    TEMPLATE_ID: str
    ENTITY_ID: str
    LATEST_APP_PATH: str
    TARGET_PHOTO_SIZE: int
    VERSION_FILE: str
    SQLALCHEMY_DATABASE_URL: str
    loaded: bool = False
    debug: bool = False


config_obj = None


def get_config() -> Config:
    global config_obj
    if config_obj is None:
        with open(Path.home().joinpath("settings").joinpath("config.json"), "r") as file:
            config_obj = json.load(file)
            return Config(**config_obj)
    else:
        return Config(**config_obj)


def reload_config() -> Config:
    global config_obj
    config_obj = None
    return get_config()
