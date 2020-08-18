import uuid
import datetime
import hashlib
import base64
import os
import io
import re

import pydantic
import typing

import pytz
import PIL.Image

import iinekoko_db

DATABASE_NAME = "iinekoko_immrk"


class CModelIMMrkDesc(pydantic.BaseModel):
    name: str
    shape_type: str
    left: typing.Optional[int]
    right: typing.Optional[int]
    top: typing.Optional[int]
    bottom: typing.Optional[int]
    radius: typing.Optional[int]


class CModelIMMrk(pydantic.BaseModel):
    id: str = pydantic.Field(default=uuid.uuid4().hex, alias="_id")
    ref: typing.Optional[str] = pydantic.Field(default=None, alias="_ref")
    tw_id: typing.Optional[pydantic.constr(strip_whitespace=True)]
    tw_username: typing.Optional[pydantic.constr(strip_whitespace=True)]
    mark_r: typing.Optional[CModelIMMrkDesc]
    mark_g: typing.Optional[CModelIMMrkDesc]
    mark_b: typing.Optional[CModelIMMrkDesc]
    hex_hash: str
    created_at: typing.Optional[datetime.datetime] = datetime.datetime.now(
        pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
    modified_at: typing.Optional[datetime.datetime] = datetime.datetime.now(
        pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


def append(o_db: iinekoko_db.CDatabase, o_doc_sess, o_immrk: CModelIMMrk):

    o_immrk.tw_id = o_doc_sess["tw_id"]
    o_immrk.tw_username = o_doc_sess["tw_username"]
    o_immrk.id = "x".join((o_immrk.hex_hash, o_immrk.tw_id))

    assert o_immrk.tw_id is not None
    assert o_immrk.tw_username is not None
    assert o_immrk.hex_hash is not None

    o_doc = o_db.o_conn[DATABASE_NAME].create_document(
        o_immrk.dict(
            by_alias=True,
            exclude_none=True,
        ))
    if o_doc.exists() is False:
        o_doc = None

    return o_doc


def delete(o_db: iinekoko_db.CDatabase, o_doc_sess, hex_hash: str):

    list_result = o_db.o_conn[DATABASE_NAME].get_view_result("image_mrk",
                                                             "list_for_delete",
                                                             key=hex_hash)

    o_db.o_conn[DATABASE_NAME].bulk_docs([{
        "_id": r["id"],
        "_rev": r["value"],
        "_deleted": True
    } for r in list_result.all()])


def get(o_db: iinekoko_db.CDatabase, o_doc_sess, hex_hash: str):

    document_id = "x".join((hex_hash, o_doc_sess["tw_id"]))

    try:
        o_doc = o_db.o_conn[DATABASE_NAME][document_id]
    except KeyError:
        o_doc = None

    return o_doc


def get_list(o_db: iinekoko_db.CDatabase, o_doc_sess, hex_hash: str):

    document_id = "x".join((hex_hash, o_doc_sess["tw_id"]))

    list_result = o_db.o_conn[DATABASE_NAME].get_view_result(
        "image_mrk",
        "list",
        startkey=[hex_hash, ""],
        endkey=[hex_hash, "Z"],
        limit=100)

    return [r for r in list_result.all() if r["id"] != document_id]


def get_list_all(o_db: iinekoko_db.CDatabase, o_doc_sess, hex_hash: str):

    list_result = o_db.o_conn[DATABASE_NAME].get_view_result(
        "image_mrk",
        "list",
        startkey=[hex_hash, ""],
        endkey=[hex_hash, "Z"],
        limit=100)

    return [r for r in list_result.all()]


# [EOF]
