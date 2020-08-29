import unittest
from DB.db import MySQLTESTDB
import Constants.StringConstants as Constants

from BE.BotBE import BotBE

class TestSubscriber:

    def __init__(self, id):
        self.id = id

class TestBotBE(unittest.TestCase):

    tables = ['alerts', 'user', 'subscriptions', 'quotes', 'playlist']

    @classmethod
    def setUpClass(cls):
        cls.test_db = MySQLTESTDB()
        cls.bot_be = BotBE(cls.test_db)

    @classmethod
    def tearDownClass(cls):
        conn = cls.test_db.pool.get_conn()
        for table in cls.tables:
            conn.cursor().execute(f"DELETE FROM {table}")
        cls.test_db.pool.release(conn)

    def setUp(self):
        self.conn = TestBotBE.test_db.pool.get_conn()
        self.cursor = self.conn.cursor()

    def tearDown(self):
        TestBotBE.test_db.pool.release(self.conn)

    def _subscribe_member(self):
        subscriber = TestSubscriber(12345)
        result = TestBotBE.bot_be.subscribe_member([TestSubscriber(i) for i in range(0, 5)], subscriber.id)
        return result, subscriber

    def _set_alert(self):
        url = "https://www.amazon.de/Naturix24-Kurkuma-gemahlen-1er-Pack/"
        price_range = "10-20"
        currency = "EUR"
        user_id = 1
        result = TestBotBE.bot_be.set_alert(url, price_range, currency, user_id)
        return result, url

    def test_subscribe_member(self):
        result, subscriber = self._subscribe_member()
        self.assertEqual(Constants.DONE, result, "Not OK")
        self.cursor.execute(f"SELECT * FROM subscriptions WHERE subscriber = '{subscriber.id}'")
        query = self.cursor.fetchall()
        self.assertIsNotNone(query, "Result is None")
        self.assertEqual(5, len(query), "Not all subscriptions were made")

    def test_unsubscribe_member(self):
        result, subscriber = self._subscribe_member()
        self.assertEqual(Constants.DONE, result, "Not OK")
        result = TestBotBE.bot_be.unsubscribe_member([TestSubscriber(i) for i in range(0, 5)], subscriber.id)
        self.assertEqual(Constants.DONE, result, "Not OK")
        self.cursor.execute(f"SELECT * FROM subscriptions WHERE subscriber = '{subscriber.id}'")
        query = self.cursor.fetchall()
        self.assertIsNotNone(query, "Result is None")
        self.assertEqual(0, len(query), "Unsubscriptions were not executed")

    def test_retrieve_subscribers_from_subscribee(self):
        result, subscriber = self._subscribe_member()
        self.assertEqual(Constants.DONE, result, "Not OK")
        self.cursor.execute(f"SELECT subscribee FROM subscriptions WHERE subscriber = '{subscriber.id}'")
        query = self.cursor.fetchall()
        self.assertIsNotNone(query, "Result is None")
        self.assertEqual(5, len(query), "Subscriber has no subscriptions")
        self.assertListEqual([subscribee['subscribee'] for subscribee in query], ['0','1','2','3','4'], "List of subscribers does not coincide")

    def test_set_alert(self):
        result, url = self._set_alert()
        self.assertNotEqual(Constants.COULD_NOT_DO_IT, result, "Not OK")
        self.cursor.execute(f"SELECT url FROM alerts WHERE url = '{url}'")
        query = self.cursor.fetchall()
        self.assertIsNotNone(query, "Result is None")
        self.assertEqual(query[0]['url'], url, "URL is not the one saved")

    def test_unset_alert(self):
        pass

    def test_load_radios_msg(self):
        pass

    def test_load_radios_config(self):
        pass

    def test_load_users_welcome_audios(self):
        pass

    def test_save_audio_for_user(self):
        pass

    def test_save_radios(self):
        pass

    def test_save_users_welcome_audios(self):
        pass

    def test_read_user_playlists(self):
        pass

    def test_save_playlist_for_user(self):
        pass

if __name__ == '__main__':
    unittest.main()