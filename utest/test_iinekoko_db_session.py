import sys
import unittest
import configparser

sys.path.append("./svc")

TEST_DOC_ID = "1"
TEST_DOC_TW_ID = "1"
TEST_DOC_TW_USERNAME = "test_username"


class CIIneKoKo_DBSession(unittest.TestCase):
    def setUp(self):
        import iinekoko_db
        self.o_conf = configparser.ConfigParser()
        self.o_conf.read("./svc/config.ini")
        self.o_db = iinekoko_db.CDatabase(self.o_conf)

    def test_create(self):
        import iinekoko_db_session

        o_model = iinekoko_db_session.CModelSession(
            _id=TEST_DOC_ID,
            tw_id=TEST_DOC_TW_ID,
            tw_username=TEST_DOC_TW_USERNAME)
        o_sess_c = iinekoko_db_session.create(self.o_db, o_model)
        o_sess_g = iinekoko_db_session.get(self.o_db, o_sess_c["_id"])

        o_sess_c.fetch()
        o_sess_g.delete()

    def test_get(self):
        import iinekoko_db_session

        o_sess = iinekoko_db_session.get(self.o_db, TEST_DOC_ID)

        self.assertEqual(o_sess, None)


# [EOF]
