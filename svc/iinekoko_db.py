"""
"""
import hashlib
import uuid
import re
import datetime
import configparser
import base64
import io

import PIL.Image
import cloudant
import pytz
from pydantic import BaseModel

# ------------------------------------------------------------------- param(s)
THUMBNAIL_LENGTH = 512
ATTACHMENT_NAME = "image"


# ------------------------------------------------------------- CouchDB:doc(s)
class CDocSession(object):
    __slots__ = ["document_id", "tw_id", "tw_username", "created_at"]

    def __init__(self, tw_id: str, tw_username: str, created_at: str = None):
        self.document_id = None
        self.tw_id = tw_id
        self.tw_username = tw_username
        self.created_at = created_at

    def get_document_id(self):
        return self.document_id

    def set_document_id(self, _id: str):
        self.document_id = _id

    def set_created_at(self, created_at: str = None):
        if created_at is not None:
            self.created_at = created_at
        else:
            self.created_at = datetime.datetime.now(
                pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_dict(self):
        assert self.document_id is not None
        assert self.created_at is not None

        return {
            "_id": self.document_id,
            "tw_id": self.tw_id,
            "tw_username": self.tw_username,
            "created_at": self.created_at
        }


class CDocImageRef:
    def __init__(self,
                 tw_id: str,
                 tw_username: str,
                 title: str,
                 list_col_desc=[],
                 created_at: str = None):
        self.tw_id = tw_id
        self.tw_username = tw_username
        self.title = title
        self.list_col_desc = list_col_desc
        self.created_at = created_at
        self.hex_hash = None
        self.attachemnt_mime = None
        self.attachment_data = None

    def get_document_id(self):
        return hashlib.sha1(":".join(
            (self.hex_hash, self.tw_id)).encode("utf-8")).hexdigest()

    def set_hex_hash(self, hex_hash: str):
        self.hex_hash = hex_hash

    def set_created_at(self, created_at: str = None):
        if created_at is not None:
            self.created_at = created_at
        else:
            self.created_at = datetime.datetime.now(
                pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_dict(self):
        assert self.hex_hash is not None
        assert self.created_at is not None

        return {
            "_id": self.get_document_id(),
            "doc_type": "image_ref",
            "tw_id": self.tw_id,
            "tw_username": self.tw_username,
            "title": self.title,
            "list_col_desc": self.list_col_desc,
            "hex_hash": self.hex_hash,
            "created_at": self.created_at,
        }


class CDocImageMrk:
    __slots__ = [
        "id_image_ref", "tw_id", "tw_username", "list_mark", "modified_at",
        "created_at"
    ]

    def __init__(self,
                 id_image_ref: str,
                 tw_id: str,
                 tw_username: str,
                 list_mark=[],
                 modified_at: str = None,
                 created_at: str = None):
        self.id_image_ref = id_image_ref
        self.tw_id = tw_id
        self.tw_username = tw_username
        self.list_mark = list_mark
        self.modified_at = modified_at
        self.created_at = created_at

    def get_document_id(self):
        assert self.id_image_ref is not None

        return ":".join((self.id_image_ref, self.tw_id))

    def set_modified_at(self, modified_at: str = None):
        if modified_at is not None:
            self.modified_at = modified_at
        else:
            self.modified_at = datetime.datetime.now(
                pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")

    def set_created_at(self, created_at: str = None):
        if created_at is not None:
            self.created_at = created_at
        else:
            self.created_at = datetime.datetime.now(
                pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_dict(self):
        assert self.id_image_ref is not None
        assert self.modified_at is not None
        assert self.created_at is not None

        return {
            "_id": self.get_document_id(),
            "id_image_ref": self.id_image_ref,
            "tw_id": self.tw_id,
            "tw_username": self.tw_username,
            "list_mark": self.list_mark,
            "modified_at": self.modified_at,
            "created_at": self.created_at
        }


#
class CReqPost_NewImageRef(BaseModel):
    title: str
    desc_r: str
    desc_g: str
    desc_b: str
    check_size: str
    image_ref: dict


class CReqPost_GetImageRef(BaseModel):
    document_id: str


class CReqPost_AppendImageMrk(BaseModel):
    id_image_ref: str
    list_mark: list


class CReqPost_RemoveImageMrk(BaseModel):
    id_image_ref: str


class CReqPost_GetImageMrk(BaseModel):
    id_image_ref: str


class CReqPost_GetImageMrkList(BaseModel):
    id_image_ref: str


class CDatabase(object):
    def __init__(self, config_filename="./svc/config.ini"):
        o_config = configparser.ConfigParser()
        o_config.read(config_filename)

        self.o_conn = cloudant.Cloudant(o_config.get("DATABASE", "USERNAME"),
                                        o_config.get("DATABASE", "PASSWORD"),
                                        url=o_config.get("DATABASE", "HOST"),
                                        connect=True)

        self.db_session = self.o_conn.create_database("iinekoko_session")

        self.db_imref = self.o_conn.create_database("iinekoko_imref")
        self.db_immrk = self.o_conn.create_database("iinekoko_immrk")

    #
    def new_session(self, tw_id: str, tw_username: str):
        o_uuid = uuid.uuid4()
        o_doc = CDocSession(tw_id, tw_username)
        o_doc.set_document_id(o_uuid.hex)
        o_doc.set_created_at()

        doc = self.db_session.create_document(o_doc.to_dict())
        if doc.exists() is False:
            o_doc = None

        return o_doc

    def del_session(self, document_id: str):
        try:
            doc = self.db_session[document_id]
            doc.fetch()
            doc.delete()
            b_result = True
        except KeyError:
            b_result = False

        return b_result

    def get_session(self, document_id: str):
        try:
            doc = self.db_session[document_id]
            if doc.exists() is True:
                doc.fetch()
                o_doc = CDocSession(doc["tw_id"], doc["tw_username"],
                                    doc["created_at"])
                o_doc.set_document_id(doc["_id"])
                o_doc.set_created_at()
                doc["created_at"] = o_doc.created_at
                doc.save()
                return o_doc
        except KeyError:
            pass

        return None

    #
    def new_image_ref(self, tw_id: str, tw_username: str,
                      o_req_post: CReqPost_NewImageRef):

        enc_data = o_req_post.image_ref["src"]

        title = o_req_post.title.strip()
        desc_r = o_req_post.desc_r.strip()
        desc_g = o_req_post.desc_g.strip()
        desc_b = o_req_post.desc_b.strip()

        list_col_desc = []
        if len(o_req_post.desc_r) > 0:
            list_col_desc.append({"name": "R", "value": desc_r})
        if len(o_req_post.desc_g) > 0:
            list_col_desc.append({"name": "G", "value": desc_g})
        if len(o_req_post.desc_b) > 0:
            list_col_desc.append({"name": "B", "value": desc_b})

        mime, raw_data = dict_image_b64dec(enc_data)
        hex_hash = hashlib.sha1(raw_data).hexdigest()

        o_doc = CDocImageRef(tw_id, tw_username, title, list_col_desc)
        o_doc.set_hex_hash(hex_hash)
        o_doc.set_created_at()

        doc = self.db_imref.create_document(o_doc.to_dict())
        if doc.exists() is False:
            o_doc = None
        else:
            doc.put_attachment(ATTACHMENT_NAME, mime, raw_data)
            o_doc.attachemnt_mime = mime
            o_doc.attachment_data = raw_data

        return o_doc

    def del_image_ref(self, document_id: str):
        try:
            doc = self.db_imref[document_id]
            doc.fetch()
            doc.delete()
            b_result = True
        except KeyError:
            b_result = False

        return b_result

    def get_image_ref(self, document_id: str):
        try:
            doc = self.db_imref[document_id]
            if doc.exists() is True:
                doc.fetch()
                o_doc = CDocImageRef(doc["tw_id"], doc["tw_username"],
                                     doc["title"], doc["list_col_desc"],
                                     doc["created_at"])
                o_doc.set_hex_hash(doc["hex_hash"])
                o_doc.attachemnt_mime = doc["_attachments"][ATTACHMENT_NAME][
                    "content_type"]
                o_doc.attachment_data = doc.get_attachment(ATTACHMENT_NAME)
                return o_doc
        except KeyError:
            pass

        return None

    def get_image_ref_list(self, tw_id: str):
        list_result = self.db_imref.get_view_result(
            "image_ref",
            "list",
        )
        return [r for r in list_result[[tw_id, ""]:[tw_id, "Z"]]]

    def append_image_mrk(self, tw_id: str, tw_username: str,
                         o_req_post: CReqPost_AppendImageMrk):

        o_doc = CDocImageMrk(o_req_post.id_image_ref, tw_id, tw_username,
                             o_req_post.list_mark)
        o_doc.set_modified_at()
        o_doc.set_created_at()
        doc = self.db_immrk.create_document(o_doc.to_dict())
        if doc.exists() is False:
            o_doc = None

        return o_doc

    def remove_image_mrk(self, tw_id: str, tw_username: str,
                         o_req_post: CReqPost_RemoveImageMrk):

        o_doc = CDocImageMrk(o_req_post.id_image_ref, tw_id, tw_username)

        try:
            doc = self.db_immrk[o_doc.get_document_id()]
            doc.fetch()
            doc.delete()
            b_result = True
        except KeyError:
            b_result = False

        return b_result

    def get_image_mrk(self, tw_id: str, tw_username: str,
                      o_req_post: CReqPost_GetImageMrk):

        o_doc = CDocImageMrk(o_req_post.id_image_ref, tw_id, tw_username)

        try:
            doc = self.db_immrk[o_doc.get_document_id()]
            if doc.exists() is True:
                doc.fetch()
                o_doc.set_modified_at(doc["modified_at"])
                o_doc.set_created_at(doc["created_at"])
                o_doc.list_mark = doc["list_mark"]
                return o_doc
        except KeyError:
            pass

        return None

    def get_image_mrk_list(self, tw_id: str, tw_username: str,
                           o_req_post: CReqPost_GetImageMrkList):

        list_result = self.db_immrk.get_view_result(
            "_design/image_mrk",
            "list",
            startkey=[o_req_post.id_image_ref, ""],
            endkey=[o_req_post.id_image_ref, "Z"],
            limit=100)

        return [
            r for r in list_result.all()
            if r["id"] != ":".join((o_req_post.id_image_ref, tw_id))
        ]


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

        if (im_w > THUMBNAIL_LENGTH) or (im_h > THUMBNAIL_LENGTH):
            o_image.thumbnail((THUMBNAIL_LENGTH, THUMBNAIL_LENGTH))

        f = io.BytesIO()
        o_image.save(f, "JPEG")
        raw_data = f.getvalue()

        return mime, raw_data

    return None, None


# [EOF]
