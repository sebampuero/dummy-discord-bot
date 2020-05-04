from Soup import Soup

soup = Soup()

price = soup.get_price_g2a("https://www.g2a.com/call-of-duty-black-ops-iii-steam-key-global-i10000007206010", "EUR")
price1 = soup.get_price_amazon("https://www.amazon.de/Beleuchtungs-Modi-Schreibtischunterlage-Wasserdicht-Computer-Professionelle/dp/B07L5ZX4Y4/ref=sr_1_9?__mk_de_DE=%C3%85M%C3%85%C5%BD%C3%95%C3%91&dchild=1&keywords=mousepad&qid=1588471288&sr=8-9&swrs=F9CF0D21AF2D29C9D930C1740701B03A")

print(price, price1)