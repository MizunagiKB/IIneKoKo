import uuid
import datetime

import pydantic
import typing

import pytz

import iinekoko_db

DATABASE_NAME = "iinekoko_session"


class CModelSession(pydantic.BaseModel):
    id: typing.Optional[str] = pydantic.Field(alias="_id")
    ref: typing.Optional[str] = pydantic.Field(alias="_ref")
    tw_id: str
    tw_username: str
    default_profile_image: bool
    profile_image_url_https: str
    referer: typing.Optional[str] = ""
    created_at: typing.Optional[datetime.datetime] = datetime.datetime.now(
        pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
    modified_at: typing.Optional[datetime.datetime] = datetime.datetime.now(
        pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


def create(o_db: iinekoko_db.CDatabase, o_sess: CModelSession):
    if o_db.o_conn is not None:
        o_doc = o_db.o_conn[DATABASE_NAME].create_document(
            o_sess.dict(by_alias=True, exclude_none=True))
        if o_doc.exists() is not True:
            o_doc = None
    else:
        o_doc = None

    return o_doc


def get(o_db: iinekoko_db.CDatabase, document_id: str):
    try:
        if o_db.o_conn is not None:
            o_doc = o_db.o_conn[DATABASE_NAME][document_id]
            print(o_doc)
            if o_doc.exists() is not True:
                o_doc = None
        else:
            o_doc = None
    except KeyError:
        o_doc = None
    except AttributeError:
        o_doc = None

    return o_doc


# [EOF]
