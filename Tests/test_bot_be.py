import unittest
from DB.db import MySQLTESTDB
import Constants.StringConstants as Constants

from BE.BotBE import BotBE

class TestSubscriber:

    def __init__(self, id):
        self.id = id

class TestBotBE(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_db = MySQLTESTDB()
        cls.bot_be = BotBE(cls.test_db)

    def tearDown(self):
        print("Rollback transaction")
        TestBotBE.test_db.rollback_transaction()

    def _subscribe_member(self):
        subscriber = TestSubscriber(12345)
        result = TestBotBE.bot_be.subscribe_member([TestSubscriber(i) for i in range(0, 5)], subscriber.id)
        return result, subscriber

    def test_subscribe_member(self):
        db = TestBotBE.test_db
        result, subscriber = self._subscribe_member()
        self.assertEqual(Constants.DONE, result, "Not OK")
        db.cursor.execute(f"SELECT * FROM subscriptions WHERE subscriber = '{subscriber.id}'")
        query = db.cursor.fetchall()
        self.assertIsNotNone(query, "Result is None")
        self.assertEqual(5, len(query), "Not all subscriptions were made")

    def test_unsubscribe_member(self):
        db = TestBotBE.test_db
        result, subscriber = self._subscribe_member()
        self.assertEqual(Constants.DONE, result, "Not OK")
        result = TestBotBE.bot_be.unsubscribe_member([TestSubscriber(i) for i in range(0, 5)], subscriber.id)
        self.assertEqual(Constants.DONE, result, "Not OK")
        db.cursor.execute(f"SELECT * FROM subscriptions WHERE subscriber = '{subscriber.id}'")
        query = db.cursor.fetchall()
        self.assertIsNotNone(query, "Result is None")
        self.assertEqual(0, len(query), "Unsubscriptions were not executed")

    def test_retrieve_subscribers_from_subscribee(self):
        pass

    def test_set_alert(self):
        pass

if __name__ == '__main__':
    unittest.main()