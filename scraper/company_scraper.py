import requests
from .base_scraper import fetch_html
import re
from urllib.parse import urlparse, urljoin
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd


def get_selenium_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return webdriver.Chrome(options=options)


def scrape_company_info(company):
    url = company["url"]
    soup = fetch_html(url)

    description = get_description(soup,url)
    clients = get_clients(soup,url)


    text = soup.get_text(separator="\n", strip=True)

    results = []
    locations = extract_locations(text)
    hq = detect_hq(text, locations)

    if not locations:
        print("No addresses found on website. Trying fallback.")
        locations, hq = fallback_scrape(company["name"])

    if not locations:
        results.append({
            "Company Name": company["name"],
            "Office Location": "Not Found",
            "Is_HQ": "Unknown"
        })

    for loc in locations:
        results.append({
            "Company Name": company["name"],
            "Office Location": loc,
            "Is_HQ": "Yes" if loc == hq else "No"
        })

    return {
        "id": company["id"],
        "name": company["name"],
        "url": company["url"],
        "description": description,
        "offices": results,
        "hq": hq,
        "clients": clients
    }


def is_relevant_about_link(href, anchor_text, keywords):
    href = href.lower().replace("-", " ").replace("_", " ")
    text = anchor_text.lower().strip().replace("-", " ")
    combined = href + " " + text
    return any(kw in combined for kw in keywords)


def get_description(soup, base_url):
    if not soup:
        return ""

    meta_tags = [
        soup.find("meta", attrs={"name": "description"}),
        soup.find("meta", property="og:description")
    ]
    for tag in meta_tags:
        if tag and tag.get("content"):
            return tag.get("content").strip()

    for p in soup.find_all("p"):
        text = p.get_text().strip()
        if len(text.split()) >= 10:
            return text

    keywords = ["about", "who we are", "company", "mission", "overview", "story"]
    about_links = []

    for a in soup.find_all("a", href=True):
        href = a['href']
        anchor_text = a.get_text()
        if is_relevant_about_link(href, anchor_text, keywords):
            full_url = urljoin(base_url, href)
            about_links.append(full_url)

    for link in about_links:
        about_soup = fetch_html(link)
        if about_soup:
            for p in about_soup.find_all("p"):
                text = p.get_text().strip()
                if len(text.split()) >= 10:
                    return text

    return ""




def extract_locations(text):
    address_pattern = re.compile(r"\d{1,5}[\w\s,.-]+(?:USA|United States|UK|Canada|Germany|India|Austria|France)", re.IGNORECASE)
    fallback_pattern = re.compile(r"[A-Z][a-z]+,\s?[A-Z][a-z]+")

    addresses = set()
    for line in text.splitlines():
        if len(line.strip()) < 6:
            continue
        if "@" in line or "www." in line or "http" in line:
            continue
        if address_pattern.search(line):
            addresses.add(address_pattern.search(line).group().strip())
        elif fallback_pattern.search(line):
            addresses.add(fallback_pattern.search(line).group().strip())

    return list(addresses)

def detect_hq(text, addresses):
    keywords = ["headquarters", "hq", "main office", "corporate office"]
    for line in text.splitlines():
        if any(k in line.lower() for k in keywords):
            for addr in addresses:
                if addr in line:
                    return addr
    return addresses[0] if addresses else None

def search_fallback_page(company_name):
    query = f"{company_name} site:linkedin.com OR site:crunchbase.com"
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
    driver = get_selenium_driver()
    driver.get(url)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    for a in soup.find_all("a"):
        href = a.get("href", "")
        if "/url?q=" in href:
            link = href.split("/url?q=")[1].split("&")[0]
            if "linkedin.com/company" in link or "crunchbase.com" in link:
                return link
    return None

def fallback_scrape(company_name):
    url = search_fallback_page(company_name)
    if not url:
        return [], None
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator="\n")
        locations = extract_locations(text)
        hq = detect_hq(text, locations)
        return locations, hq
    except:
        return [], None


def get_clients(soup, base_url):
    clients = set()
    if not soup:
        return []
    for img in soup.find_all("img"):
        alt = img.get("alt", "").strip()
        src = img.get("src", "").strip()

        if not src or len(src) < 5:
            continue

        src_lower = src.lower()
        alt_lower = alt.lower()

        if any(word in src_lower for word in ["logo", "client", "partner", "brand"]) or \
           any(word in alt_lower for word in ["logo", "client", "partner", "customer"]):

            name = alt if alt else extract_name_from_src(src_lower)
            if name:
                clients.add(name.strip())

    return list(clients)

def extract_name_from_src(src):
    name = src.split("/")[-1].split(".")[0]
    name = name.replace("-", " ").replace("_", " ").strip()
    blacklist = ["logo", "icon", "client", "partner", "brand", "image"]
    if any(b in name.lower() for b in blacklist) or len(name) < 3:
        return None
    return name.title()