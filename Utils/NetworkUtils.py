import requests
import hashlib

class NetworkUtils():
    
    def __init__(self):
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'upgrade-insecure-requests': '1',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'de-DE,de;q=0.9,es-DE;q=0.8,es;q=0.7,en-US;q=0.6,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate'
        }
    
    def getAndSaveTtsLoquendoVoice(self, text):
        url = "http://nuancevocalizerexpressive.sodels.com/"
        headers = {
            'pragma': 'no-cache',
            'cache-control': 'max-age=0',
            'referer': 'http://nuancevocalizerexpressive.sodels.com/',
            'origin': 'http://nuancevocalizerexpressive.sodels.com',
            'cookie': '_ga=GA1.2.1310227732.1588589777; _gid=GA1.2.1602425444.1588891018; _gat_gtag_UA_161011357_1=1',
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
            "ddlIdioma": "Spanish (Spain)",
            "ddlVoz": "Vocalizer Expressive Jorge Premium High 22kHz",
            "bEscuchar": "Escuchar"
        }
        response = requests.post(url, data = form_data)
        if response.status_code == 200:
            try:
                file_name = hashlib.md5(text.encode("utf-8")).hexdigest()
                f = open(f"./assets/audio/{file_name}.mp3", "wb")
                f.write(response.content)
                f.close()
                return f"./assets/audio/{file_name}.mp3" # hash
            except Exception as e:
                print(f"{str(e)} while downloading audio file")
                return ""
        else:
            return ""