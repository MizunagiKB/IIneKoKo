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
COOKIE_EXPIRE_SEC = 7 * 24 * 60 * 60
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
app.mount("/doc", StaticFiles(directory="./doc"), name="doc")
app.mount("/ref", StaticFiles(directory="./ref"), name="ref")

o_tpl = Jinja2Templates(directory="./tpl")


def session_load(session_key: str):

    o_db = iinekoko_db.CDatabase(o_conf)

    o_doc_sess = iinekoko_db_session.get(o_db, session_key)
    if o_doc_sess is None:
        o_sess = iinekoko_db_session.CModelSession(tw_id="",
                                                   tw_username="",
                                                   profile_image_url_https="",
                                                   default_profile_image=False)
        o_doc_sess = iinekoko_db_session.create(o_db, o_sess)

    return o_db, o_doc_sess


def session_save(o_doc_sess, o_res):

    expired_sec = int(
        datetime.datetime.now(pytz.timezone("UTC")).timestamp() /
        100000000) + COOKIE_EXPIRE_SEC

    o_res.set_cookie(key=COOKIE_NAME,
                     value=o_doc_sess["_id"],
                     expires=expired_sec)


def is_signin(o_doc_sess):
    try:
        n_result = len(o_doc_sess["tw_id"])
    except KeyError:
        n_result = 0

    if n_result > 0:
        n_result = 1

    return n_result


async def index(o_req: Request, iinekoko_session=Cookie(None)):
    o_db, o_doc_sess = session_load(iinekoko_session)
    if o_doc_sess is None:
        return None

    o_res = o_tpl.TemplateResponse(
        "index.html", {
            "request": o_req,
            "signin_status": is_signin(o_doc_sess),
            "o_doc_sess": o_doc_sess,
            "conf_site": o_conf["SITE"]
        })

    session_save(o_doc_sess, o_res)

    return o_res


async def login(o_req: Request, iinekoko_session=Cookie(None)):
    o_db, o_doc_sess = session_load(iinekoko_session)
    if o_doc_sess is None:
        return None

    if "referer" in o_req.headers:
        o_doc_sess["referer"] = o_req.headers["referer"]
        o_doc_sess.save()

    twitter = o_auth.create_client("twitter")
    redirect_uri = o_conf.get("SITE", "toppage_url") + "auth"

    return await twitter.authorize_redirect(o_req, redirect_uri)


async def login_auth(o_req: Request, iinekoko_session=Cookie(None)):
    o_db, o_doc_sess = session_load(iinekoko_session)
    if o_doc_sess is None:
        return None

    twitter = o_auth.create_client("twitter")

    if "referer" in o_doc_sess:
        referer = o_doc_sess["referer"]
    else:
        referer = o_conf.get("SITE", "toppage_url")

    o_doc_sess["referer"] = ""
    o_doc_sess.save()

    o_res = RedirectResponse(referer)

    try:
        token = await twitter.authorize_access_token(o_req)
    except authlib.integrations.base_client.errors.OAuthError:
        return o_res

    res = await twitter.get("account/verify_credentials.json",
                            params={"skip_status": True},
                            token=token)
    dict_user = res.json()
    # o_log.info(dict_user)

    o_doc_sess["tw_id"] = dict_user["id_str"]
    o_doc_sess["tw_username"] = dict_user["screen_name"]
    o_doc_sess["default_profile_image"] = dict_user["default_profile_image"]
    if dict_user["default_profile_image"] is True:
        o_doc_sess["profile_image_url_https"] = ""
    else:
        o_doc_sess["profile_image_url_https"] = dict_user[
            "profile_image_url_https"]
    o_doc_sess.save()

    session_save(o_doc_sess, o_res)

    return o_res


async def logout(o_req: Request, iinekoko_session=Cookie(None)):
    o_db, o_doc_sess = session_load(iinekoko_session)
    if o_doc_sess is None:
        return None

    if "referer" in o_req.headers:
        referer = o_req.headers["referer"]
    else:
        referer = o_conf.get("SITE", "toppage_url")

    o_doc_sess.delete()

    o_res = RedirectResponse(referer)
    o_res.delete_cookie(COOKIE_NAME)

    return o_res


async def image_ref_new(o_model: iinekoko_db_imref.CModelIMRef,
                        iinekoko_session=Cookie(None)):
    o_db, o_doc_sess = session_load(iinekoko_session)
    if o_doc_sess is None:
        return None
    if is_signin(o_doc_sess) != 1:
        res = JSONResponse()
        res.status_code = 401
        return res

    list_doc_imref = iinekoko_db_imref.get_list(o_db, o_doc_sess,
                                                [o_doc_sess["tw_id"], "Z"],
                                                [o_doc_sess["tw_id"], ""],
                                                True)
    if len(list_doc_imref) < MAX_IMREF:
        o_doc_imref = iinekoko_db_imref.create(
            o_db, o_doc_sess, o_model, o_conf.get("SITE", "image_store"))
    else:
        o_doc_imref = None

    return {"doc": o_doc_imref}


