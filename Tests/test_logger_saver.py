import unittest
import json

from Utils.LoggerSaver import *

class TestLogger(unittest.TestCase):

    def test_whatsapp_logger(self):
        msg = LoggerSaver.save_log("Test log", WhatsappLogger())
        self.assertIsNotNone(msg, "Returning message from Twillio is None")
        with open("config/creds.json") as f:
            account_id = json.loads(f.read())["twillio"]["account_sid"]
        self.assertEqual(account_id, msg.account_sid, "SID is not equal")

if __name__ == '__main__':
    unittest.main()