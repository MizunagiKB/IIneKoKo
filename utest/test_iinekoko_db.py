import sys
import unittest

sys.path.append("./svc")


class CIIneKoKo_DB(unittest.TestCase):
    def setUp(self):
        import iinekoko_db
        self.o_conn = iinekoko_db.CDatabase()

    def test_image_encdec(self):
        import iinekoko_db

        with open("utest/image/test.jpg", "rb") as f:
            raw_data = f.read()

            enc_data1 = iinekoko_db.dict_image_b64enc("image/jpeg", raw_data)
            mime, dec_data = iinekoko_db.dict_image_b64dec(enc_data1)
            iinekoko_db.dict_image_b64enc(mime, dec_data)

            self.assertTrue(True)

    def test_doc_session(self):
        o_doc1 = self.o_conn.new_session("1", "username_1")
        self.assertEqual(o_doc1.tw_id, "1")
        self.assertEqual(o_doc1.tw_username, "username_1")

        o_doc2 = self.o_conn.get_session(o_doc1.document_id)
        self.assertEqual(o_doc1.document_id, o_doc2.document_id)

        self.o_conn.del_session(o_doc1.document_id)
        o_doc = self.o_conn.get_session(o_doc1.document_id)
        self.assertEqual(o_doc, None)

        o_doc = self.o_conn.get_session("X")
        self.assertEqual(o_doc, None)

        self.assertFalse(self.o_conn.del_session("X"))

    def test_doc_image_ref(self):
        import iinekoko_db

        with open("utest/image/test.jpg", "rb") as f:
            raw_data = f.read()

            enc_data = iinekoko_db.dict_image_b64enc("image/jpeg", raw_data)

            TW_ID = "1"
            TW_USERNAME = "username_1"

            o_doc = self.o_conn.new_image_ref(enc_data, TW_ID, TW_USERNAME, [])
            self.assertEqual(o_doc.tw_id, TW_ID)

            o_doc1 = self.o_conn.get_image_ref(o_doc.get_document_id())
            self.assertEqual(o_doc.get_document_id(), o_doc1.get_document_id())

            self.o_conn.del_image_ref(o_doc.get_document_id())
            o_doc = self.o_conn.get_image_ref(o_doc.get_document_id())
            self.assertEqual(o_doc, None)

    def test_doc_image_mrk(self):
        import iinekoko_db

        ID_IMAGE_REF = "1"
        TW_ID = "1"
        TW_USERNAME = "username_1"

        o_doc = self.o_conn.append_image_mrk(ID_IMAGE_REF, TW_ID, TW_USERNAME,
                                             [])

        self.o_conn.remove_image_mrk(o_doc.get_document_id())

    def test_doc_image_ref_list(self):
        import iinekoko_db

        TW_ID = "431236837"
        self.o_conn.get_image_ref_list(TW_ID)


# [EOF]