async def image_ref_del(document_id: str, iinekoko_session=Cookie(None)):
    o_db, o_doc_sess = session_load(iinekoko_session)
    if o_doc_sess is None:
        return None
    if is_signin(o_doc_sess) != 1:
        res = JSONResponse()
        res.status_code = 401
        return res

    iinekoko_db_imref.delete(o_db, o_doc_sess, document_id,
                             o_conf.get("SITE", "image_store"))

    return {"doc": None}


async def image_ref_get(document_id: str, iinekoko_session=Cookie(None)):
    o_db, o_doc_sess = session_load(iinekoko_session)
    if o_doc_sess is None:
        return None

    o_doc_imref = iinekoko_db_imref.get(o_db, document_id)
    if o_doc_imref is not None:
        return {"doc": o_doc_imref}

    return {"doc": None}


async def image_ref_get_list(o_req: Request, iinekoko_session=Cookie(None)):
    o_db, o_doc_sess = session_load(iinekoko_session)
    if o_doc_sess is None:
        return None
    if is_signin(o_doc_sess) != 1:
        res = JSONResponse()
        res.status_code = 401
        return res

    list_result = iinekoko_db_imref.get_list(o_db, o_doc_sess,
                                             [o_doc_sess["tw_id"], "Z"],
                                             [o_doc_sess["tw_id"], ""], True)

    return list_result


async def image_mrk_new(o_model: iinekoko_db_immrk.CModelIMMrk,
                        iinekoko_session=Cookie(None)):
    o_db, o_doc_sess = session_load(iinekoko_session)
    if o_doc_sess is None:
        return None
    if is_signin(o_doc_sess) != 1:
        res = JSONResponse()
        res.status_code = 401
        return res

    if iinekoko_db_imref.get(o_db, o_model.id_imref) is None:
        res = JSONResponse()
        res.status_code = 400
        return res

    list_doc_immrk = iinekoko_db_immrk.get_list(o_db, o_model.id_imref)

    if len(list_doc_immrk) < MAX_IMMRK:
        o_doc_immrk = iinekoko_db_immrk.get(o_db, o_doc_sess, o_model.id_imref)
        if o_doc_immrk is not None:
            # o_doc_immrk["x"] = o_model.x
            # o_doc_immrk["y"] = o_model.y
            # o_doc_immrk.save()
            pass
        else:
            iinekoko_db_immrk.create(o_db, o_doc_sess, o_model)

    return None


async def image_mrk_del(id_imref: str, iinekoko_session=Cookie(None)):
    o_db, o_doc_sess = session_load(iinekoko_session)
    if o_doc_sess is None:
        return None
    if is_signin(o_doc_sess) != 1:
        res = JSONResponse()
        res.status_code = 401
        return res

    o_doc_immrk = iinekoko_db_immrk.get(o_db, o_doc_sess, id_imref)

    if o_doc_immrk is not None:
        o_doc_immrk.delete()

    return None


async def image_mrk_get(id_imref: str, iinekoko_session=Cookie(None)):
    o_db, o_doc_sess = session_load(iinekoko_session)
    if o_doc_sess is None:
        return None
    if is_signin(o_doc_sess) != 1:
        res = JSONResponse()
        res.status_code = 401
        return res

    o_doc_immrk = iinekoko_db_immrk.get(o_db, o_doc_sess, id_imref)
    return {"doc": o_doc_immrk}


async def image_mrk_get_list(id_imref: str, iinekoko_session=Cookie(None)):
    o_db, o_doc_sess = session_load(iinekoko_session)

    list_result = iinekoko_db_immrk.get_list(o_db, id_imref, include_docs=True)
    if len(list_result) == MAX_IMMRK:
        return list_result
    else:
        if o_doc_sess is None:
            return None
        if is_signin(o_doc_sess) != 1:
            res = JSONResponse()
            res.status_code = 401
            return res

        o_doc_imref = iinekoko_db_imref.get(o_db, id_imref)
        if o_doc_imref is not None:
            if o_doc_imref["tw_id"] == o_doc_sess["tw_id"]:
                return list_result

        o_doc_immrk = iinekoko_db_immrk.get(o_db, o_doc_sess, id_imref)
        if o_doc_immrk is not None:
            return list_result

    return []


#
app.add_api_route("/", index)
app.add_api_route("/index", index)
app.add_api_route("/signin", login)
app.add_api_route("/auth", login_auth)
app.add_api_route("/signout", logout)

app.add_api_route("/api/image_ref_new", image_ref_new, methods=["POST"])
app.add_api_route("/api/image_ref_del/{document_id}",
                  image_ref_del,
                  methods=["POST"])
app.add_api_route("/api/image_ref_get/{document_id}",
                  image_ref_get,
                  methods=["POST"])
app.add_api_route("/api/image_ref_get_list",
                  image_ref_get_list,
                  methods=["POST"])

app.add_api_route("/api/image_mrk_new", image_mrk_new, methods=["POST"])
app.add_api_route("/api/image_mrk_del/{id_imref}",
                  image_mrk_del,
                  methods=["POST"])
app.add_api_route("/api/image_mrk_get/{id_imref}",
                  image_mrk_get,
                  methods=["POST"])
app.add_api_route("/api/image_mrk_get_list/{id_imref}",
                  image_mrk_get_list,
                  methods=["POST"])

# [EOF]
