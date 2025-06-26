
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

ua = UserAgent()

def fetch_html(url):
    try:
        headers = {'User-Agent': ua.random}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None
