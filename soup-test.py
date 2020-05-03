from bs4 import BeautifulSoup
import requests
import re
from fake_useragent import UserAgent

ua = UserAgent()

url = "https://www.amazon.de/KabelDirekt-Kabel-kompatibel-Highspeed-Ethernet/dp/B004BEMD5Q/ref=sr_1_4?__mk_de_DE=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=D1IPQMUDFCRJ&dchild=1&keywords=hdmi+kabel&qid=1588469685&sprefix=hdmi%2Caps%2C174&sr=8-4"
currency = "EUR"

headers = {
    'user-agent': ua.random
}

tag = "span"
id = "priceblock_ourprice"
        
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content,  "html.parser")
element = soup.find_all(tag, id = id)
if len(element) > 0:
    the_price = element[0].text.strip()
    pattern = re.compile("(\d+)[,|\.](\d{2,})")
    match = pattern.search(the_price)
    print(float(match.group().replace(",", ".")))  # price
else:
    print(0.0)
