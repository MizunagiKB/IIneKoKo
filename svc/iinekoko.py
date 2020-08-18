import datetime
import configparser
import logging

from fastapi import FastAPI, Request, Cookie
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware

import authlib
from authlib.integrations.starlette_client import OAuth

import pytz

import iinekoko_db
import iinekoko_db_imref
import iinekoko_db_immrk
import iinekoko_db_session

# ------------------------------------------------------------------- param(s)
CONFIG_PATH = "./config.ini"
COOKIE_NAME = "iinekoko_session"
TOPPAGE_URL = "http://127.0.0.1:8000/"
MAX_IMREF = 10
MAX_IMMRK = 100

o_conf = configparser.ConfigParser()
o_conf.read(CONFIG_PATH)
o_log = logging.getLogger("iinekoko")
o_log.setLevel(level=logging.INFO)

o_auth = OAuth(Config(".env"))
o_auth.register(
    name='twitter',
    api_base_url='https://api.twitter.com/1.1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="some-random-string")
app.mount("/js", StaticFiles(directory="./js"), name="js")
app.mount("/ref", StaticFiles(directory="./ref"), name="ref")

o_tpl = Jinja2Templates(directory="./tpl")


async def index(o_req: Request, iinekoko_session=Cookie(None)):

    login_status = False

    if iinekoko_session is not None:
        o_db = iinekoko_db.CDatabase(o_conf)
        o_doc_sess = iinekoko_db_session.get(o_db, iinekoko_session)
        if o_doc_sess is not None:
            o_doc_sess.fetch()
            login_status = True

    return o_tpl.TemplateResponse("index.jinja2", {
        "request": o_req,
        "login_status": login_status
    })


async def login(o_req: Request):
    twitter = o_auth.create_client("twitter")
    redirect_uri = TOPPAGE_URL + "auth"

    return await twitter.authorize_redirect(o_req, redirect_uri)


async def login_auth(o_req: Request):
    twitter = o_auth.create_client("twitter")

    o_res = RedirectResponse(TOPPAGE_URL)

    try:
        token = await twitter.authorize_access_token(o_req)
    except authlib.integrations.base_client.errors.OAuthError:
        o_res.delete_cookie(COOKIE_NAME)
        return o_res

    url = "account/verify_credentials.json"
    res = await twitter.get(url, params={"skip_status": True}, token=token)
    dict_user = res.json()

    o_db = iinekoko_db.CDatabase(o_conf)
    o_sess = iinekoko_db_session.CModelSession(
        tw_id=dict_user["id_str"], tw_username=dict_user["screen_name"])
    o_doc_sess = iinekoko_db_session.create(o_db, o_sess)
    if o_doc_sess is not None:
        expired_sec = int(
            datetime.datetime.now(pytz.timezone("UTC")).timestamp()) + 60

        o_res.set_cookie(key="iinekoko_session",
                         value=o_doc_sess["_id"],
                         expires=expired_sec)

    return o_res


async def logout(o_req: Request, iinekoko_session=Cookie(None)):

    if iinekoko_session is not None:
        o_db = iinekoko_db.CDatabase(o_conf)
        o_doc_sess = iinekoko_db_session.get(o_db, iinekoko_session)
        if o_doc_sess is not None:
            o_doc_sess.fetch()
            o_doc_sess.delete()

    o_res = RedirectResponse(TOPPAGE_URL)
    o_res.delete_cookie(COOKIE_NAME)

    return o_res


async def new_image_ref(o_model: iinekoko_db_imref.CModelIMRef,
                        iinekoko_session=Cookie(None)):

    if iinekoko_session is not None:
        o_db = iinekoko_db.CDatabase(o_conf)
        o_doc_sess = iinekoko_db_session.get(o_db, iinekoko_session)
        if o_doc_sess is not None:
            o_doc_sess.fetch()
            list_doc_imref = iinekoko_db_imref.get_list(o_db, o_doc_sess)
            if len(list_doc_imref) < MAX_IMREF:
                o_doc_imref = iinekoko_db_imref.create(
                    o_db, o_doc_sess, o_model,
                    o_conf.get("SITE", "image_store"))
                if o_doc_imref is not None:
                    o_doc_imref.fetch()
                    return {"doc": o_doc_imref}

    return {"doc": None}


async def del_image_ref(document_id: str, iinekoko_session=Cookie(None)):

    if iinekoko_session is not None:
        o_db = iinekoko_db.CDatabase(o_conf)
        o_doc_sess = iinekoko_db_session.get(o_db, iinekoko_session)
        if o_doc_sess is not None:
            o_doc_sess.fetch()
            iinekoko_db_imref.delete(o_db, o_doc_sess, document_id,
                                     o_conf.get("SITE", "image_store"))

    return {"doc": None}


async def get_image_ref(document_id: str, iinekoko_session=Cookie(None)):

    if iinekoko_session is not None:
        o_db = iinekoko_db.CDatabase(o_conf)
        o_doc_sess = iinekoko_db_session.get(o_db, iinekoko_session)
        if o_doc_sess is not None:
            o_doc_sess.fetch()
            o_doc_imref = iinekoko_db_imref.get(o_db, document_id)
            if o_doc_imref is not None:
                return {"doc": o_doc_imref}

    return {"doc": None}


async def get_image_ref_list(o_req: Request, iinekoko_session=Cookie(None)):

    list_result = []

    if iinekoko_session is not None:
        o_db = iinekoko_db.CDatabase(o_conf)
        o_doc_sess = iinekoko_db_session.get(o_db, iinekoko_session)
        if o_doc_sess is not None:
            list_result = iinekoko_db_imref.get_list(
                o_db,
                o_doc_sess,
            )

    return list_result


async def append_image_mrk(o_model: iinekoko_db_immrk.CModelIMMrk,
                           iinekoko_session=Cookie(None)):

    if iinekoko_session is not None:
        o_db = iinekoko_db.CDatabase(o_conf)
        o_doc_sess = iinekoko_db_session.get(o_db, iinekoko_session)
        if o_doc_sess is not None:

            list_immrk = iinekoko_db_immrk.get_list_all(
                o_db, o_doc_sess, o_model.hex_hash)

            if len(list_immrk) < MAX_IMMRK:

                o_doc_immrk = iinekoko_db_immrk.get(o_db, o_doc_sess,
                                                    o_model.hex_hash)
                if o_doc_immrk is not None:
                    o_doc_immrk.fetch()
                    if o_model.mark_r is not None:
                        o_doc_immrk["mark_r"] = o_model.mark_r.dict()
                    if o_model.mark_g is not None:
                        o_doc_immrk["mark_g"] = o_model.mark_g.dict()
                    if o_model.mark_b is not None:
                        o_doc_immrk["mark_b"] = o_model.mark_b.dict()
                    o_doc_immrk["modified_at"] = o_model.modified_at
                    o_doc_immrk.save()
                else:
                    iinekoko_db_immrk.append(o_db, o_doc_sess, o_model)

    return None


async def remove_image_mrk(hex_hash: str,
                           o_model: iinekoko_db_immrk.CModelIMMrk,
                           iinekoko_session=Cookie(None)):

    if iinekoko_session is not None:
        o_db = iinekoko_db.CDatabase(o_conf)
        o_doc_sess = iinekoko_db_session.get(o_db, iinekoko_session)
        if o_doc_sess is not None:
            o_doc_immrk = iinekoko_db_immrk.get(o_db, o_doc_sess, hex_hash)
            if o_doc_immrk is not None:
                o_doc_immrk.fetch()
                o_doc_immrk.delete()

    return None


async def get_image_mrk(hex_hash: str, iinekoko_session=Cookie(None)):

    if iinekoko_session is not None:
        o_db = iinekoko_db.CDatabase(o_conf)
        o_doc_sess = iinekoko_db_session.get(o_db, iinekoko_session)
        if o_doc_sess is not None:
            o_doc_immrk = iinekoko_db_immrk.get(o_db, o_doc_sess, hex_hash)
            if o_doc_immrk is not None:
                return {"doc": o_doc_immrk}

    return {"doc": None}


async def get_image_mrk_list(hex_hash: str, iinekoko_session=Cookie(None)):

    list_result = []

    if iinekoko_session is not None:
        o_db = iinekoko_db.CDatabase(o_conf)
        o_doc_sess = iinekoko_db_session.get(o_db, iinekoko_session)
        if o_doc_sess is not None:
            list_result = iinekoko_db_immrk.get_list(o_db, o_doc_sess,
                                                     hex_hash)

    return list_result


#
app.add_api_route("/", index)
app.add_api_route("/login", login)
app.add_api_route("/auth", login_auth)
app.add_api_route("/logout", logout)

app.add_api_route("/api/new_image_ref", new_image_ref, methods=["POST"])
app.add_api_route("/api/del_image_ref/{document_id}",
                  del_image_ref,
                  methods=["POST"])
app.add_api_route("/api/get_image_ref/{document_id}",
                  get_image_ref,
                  methods=["POST"])
app.add_api_route("/api/get_image_ref_list", get_image_ref_list)

app.add_api_route("/api/append_image_mrk", append_image_mrk, methods=["POST"])
app.add_api_route("/api/remove_image_mrk/{hex_hash}",
                  remove_image_mrk,
                  methods=["POST"])
app.add_api_route("/api/get_image_mrk/{hex_hash}",
                  get_image_mrk,
                  methods=["POST"])
app.add_api_route("/api/get_image_mrk_list/{hex_hash}",
                  get_image_mrk_list,
                  methods=["POST"])

# [EOF]
