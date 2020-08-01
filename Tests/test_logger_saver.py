import unittest

from Utils.LoggerSaver import *

class TestLogger(unittest.TestCase):

    def test_whatsapp_logger(self):
        msg = LoggerSaver.save_log("Test log", WhatsappLogger())
        self.assertIsNotNone(msg, "Returning message from Twillio is None")
        self.assertEqual("AC195839e17375092b49275039b92105b5", msg.account_sid, "SID is not equal")

if __name__ == '__main__':
    unittest.main()