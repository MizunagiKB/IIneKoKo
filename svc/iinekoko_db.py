# ------------------------------------------------------------------ import(s)
import requests
import cloudant


class CDatabase(object):
    def __init__(self, o_conf):
        self.o_conf = o_conf

        try:
            self.o_conn = cloudant.Cloudant(o_conf.get("DATABASE", "USERNAME"),
                                            o_conf.get("DATABASE", "PASSWORD"),
                                            url=o_conf.get("DATABASE", "HOST"),
                                            connect=True)
        except requests.exceptions.ConnectionError:
            self.o_conn = None

        if self.o_conn is not None:
            self.o_conn.create_database("iinekoko_session")
            self.o_conn.create_database("iinekoko_imref")
            self.o_conn.create_database("iinekoko_immrk")
