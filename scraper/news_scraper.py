from googlesearch import search
from bs4 import BeautifulSoup
import requests
import time
from fake_useragent import UserAgent

ua = UserAgent()


def extract_dates_from_text(text, max_results=5):
    potential_dates = []
    seen = set()

    date_patterns = [
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[ .,-]+\d{1,2}[ .,-]+\d{4}',
        r'\b\d{1,2}[ .,-]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[ .,-]+\d{4}',
        r'\b\d{4}-\d{2}-\d{2}',
    ]

    for pattern in date_patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            try:
                dt = date_parse(match, fuzzy=True).date()
                if dt not in seen:
                    seen.add(dt)
                    potential_dates.append(str(dt))
                    if len(potential_dates) >= max_results:
                        return potential_dates
            except:
                continue

    return potential_dates

def extract_article_date(soup):
    meta_tags = [
        {"name": "article:published_time"},
        {"property": "article:published_time"},
        {"name": "og:published_time"},
        {"property": "og:published_time"},
        {"itemprop": "datePublished"},
        {"name": "date"},
    ]
    for attrs in meta_tags:
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            return tag["content"].strip()

    time_tag = soup.find("time", {"datetime": True})
    if time_tag:
        return time_tag["datetime"]

    for tag in soup.find_all(["time", "span", "p", "div"]):
        text = tag.get_text().strip()
        date_list=extract_dates_from_text(text)
        if date_list!=None and len(date_list)>0:
            return date_list[0]
    return None

def summarize_article(url):
    headers = {'User-Agent': ua.random}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.title.string.strip() if soup.title else None
        meta = soup.find("meta", {"name": "description"}) or \
               soup.find("meta", {"property": "og:description"}) or \
               soup.find("meta", {"name": "twitter:description"})

        summary = meta['content'].strip() if meta and meta.get("content") else ""
        date = extract_article_date(soup)

        return {"title": title, "summary": summary[:300], "date": date, "url": url}
    except Exception as e:
        return {"title": None, "summary": None, "date": None, "url": url, "error": str(e)}

def find_google_news(company_name):
    query = f"{company_name} latest news"
    for url in search(query, num_results=5):
        if url.startswith("http"):
            return summarize_article(url)
    return {"title": None, "summary": None, "date": None, "url": None}

def find_company_news_section(company_url):
    headers = {'User-Agent': ua.random}
    try:
        res = requests.get(company_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        for link in soup.find_all("a", href=True):
            if any(k in link['href'].lower() for k in ["news", "press", "updates"]):
                full_url = link['href'] if "http" in link['href'] else company_url.rstrip("/") + "/" + link["href"].lstrip("/")
                return summarize_article(full_url)
    except:
        return None
    return None

def scrape_latest_news(company):

    
    site_result = find_company_news_section(company["url"])
    google_result = find_google_news(company["name"])
    articles=[]
    for label, result in [("From Company Website", site_result), ("From Google News", google_result)]:
        if result and isinstance(result, dict):
            articles.append({
                    "title": result.get('title'),
                    "date": result.get('date'),
                    "url": result.get('url'),
                    "summary": result.get('summary')
                })
    return articles
