#!/usr/bin/env python3
from get_metrics import fda_pipeline
from db_helper import query_database
import os
import sys 
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH")

def test_save_and_query(ticker: str = "AAPL"):
    # 1. Run the pipeline to populate the DB
    print(f"Running fda_pipeline for {ticker}...")
    metrics = fda_pipeline(ticker, env_path="/Users/yeobe/SideProjects/Antigravity/fin-analyst-agents/.env")
    print(f"Got {len(metrics['financial_extraction'])} fiscal years of data\n")

    # 2. Query the DB with a SQL statement to verify data
    query = f"SELECT * FROM financial_metrics WHERE symbol = '{ticker}' ORDER BY year"
    results = query_database(query=query, db_path=DB_PATH)
    print("Stored financial_metrics rows:")
    for row in results:
        print(row)

    # 3. Also check company_info
    results2 = query_database("SELECT * FROM company_info", db_path=DB_PATH)
    print("\nStored company_info rows:")
    for row in results2:
        print(row)

if __name__ == "__main__":
    args = sys.argv
    if len(args) < 2:
        print("Please provide a ticker symbol as an argument.")
        sys.exit(1)
    test_save_and_query(ticker=args[1])
