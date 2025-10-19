from typing import Literal

from pydantic import BaseModel


class AdminDeterminesIMDBTMDBIdPayload(BaseModel):
    provider_url: str


class AdminDeterminesIMDBTMDBIdError(BaseModel):
    error_code: str


class AdminDeterminesIMDBTMDBIdRawItemNotFoundError(AdminDeterminesIMDBTMDBIdError):
    error_code: Literal["raw-item-not-found"] = "raw-item-not-found"


class AdminDeterminesIMDBTMDBIdValueError(AdminDeterminesIMDBTMDBIdError):
    error_code: Literal["value-error"] = "value-error"
    message: str
