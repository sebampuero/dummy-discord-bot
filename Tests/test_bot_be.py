import unittest
import pymysql

from BE.BotBE import BotBE

class TestBotBE(unittest.TestCase):

    def setUp(self):
        #connects to the docker mysql container
        self.db = pymysql.connect(host="localhost", user="root", password="test", database="discordb", port=3307)
        self.cursor = self.db.cursor()

    def test_subscribe_member(self):
        pass

    def test_unsubscribe_member(self):
        pass