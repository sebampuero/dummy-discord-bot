from Utils.LoggerSaver import *
import requests
import aiohttp
import asyncio
import logging
import discord
"""
NetworkUtils is responsible for managing and processing all network related requests
"""

class NetworkUtils(): #TODO: convert this to static class

    def __init__(self):
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'upgrade-insecure-requests': '1',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'de-DE,de;q=0.9,es-DE;q=0.8,es;q=0.7,en-US;q=0.6,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
    
    async def website_check(self, url, headers=None):
        headers = dict(self.base_headers, **headers) if headers else self.base_headers
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, allow_redirects=True) as response:
                    return response.status, response.content_type
            except:
                return 0, ""
                
    async def get_content_from_page(self, url, headers=None):
        headers = dict(self.base_headers, **headers) if headers else self.base_headers
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    try:
                        content = await response.text()
                        return content
                    except Exception as e:
                        log = f"While fetching page content from {url} {str(e)}"
                        logging.error(log, exc_info=True)
                        LoggerSaver.save_log(log, WhatsappLogger())
                        return ""
                else:
                    return ""