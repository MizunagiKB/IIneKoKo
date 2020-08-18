import unittest
import sys
import configparser

sys.path.append("./svc")

IMAGE_STORE = "./svc/ref"
TEST_DOC_ID = "1"
TEST_DOC_TW_ID = "1"
TEST_DOC_TW_USERNAME = "test_username"


class CIIneKoKo_DBIMRef(unittest.TestCase):
    def setUp(self):
        import iinekoko_db
        import iinekoko_db_session

        self.o_conf = configparser.ConfigParser()
        self.o_conf.read("./svc/config.ini")
        self.o_db = iinekoko_db.CDatabase(self.o_conf)

        o_model = iinekoko_db_session.CModelSession(
            _id=TEST_DOC_ID,
            tw_id=TEST_DOC_TW_ID,
            tw_username=TEST_DOC_TW_USERNAME)
        self.o_doc_sess = iinekoko_db_session.create(self.o_db, o_model)
        self.o_doc_sess.fetch()

    def test_create(self):
        import iinekoko_db_imref

        with open("utest/image/test.jpg", "rb") as f:
            raw_data = f.read()
            enc_data = iinekoko_db_imref.dict_image_b64enc(
                "image/jpeg", raw_data)

            o_model = iinekoko_db_imref.CModelIMRef(title="TEST_TITLE",
                                                    desc_r="desc_r_text",
                                                    desc_g="desc_g_text",
                                                    desc_b="desc_b_text")
            """
            o = o_model.dict(
                exclude={"image_ref"},
                by_alias=True,
                exclude_none=True,
            )
            print(o)
            return
            """

            o_doc_imref_c = iinekoko_db_imref.create(self.o_db,
                                                     self.o_doc_sess, o_model,
                                                     enc_data, IMAGE_STORE)

            o_doc_imref_g = iinekoko_db_imref.get(self.o_db,
                                                  o_doc_imref_c["_id"])

            self.assertEqual(o_doc_imref_c["_id"], o_doc_imref_g["_id"])

            o_doc_imref_c.fetch()
            o_doc_imref_c.delete()

    def test_get(self):
        import iinekoko_db_imref

        o_doc_imref = iinekoko_db_imref.get(self.o_db, TEST_DOC_ID)

        self.assertEqual(o_doc_imref, None)

    def test_get_list(self):
        import iinekoko_db_imref

        o_doc_imref = iinekoko_db_imref.get_list(self.o_db, self.o_doc_sess)

        self.assertEqual(o_doc_imref, [])


# [EOF]
