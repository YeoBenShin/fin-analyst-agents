import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from get_metrics import fao_pipeline

def run_test():
    symbol = "AAPL"
    print(f"--- Running fao_pipeline for {symbol} ---")
    try:
        metrics = fao_pipeline(symbol, env_path="/Users/yeobe/SideProjects/Antigravity/fin-analyst-agents/.env")
        print("\nPipeline Result Company Info:")
        print(json.dumps(metrics["company_info"], indent=2))
        
        print(f"\nPipeline Result Years: {list(metrics['metrics_by_year'].keys())}")
        
        # Display the most recent year's data
        recent_year = sorted(list(metrics["metrics_by_year"].keys()))[-1]
        print(f"\nPipeline Result for {recent_year} (Most Recent Year):")
        print(json.dumps(metrics["metrics_by_year"][recent_year], indent=2))
        
    except Exception as e:
        print("Error during pipeline execution:", e)

if __name__ == "__main__":
    run_test()
