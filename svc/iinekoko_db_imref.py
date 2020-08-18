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
import iinekoko_db_immrk

DATABASE_NAME = "iinekoko_imref"
IMAGE_MAX_W = 512
IMAGE_MAX_H = 512
IMAGE_THUMB_W = 32
IMAGE_THUMB_H = 32


class CModelIMRef(pydantic.BaseModel):
    id: str = pydantic.Field(default=uuid.uuid4().hex, alias="_id")
    ref: typing.Optional[str] = pydantic.Field(default=None, alias="_ref")
    tw_id: typing.Optional[pydantic.constr(strip_whitespace=True)]
    tw_username: typing.Optional[pydantic.constr(strip_whitespace=True)]
    title: pydantic.constr(strip_whitespace=True)
    desc_r: pydantic.constr(strip_whitespace=True)
    desc_g: pydantic.constr(strip_whitespace=True)
    desc_b: pydantic.constr(strip_whitespace=True)
    image_ref: typing.Any
    hex_hash: typing.Optional[pydantic.constr(strip_whitespace=True)]
    created_at: typing.Optional[datetime.datetime] = datetime.datetime.now(
        pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
    modified_at: typing.Optional[datetime.datetime] = datetime.datetime.now(
        pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


def create(o_db: iinekoko_db.CDatabase, o_doc_sess, o_imref: CModelIMRef,
           image_dir: str):

    mime, dec_data = dict_image_b64dec(o_imref.image_ref)
    hex_hash = hashlib.sha1(dec_data).hexdigest()

    o_image = PIL.Image.open(io.BytesIO(dec_data))
    o_image.save(os.path.join(image_dir, hex_hash + ".jpeg"), "JPEG")
    o_image.thumbnail((IMAGE_THUMB_W, IMAGE_THUMB_H))
    o_image.save(os.path.join(image_dir, hex_hash + "_thumb.jpeg"), "JPEG")

    o_imref.tw_id = o_doc_sess["tw_id"]
    o_imref.tw_username = o_doc_sess["tw_username"]
    o_imref.hex_hash = hex_hash
    o_imref.id = "x".join((o_imref.hex_hash, o_imref.tw_id))

    assert o_imref.tw_id is not None
    assert o_imref.tw_username is not None
    assert o_imref.hex_hash is not None

    list_col_desc = []

    if len(o_imref.desc_r) > 0:
        list_col_desc.append({"name": "R", "value": o_imref.desc_r})
    if len(o_imref.desc_g) > 0:
        list_col_desc.append({"name": "G", "value": o_imref.desc_g})
    if len(o_imref.desc_b) > 0:
        list_col_desc.append({"name": "B", "value": o_imref.desc_b})

    o_doc = o_db.o_conn[DATABASE_NAME].create_document(
        o_imref.dict(
            exclude={"image_ref"},
            by_alias=True,
            exclude_none=True,
        ))
    if o_doc.exists() is False:
        o_doc = None

    return o_doc


def delete(o_db: iinekoko_db.CDatabase, o_doc_sess, document_id: str,
           image_dir: str):

    o_doc_imref = get(o_db, document_id)
    if o_doc_imref is not None:
        o_doc_imref.fetch()
        if o_doc_imref["tw_id"] == o_doc_sess["tw_id"]:
            for ext in ("_thumb.jpeg", ".jpeg"):
                try:
                    os.remove(
                        os.path.join(image_dir, o_doc_imref["hex_hash"]) + ext)
                except FileNotFoundError:
                    pass

            iinekoko_db_immrk.delete(o_db, o_doc_sess, o_doc_imref["_id"])

            o_doc_imref.delete()


def get(o_db: iinekoko_db.CDatabase, document_id: str):
    try:
        o_doc = o_db.o_conn[DATABASE_NAME][document_id]
    except KeyError:
        o_doc = None

    return o_doc


def get_list(o_db: iinekoko_db.CDatabase, o_doc_sess):

    list_result = o_db.o_conn[DATABASE_NAME].get_view_result(
        "image_ref",
        "list",
        startkey=[o_doc_sess["tw_id"], ""],
        endkey=[o_doc_sess["tw_id"], "Z"],
    )

    return [r for r in list_result]


def dict_image_b64enc(mime, dec_data):

    result = "data:" + mime + ";base64,"
    return result + base64.b64encode(dec_data).decode("utf-8")


def dict_image_b64dec(enc_data):

    # data:*/*;base64,...
    o_re = re.search("^data:(.*?);base64,(.*)$", enc_data)
    if o_re is not None:
        mime = o_re.group(1)
        enc_data = o_re.group(2)

        dec_data = base64.b64decode(enc_data)

        o_image = PIL.Image.open(io.BytesIO(dec_data))
        im_w, im_h = o_image.size

        if (im_w > IMAGE_MAX_W) or (im_h > IMAGE_MAX_H):
            o_image.thumbnail((IMAGE_MAX_W, IMAGE_MAX_H))

        f = io.BytesIO()
        o_image.save(f, "JPEG")
        raw_data = f.getvalue()

        return mime, raw_data

    return None, None


# [EOF]
