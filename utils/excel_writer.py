
import pandas as pd
import os

def write_to_excel(data):
    os.makedirs("output", exist_ok=True)

    companies_table = []
    offices_table = []
    clients_table = []
    news_table = []

    for company in data:
        companies_table.append({
            "Company ID": company["id"],
            "Name": company["name"],
            "URL": company["url"],
            "Description": company["description"],
            "HQ": company["hq"]
        })

        for location in company["offices"]:
            offices_table.append({
                "Company ID": company["id"],
                "Office Location": location["Office Location"],
                "Is Headquarter":  location["Is_HQ"]
            })

        for client in company["clients"]:
            clients_table.append({
                "Company ID": company["id"],
                "Client": client
            })

        for article in company["news"]:
            news_table.append({
                "Company ID": company["id"],
                "Title": article["title"],
                "Date": article["date"],
                "URL": article["url"],
                "Summary": article["summary"]
            })

    with pd.ExcelWriter("output/netzero_data.xlsx", engine="openpyxl") as writer:
        pd.DataFrame(companies_table).to_excel(writer, sheet_name="Companies", index=False)
        pd.DataFrame(offices_table).to_excel(writer, sheet_name="Offices", index=False)
        pd.DataFrame(clients_table).to_excel(writer, sheet_name="Clients", index=False)
        pd.DataFrame(news_table).to_excel(writer, sheet_name="News", index=False)

    print("Excel export complete.")
