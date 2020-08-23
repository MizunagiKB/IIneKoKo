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
IMAGE_THUMB_W = 64
IMAGE_THUMB_H = 64


class CModelIMRef(pydantic.BaseModel):
    id: typing.Optional[str] = pydantic.Field(default=None, alias="_id")
    ref: typing.Optional[str] = pydantic.Field(default=None, alias="_ref")
    tw_id: typing.Optional[pydantic.constr(strip_whitespace=True)]
    tw_username: typing.Optional[pydantic.constr(strip_whitespace=True)]
    default_profile_image: typing.Optional[bool] = True
    profile_image_url_https: typing.Optional[str] = ""
    title: pydantic.constr(strip_whitespace=True, max_length=64)
    image_ref: typing.Any
    created_at: typing.Optional[datetime.datetime] = datetime.datetime.now(
        pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
    modified_at: typing.Optional[datetime.datetime] = datetime.datetime.now(
        pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


def create(o_db: iinekoko_db.CDatabase, o_doc_sess, o_imref: CModelIMRef,
           image_dir: str):

    mime, dec_data = dict_image_b64dec(o_imref.image_ref)

    o_imref.tw_id = o_doc_sess["tw_id"]
    o_imref.tw_username = o_doc_sess["tw_username"]
    o_imref.default_profile_image = o_doc_sess["default_profile_image"]
    o_imref.profile_image_url_https = o_doc_sess["profile_image_url_https"]

    o_doc = o_db.o_conn[DATABASE_NAME].create_document(
        o_imref.dict(
            exclude={"image_ref"},
            by_alias=True,
            exclude_none=True,
        ))
    if o_doc.exists() is True:
        basic = io.BytesIO()
        thumb = io.BytesIO()

        o_image = PIL.Image.open(io.BytesIO(dec_data))
        o_image.save(basic, "JPEG")
        o_image.thumbnail((IMAGE_THUMB_W, IMAGE_THUMB_H))
        o_image.save(thumb, "JPEG")

        with open(os.path.join(image_dir, o_doc["_id"]) + "-basic.jpeg",
                  "wb") as f:
            # o_doc.put_attachment("basic", "image/jpeg", basic.getvalue())
            f.write(basic.getvalue())
        with open(os.path.join(image_dir, o_doc["_id"]) + "-thumb.jpeg",
                  "wb") as f:
            # o_doc.put_attachment("thumb", "image/jpeg", thumb.getvalue())
            f.write(thumb.getvalue())
    else:
        o_doc = None

    return o_doc


def delete(o_db: iinekoko_db.CDatabase, o_doc_sess, document_id: str,
           image_dir: str):

    o_doc_imref = get(o_db, document_id)
    if o_doc_imref is not None:
        if o_doc_imref["tw_id"] == o_doc_sess["tw_id"]:
            for suf in ("-basic.jpeg", "-thumb.jpeg"):
                try:
                    os.remove(
                        os.path.join(image_dir, o_doc_imref["_id"]) + suf)
                except FileNotFoundError:
                    pass

            iinekoko_db_immrk.delete_rel_imref(o_db, o_doc_sess,
                                               o_doc_imref["_id"])

            o_doc_imref.delete()


def get(o_db: iinekoko_db.CDatabase, document_id: str):
    try:
        o_doc = o_db.o_conn[DATABASE_NAME][document_id]
        if o_doc.exists() is not True:
            o_doc = None
    except KeyError:
        o_doc = None

    return o_doc


def get_list(o_db: iinekoko_db.CDatabase,
             o_doc_sess,
             startkey,
             endkey,
             descending=False):

    list_result = o_db.o_conn[DATABASE_NAME].get_view_result(
        "image_ref",
        "list",
        startkey=startkey,
        endkey=endkey,
        descending=descending)

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

        o_image_org = PIL.Image.open(io.BytesIO(dec_data))
        im_w, im_h = o_image_org.size

        if o_image_org.mode == "RGB":
            o_image = o_image_org
        else:
            o_image = PIL.Image.new("RGB", o_image_org.size, (255, 255, 255))
            o_image.paste(o_image_org, mask=o_image_org.split()[3])

        if (im_w > IMAGE_MAX_W) or (im_h > IMAGE_MAX_H):
            o_image.thumbnail((IMAGE_MAX_W, IMAGE_MAX_H))

        f = io.BytesIO()
        o_image.save(f, "JPEG")
        raw_data = f.getvalue()

        return mime, raw_data

    return None, None


# [EOF]
