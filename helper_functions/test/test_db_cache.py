import os
import sqlite3
import unittest
from unittest.mock import patch

# Add parent helper_functions directory to path to import get_metrics.
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from get_metrics import fao_pipeline

class TestDBCache(unittest.TestCase):
    def setUp(self):
        # Use a temporary test database file
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_financial_data.db")
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass
            
    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_e2e_caching(self):
        symbol = "MSFT"
        # We need a valid path to env if we are wrapping the extract_company_data or if we mock it completely.
        # Let's mock extract_company_data to return a realistic mock payload so compute_fao_metrics can process it.
        mock_raw_data = {
            "symbol": symbol,
            "profile": {
                "name": "Microsoft Corp",
                "country": "US",
                "finnhubIndustry": "Technology",
                "currency": "USD",
                "shareOutstanding": 7400.0
            },
            "quote": {
                "c": 420.0
            },
            "reported_financials": {
                "data": [
                    {
                        "year": 2024,
                        "form": "10-K",
                        "report": {
                            "bs": [
                                {"concept": "Assets", "value": 470000000000.0},
                                {"concept": "Liabilities", "value": 250000000000.0},
                                {"concept": "AssetsCurrent", "value": 180000000000.0},
                                {"concept": "LiabilitiesCurrent", "value": 110000000000.0},
                                {"concept": "StockholdersEquity", "value": 220000000000.0}
                            ],
                            "ic": [
                                {"concept": "RevenueFromContractWithCustomerExcludingAssessedTax", "value": 245000000000.0},
                                {"concept": "NetIncomeLoss", "value": 88000000000.0},
                                {"concept": "OperatingIncomeLoss", "value": 109000000000.0}
                            ],
                            "cf": [
                                {"concept": "DepreciationDepletionAndAmortization", "value": 14000000000.0},
                                {"concept": "PaymentsOfDividends", "value": -28000000000.0}
                            ]
                        }
                    }
                ]
            },
            "basic_financials": {}
        }
        
        # 1. First call: Should query the mock API (extract_company_data)
        with patch('get_metrics.extract_company_data', return_value=mock_raw_data) as mock_extract:
            metrics1 = fao_pipeline(symbol, env_path=None, db_path=self.db_path)
            
            # Verify it was called once
            mock_extract.assert_called_once_with(symbol, None)
            
        # Verify database exists and tables were created
        self.assertTrue(os.path.exists(self.db_path))
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        self.assertIn("company_info", tables)
        self.assertIn("financial_metrics", tables)
        
        # Verify symbol was stored in the database
        cursor.execute("SELECT symbol FROM company_info WHERE symbol=?", (symbol,))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], symbol)
        conn.close()
        
        # 2. Second call: Should read from database and NOT call extract_company_data
        with patch('get_metrics.extract_company_data') as mock_extract2:
            metrics2 = fao_pipeline(symbol, env_path=None, db_path=self.db_path)
            
            # Verify API was NOT called
            mock_extract2.assert_not_called()
            
            # Verify data returned from cache matches the first run's shape
            self.assertEqual(metrics1["company_info"]["symbol"], metrics2["company_info"]["symbol"])
            self.assertEqual(metrics1["company_info"]["name"], metrics2["company_info"]["name"])
            self.assertEqual(metrics1["metrics_by_year"], metrics2["metrics_by_year"])

    def test_query_database(self):
        from get_metrics import query_database, save_to_db
        
        # Save some mock data first
        mock_data = {
            "company_info": {
                "symbol": "TSLA",
                "name": "Tesla Inc",
                "country": "US",
                "sector": "Automotive",
                "industry": "Automotive",
                "currency": "USD"
            },
            "metrics_by_year": {
                "2023": {"source": "reported", "revenue": 96000000000.0},
                "2024": {"source": "reported", "revenue": 105000000000.0}
            }
        }
        save_to_db(mock_data, self.db_path)
        
        # 1. Custom query test
        res_custom = query_database("SELECT symbol, name FROM company_info", db_path=self.db_path)
        self.assertEqual(len(res_custom), 1)
        self.assertEqual(res_custom[0]["symbol"], "TSLA")
        self.assertEqual(res_custom[0]["name"], "Tesla Inc")
        
        # 2. Summary query test (when query is None)
        summary = query_database(db_path=self.db_path)
        self.assertIn("tables", summary)
        self.assertIn("company_count", summary)
        self.assertIn("metrics_count", summary)
        self.assertIn("companies", summary)
        
        self.assertEqual(summary["company_count"], 1)
        self.assertEqual(summary["metrics_count"], 2)
        self.assertIn("TSLA", summary["companies"])
        self.assertEqual(summary["companies"]["TSLA"]["years"], ["2023", "2024"])
        self.assertEqual(summary["companies"]["TSLA"]["name"], "Tesla Inc")

if __name__ == "__main__":
    unittest.main()
