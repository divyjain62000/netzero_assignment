
import json
from scraper.company_scraper import scrape_company_info
from scraper.news_scraper import scrape_latest_news
from utils.excel_writer import write_to_excel

def main():
    with open("data/companies.json", "r") as f:
        companies = json.load(f)

    all_data = []

    for company in companies:
        print(f"Scraping: {company['name']}")
        company_info = scrape_company_info(company)
        news_articles = scrape_latest_news(company)
        company_info["news"] = news_articles
        all_data.append(company_info)

    write_to_excel(all_data)
    print("All data saved to output/netzero_data.xlsx")

if __name__ == "__main__":
    main()
