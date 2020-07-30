import unittest
import aiounittest

from Utils.NetworkUtils import NetworkUtils

class TestNetworkUtils(aiounittest.AsyncTestCase):

    def setUp(self):
        self.network_utils = NetworkUtils()
        self.webpage = "https://geohot.com/" # the god

    async def test_website_check(self):
        """
        Test that it can check a website for status code and content type
        """
        status, content_type = await self.network_utils.website_check(self.webpage)
        self.assertIsNotNone(status, "Status code is not none")
        self.assertIsNotNone(content_type, "Content-Type is not None")
        self.assertEqual(content_type, "text/html")

    async def test_get_content_from_page(self):
        """
        Test that it can get the content from a page
        """
        content = await self.network_utils.get_content_from_page(self.webpage)
        self.assertNotEqual(content, "", "Content is not retrieved")
        self.assertIn('<a href="https://comma.ai/">my startup</a>', content, "Content has no anchor tag")


if __name__ == '__main__':
    unittest.main()