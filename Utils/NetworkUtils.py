import requests
import hashlib
import aiohttp
import asyncio
import logging
import discord
import io
import subprocess
import time
import discord
"""
NetworkUtils is responsible for managing and processing all network related requests
"""

class NetworkUtils():
    
    STREAM_BUFFER_SIZE = 80000

    def __init__(self):
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'upgrade-insecure-requests': '1',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'de-DE,de;q=0.9,es-DE;q=0.8,es;q=0.7,en-US;q=0.6,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate'
        }
        
    def setStreamingFlag(self, stream):
        self.stream = stream
    
    async def checkConnectionStatusForSite(self, url, headers=None):
        headers = dict(self.base_headers, **headers) if headers else self.base_headers
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                return response.status
        

    async def getAndSaveTtsLoquendoVoice(self, text, voice="Jorge", language="Spanish (Spain)"):
        url = "http://nuancevocalizerexpressive.sodels.com/"
        headers = {
            'pragma': 'no-cache',
            'cache-control': 'max-age=0',
            'referer': 'http://nuancevocalizerexpressive.sodels.com/',
            'origin': 'http://nuancevocalizerexpressive.sodels.com',
            'content-type': 'application/x-www-form-urlencoded',
            'connection': 'keep-alive',
        }
        
        headers = dict(self.base_headers, **headers)
        form_data = {
            '__EVENTTARGET': "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": "/wEPDwUJNzgxNTk2NjQ3D2QWAgIBD2QWBgIFDxAPFgIeC18hRGF0YUJvdW5kZ2QQFQ4PQmFzcXVlIChCYXNxdWUpEUNhdGFsYW4gKENhdGFsYW4pGEVuZ2xpc2ggKFVuaXRlZCBLaW5nZG9tKRdFbmdsaXNoIChVbml0ZWQgU3RhdGVzKQ9GcmVuY2ggKEZyYW5jZSkTR2FsaWNpYW4gKEdhbGljaWFuKRBHZXJtYW4gKEdlcm1hbnkpD0l0YWxpYW4gKEl0YWx5KRNQb3J0dWd1ZXNlIChCcmF6aWwpFVBvcnR1Z3Vlc2UgKFBvcnR1Z2FsKRNTcGFuaXNoIChBcmdlbnRpbmEpElNwYW5pc2ggKENvbG9tYmlhKRBTcGFuaXNoIChNZXhpY28pD1NwYW5pc2ggKFNwYWluKRUOD0Jhc3F1ZSAoQmFzcXVlKRFDYXRhbGFuIChDYXRhbGFuKRhFbmdsaXNoIChVbml0ZWQgS2luZ2RvbSkXRW5nbGlzaCAoVW5pdGVkIFN0YXRlcykPRnJlbmNoIChGcmFuY2UpE0dhbGljaWFuIChHYWxpY2lhbikQR2VybWFuIChHZXJtYW55KQ9JdGFsaWFuIChJdGFseSkTUG9ydHVndWVzZSAoQnJhemlsKRVQb3J0dWd1ZXNlIChQb3J0dWdhbCkTU3BhbmlzaCAoQXJnZW50aW5hKRJTcGFuaXNoIChDb2xvbWJpYSkQU3BhbmlzaCAoTWV4aWNvKQ9TcGFuaXNoIChTcGFpbikUKwMOZ2dnZ2dnZ2dnZ2dnZ2cWAQINZAIHD2QWAmYPZBYCAgEPEGQQFQMFSm9yZ2UHTWFyaXNvbAZNb25pY2EVAy1Wb2NhbGl6ZXIgRXhwcmVzc2l2ZSBKb3JnZSBQcmVtaXVtIEhpZ2ggMjJrSHovVm9jYWxpemVyIEV4cHJlc3NpdmUgTWFyaXNvbCBQcmVtaXVtIEhpZ2ggMjJrSHouVm9jYWxpemVyIEV4cHJlc3NpdmUgTW9uaWNhIFByZW1pdW0gSGlnaCAyMmtIehQrAwNnZ2dkZAILDw8WAh4EVGV4dGVkZGTmsgGpgX/ypJYbJ6yJk6ADXPXV5czepn//KxJlCBPNFA==",
            "__VIEWSTATEGENERATOR": "CA0B0334",
            "__EVENTVALIDATION": "/wEdABW8yIECg1BKZ4qISfIfPZPCRPan6xhbSS1PIg8K/UsVxrD/pNmS0s/A+w1rah2YhRHmgnMQl6mB6aTs5vI0wULx2pCX7+6ls6ZQ2VZGfpG9HQgGLKsowKGYG4FmVOUaoVcXneTsG2OF5bzQKdS4g9XiFxg1dXUnHsrzIrmimT+yELAr2rxOIJnuZsrHTu1hW+mrkzyi5tkymvZYx/M5Md1C5SMB1MSZA/tGqMAodrsZzFv5ze0cj5cKYRZFvXcf3p7lOmlE2cSJ/kHxsbhxNFLUF+769Rjp/EV2/GPmqEAycD4MN2nwyyNcmyw7ddC2nK8nTT2UUbR6syEoqjmLHEGjcegFrjno3zsMIHCkNe3TEIwVINbc3XvGc3I0CbnlX1OR5fDOo3rr2jqR3fgcE+pB4cML+Qld+5Jalgh0n+901PS6a+/VoxzUcWico14GexqcJoon/nkkJJrE7nvKH3vpK7+jIuEnB/6SYtVfDVbtoA==",
            "tbTexto": text,
            "ddlIdioma": language,
            "ddlVoz": f"Vocalizer Expressive {voice} Premium High 22kHz",
            "bEscuchar": "Escuchar"
        }
        
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form_data, headers=self.base_headers, timeout=timeout) as response:
                if response.status == 200:
                    logging.warning("Saving file loquendo voice")
                    try:
                        file_name = hashlib.md5(text.encode("utf-8")).hexdigest()
                        f = open(f"./assets/audio/loquendo/{file_name}.mp3", "wb")
                        content = await response.read()
                        f.write(content)
                        f.close()
                        return f"./assets/audio/loquendo/{file_name}.mp3" # hash
                    except Exception as e:
                        logging.error("While downloading audio file", exc_info=True)
                        return ""
                else:
                    logging.error("Failed downloading with status 500", exc_info=True)
                    return ""
                
    async def getContentFromPage(self, url, headers=None):
        headers = dict(self.base_headers, **headers) if headers else self.base_headers
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    try:
                        content = await response.text()
                        return content
                    except Exception as e:
                        logging.error(f"While fetching page content from {url}", exc_info=True)
                        return ""
                else:
                    return ""

    def streaming(self, url, client, buffer_size=STREAM_BUFFER_SIZE):
        headers = {
            'Accept-Encoding': 'identity;q=1, *;q=0',
            'accept': "*/*",
            "Connection": "keep-alive",
            "host": "s3.radio.co",
            "Range": "bytes=0-",
            "Referer": "http://radio.garden/visit/freetown/LPlUvV8C",
            "Sec-Fetch-Dest": "audio",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site"
        }
        headers = dict(self.base_headers, **headers)
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            for data in r.iter_content(buffer_size):
                if not self.stream or not client.is_connected():
                    r.connection.close()
                    break
                args = []
                args.extend(('ffmpeg','-i','-','-f', 's16le', '-ar', '48000', '-ac', '2', '-loglevel', 'warning', 'pipe:1'))
                process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=None, stdin=subprocess.PIPE)
                process.stdin.write(data)
                process.stdin.close()
                audio_source = discord.PCMAudio(process.stdout)
                client.play(audio_source)
                while client.is_playing():
                    time.sleep(0.001)
                    pass
                process.kill()