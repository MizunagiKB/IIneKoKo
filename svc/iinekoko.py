import base64
import hashlib
import datetime
from fastapi import FastAPI, Request, Cookie, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse

# from starlette.applications import Starlette
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware

from authlib.integrations.starlette_client import OAuth

import pytz
#
import iinekoko_db

# ------------------------------------------------------------------- param(s)
CONFIG_PATH = "./config.ini"
COOKIE_NAME = "iinekoko_session"

conf = Config('.env')
o_auth = OAuth(conf)
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

o_tpl = Jinja2Templates(directory="./tpl")


@app.get("/")
async def read_root(o_req: Request):
    if COOKIE_NAME in o_req.cookies:
        o_conn = iinekoko_db.CDatabase(CONFIG_PATH)
        o_doc = o_conn.get_session(o_req.cookies[COOKIE_NAME])
        if o_doc is not None:
            login_status = True
    else:
        login_status = False

    return o_tpl.TemplateResponse("index.jinja2", {
        "request": o_req,
        "login_status": login_status
    })


@app.route("/login")
async def login(request: Request):
    twitter = o_auth.create_client("twitter")
    redirect_uri = "http://127.0.0.1:8000/auth"

    return await twitter.authorize_redirect(request, redirect_uri)


@app.route("/auth")
async def auth(request: Request):
    twitter = o_auth.create_client("twitter")

    token = await twitter.authorize_access_token(request)
    url = "account/verify_credentials.json"
    res = await twitter.get(url, params={"skip_status": True}, token=token)
    dict_user = res.json()

    o_conn = iinekoko_db.CDatabase(CONFIG_PATH)
    o_doc = o_conn.new_session(dict_user["id_str"], dict_user["screen_name"])

    expired_sec = int(datetime.datetime.now(
        pytz.timezone("UTC")).timestamp()) + 60

    response = RedirectResponse("http://127.0.0.1:8000/")
    response.set_cookie(key="iinekoko_session",
                        value=o_doc.get_document_id(),
                        expires=expired_sec)

    return response


@app.get("/logout")
async def set_create(o_req: Request, iinekoko_session=Cookie(None)):
    if iinekoko_session is not None:
        o_conn = iinekoko_db.CDatabase(CONFIG_PATH)
        o_conn.del_session(iinekoko_session)

    response = RedirectResponse("http://127.0.0.1:8000/")
    response.delete_cookie(COOKIE_NAME)
    return response


@app.post("/api/new_image_ref")
async def new_image_ref(o_req_post: iinekoko_db.CReqPost_NewImageRef,
                        iinekoko_session=Cookie(None)):

    if iinekoko_session is not None:
        o_conn = iinekoko_db.CDatabase(CONFIG_PATH)
        o_doc = o_conn.get_session(iinekoko_session)
        if o_doc is not None:
            o_conn.new_image_ref(o_doc.tw_id, o_doc.tw_username, o_req_post)

    return None


@app.get("/api/get_image_ref_list")
async def get_image_ref_list(o_req: Request, iinekoko_session=Cookie(None)):

    list_result = []

    if iinekoko_session is not None:
        o_conn = iinekoko_db.CDatabase(CONFIG_PATH)
        o_doc = o_conn.get_session(iinekoko_session)
        if o_doc is not None:
            list_result = o_conn.get_image_ref_list(o_doc.tw_id)

    return list_result


@app.post("/api/get_image_ref")
async def get_image_ref(o_req_post: iinekoko_db.CReqPost_GetImageRef,
                        iinekoko_session=Cookie(None)):

    if iinekoko_session is not None:
        o_conn = iinekoko_db.CDatabase(CONFIG_PATH)
        o_doc = o_conn.get_session(iinekoko_session)
        if o_doc is not None:
            o_doc_image_ref = o_conn.get_image_ref(o_req_post.document_id)
            if o_doc_image_ref is not None:
                enc_data = iinekoko_db.dict_image_b64enc(
                    o_doc_image_ref.attachemnt_mime,
                    o_doc_image_ref.attachment_data)

                return {"doc": o_doc_image_ref.to_dict(), "ref": enc_data}

    return {}


@app.post("/api/append_image_mrk")
async def append_image_mrk(o_req_post: iinekoko_db.CReqPost_AppendImageMrk,
                           iinekoko_session=Cookie(None)):

    if iinekoko_session is not None:
        o_conn = iinekoko_db.CDatabase(CONFIG_PATH)
        o_doc = o_conn.get_session(iinekoko_session)
        if o_doc is not None:
            o_conn.append_image_mrk(o_doc.tw_id, o_doc.tw_username, o_req_post)

    return None


@app.post("/api/remove_image_mrk")
async def remove_image_mrk(o_req_post: iinekoko_db.CReqPost_RemoveImageMrk,
                           iinekoko_session=Cookie(None)):

    if iinekoko_session is not None:
        o_conn = iinekoko_db.CDatabase(CONFIG_PATH)
        o_doc = o_conn.get_session(iinekoko_session)
        if o_doc is not None:
            o_conn.remove_image_mrk(o_doc.tw_id, o_doc.tw_username, o_req_post)

    return None


@app.post("/api/get_image_mrk")
async def get_image_mrk(o_req_post: iinekoko_db.CReqPost_GetImageMrk,
                        iinekoko_session=Cookie(None)):

    if iinekoko_session is not None:
        o_conn = iinekoko_db.CDatabase(CONFIG_PATH)
        o_doc = o_conn.get_session(iinekoko_session)
        if o_doc is not None:
            o_doc_image_ref = o_conn.get_image_mrk(o_doc.tw_id,
                                                   o_doc.tw_username,
                                                   o_req_post)
            if o_doc_image_ref is not None:
                return {"doc": o_doc_image_ref.to_dict()}

    return {}


@app.post("/api/get_image_mrk_list")
async def get_image_mrk_list(o_req_post: iinekoko_db.CReqPost_GetImageMrkList,
                             iinekoko_session=Cookie(None)):

    list_result = []

    if iinekoko_session is not None:
        o_conn = iinekoko_db.CDatabase(CONFIG_PATH)
        o_doc = o_conn.get_session(iinekoko_session)
        if o_doc is not None:
            list_result = o_conn.get_image_mrk_list(o_doc.tw_id,
                                                    o_doc.tw_username,
                                                    o_req_post)

    return list_result


# [EOF]
