from bs4 import BeautifulSoup
import requests
import re
from Utils.NetworkUtils import NetworkUtils

"""
Soup is responsible for parsing and processing all HTML/XML input data
"""

class Soup():
    
    def __init__(self):
        self.network_utils = NetworkUtils()
        
    async def get_price_g2a(self, url, currency = "USD"):
        headers = {
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'referer': 'https://www.g2a.com/',
            'cookie': f"bm_sz=0F84AC03C7911CFAC0941EB02E4CA5C1~YAAQewoWAjOX185xAQAA8+HHzwcWKTDRMSD7hJ0VRCTjsFMdFJqQPPQ8hSOmO71gegzJThJ3n/lcJhcRUIEWhf2Uo//urnlIJnvX2mljvZZBuohR91pl5LyVXZ53V5yfhlKzOYDcmQ+JWMyF+9Fy6UW0Wbp/CdO+q6PHJHh1W+bgL1rLUXSUJgtIEFfj; skc=4ef7b8a8-6cbf-4b00-8ad3-e2b6ba248ac7-1588328916; cart-v2=true; gtm_client_id=0900566535.1588328917034; _abck=3F122858A7E8879ED8F62DDFD29E9C9F~0~YAAQewoWAjuX185xAQAAkO/HzwNNOLO/dVxG0EF9H3bHozepSPd64t8hbEav8Q/N60lLIwQ1mqIYPH3AXryS7PMeQM9i7nf99LAZubOEYrwwOGJMPliySBHKHw8xMLX6vX34w4cMwnkoemeaCB2CwczBkHKucskwh+nFj6K8NhB1SixxNeGAQsAbz0XDsdGwdX64pesqqs2DvoSrGSke0xSO024eii8UyXdEST5NQhx+fzGXIb7vxa4LW9mJ+blYSJt8vWmoai9hyJUK3ty/udntaw18yubvHdR4i8y5AEDrrpo+ym5cpZOYP45PEsDjXq5DOA==~-1~-1~-1; _gcl_au=1.1.386117768.1588328918; store=german; G2ACOM=n0ihqllg3905a2u3m3je0siie6; currency={currency}; ak_bmsc=B4C4D40EE220D77CD59FAEBDAD71A8C202160A7BEA460000D5F9AB5ECDA1F917~plZQiK+Tj3IS7erAC9pk1O9G4bDQF9wBxoHkgBJ3wXQIL20Gam3zXP/gPCgPFejxx1M7+4JNAnPZ6mJG39LjWDTVBPTSJslrr3wRJzuToJpHv/YSZAFWsmKOthpsx9kxqGLbq4FOuE9ZNkVx4kWHpqjCONtbJpY3z84+waEJ8VPpwSsStqWdMMvyz0ATVoAYpBiaTNeJ4rwfHq0Z0y4c7WsSeuuF6abeT7GZ5iq5QAlag=; _hjid=87122377-3a29-4416-a0b3-4a490e069098; fbbl=true; rdt_uuid=84b61ecd-acdb-4f56-ad5d-49d914bba47e; user_type=retail; luid=b0583bf0c3a4f5c30d5a47b4167ed605c7546c2d; ins-storage-version=2; _uetsid=_uet16b22fd3-5f02-5dd1-aa24-562f5a7e675d; bm_sv=38A2F74F2F8719C30422182BAA24F38F~zYqDvW092CMoPoKV+DkKPu/+bdxkloOngkjTm0lufGxuILj1PyPGC5BHJbCarj6gcCVfndd8+idou/Ele+mXYNn3Da2dUrcN1Q/IwvMYnUa7oPZDuesHOyry1exWCGd7D2+w4tAYWknnDYdasY6Ifw==",
        }
        tag = "span"
        class_ = "offer__price price"
        response = await self.network_utils.get_content_from_page(url, headers=headers)
        soup = BeautifulSoup(response,  "html.parser")
        element = soup.find_all(tag, class_= class_, limit=2)
        if len(element) > 0:
            the_price = element[1].text.strip()
            pattern = re.compile("(\d+)[,|\.](\d{2,})")
            match = pattern.search(the_price)
            return float(match.group())  # price
        else:
            return 0.0
        
    async def get_price_amazon(self, url, currency="USD"):
        id = "priceblock_ourprice"
        tag = "span"
        
        response = await self.network_utils.get_content_from_page(url)
        soup = BeautifulSoup(response, features = "lxml")
        element = soup.find(tag, id = id)
        if element != None:
            the_price = element.text.strip()
            pattern = re.compile("(\d+)[,|\.](\d{2,})")
            match = pattern.search(the_price)
            return float(match.group().replace(",", "."))  # price
        else:
            return 0.0
        
        