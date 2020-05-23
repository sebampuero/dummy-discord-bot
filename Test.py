from bs4 import BeautifulSoup

soup = BeautifulSoup("<html><body><span>hello</span></body></html>",  "html.parser")
print(soup.find("span"))