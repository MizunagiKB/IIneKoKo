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


class CModelIMMrk(pydantic.BaseModel):
    id: typing.Optional[str] = pydantic.Field(default=None, alias="_id")
    ref: typing.Optional[str] = pydantic.Field(default=None, alias="_ref")
    tw_id: typing.Optional[pydantic.constr(strip_whitespace=True)]
    tw_username: typing.Optional[pydantic.constr(strip_whitespace=True)]
    id_imref: str
    x: int
    y: int
    size: int
    created_at: typing.Optional[str]
    modified_at: typing.Optional[str]


def create(o_db: iinekoko_db.CDatabase, o_doc_sess, o_immrk: CModelIMMrk):

    o_immrk.tw_id = o_doc_sess["tw_id"]
    o_immrk.tw_username = o_doc_sess["tw_username"]
    o_immrk.id = "x".join((o_immrk.id_imref, o_immrk.tw_id))
    o_immrk.created_at = datetime.datetime.now(
        pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
    o_immrk.modified_at = o_immrk.created_at

    assert o_immrk.tw_id is not None
    assert o_immrk.tw_username is not None
    assert o_immrk.id_imref is not None

    o_doc = o_db.o_conn[DATABASE_NAME].create_document(
        o_immrk.dict(
            by_alias=True,
            exclude_none=True,
        ))
    if o_doc.exists() is False:
        o_doc = None

    return o_doc


def delete_rel_imref(o_db: iinekoko_db.CDatabase, o_doc_sess,
                     id_image_ref: str):

    list_result = o_db.o_conn[DATABASE_NAME].get_view_result("image_mrk",
                                                             "list_for_delete",
                                                             key=id_image_ref)

    o_db.o_conn[DATABASE_NAME].bulk_docs([{
        "_id": r["id"],
        "_rev": r["value"],
        "_deleted": True
    } for r in list_result.all()])


def get(o_db: iinekoko_db.CDatabase, o_doc_sess, id_imref: str):

    document_id = "x".join((id_imref, o_doc_sess["tw_id"]))

    try:
        o_doc = o_db.o_conn[DATABASE_NAME][document_id]
        if o_doc.exists() is not True:
            o_doc = None
    except KeyError:
        o_doc = None

    return o_doc


def get_list(o_db: iinekoko_db.CDatabase,
             id_immrk: str,
             include_docs: bool = False):

    list_result = o_db.o_conn[DATABASE_NAME].get_view_result(
        "image_mrk",
        "list",
        descending=True,
        include_docs=include_docs,
        startkey=[id_immrk, "Z"],
        endkey=[id_immrk, ""],
        limit=100)

    return [r for r in list_result.all()]


# [EOF]
