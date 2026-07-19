import json
import os
import unittest

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from get_metrics import process_metrics

from dotenv import load_dotenv
load_dotenv()
HOME_PATH = os.getenv("HOME_PATH")


def load_fixture(filename):
    path = os.path.join(HOME_PATH, ".agents/skills/financial-data-agent/assets", filename)
    with open(path) as f:
        return json.load(f)


class TestProcessMetrics(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.raw = load_fixture("finnhub_api_output.json")
        cls.result = process_metrics(cls.raw)
        # with open (os.path.join(HOME_PATH, ".agents/skills/financial-data-agent/assets", "processed_metrics.json"), "w") as f:
        #     json.dump(cls.result, f, indent=2, default=str)

    def test_output_has_company_info(self):
        info = self.result["company_info"]
        self.assertEqual(info["symbol"], "AAPL")
        self.assertEqual(info["name"], "Apple Inc")
        self.assertEqual(info["country"], "US")
        self.assertEqual(info["sector"], "Technology")
        self.assertEqual(info["currency"], "USD")
        self.assertIsInstance(info.get("shares_outstanding"), (int, float))

    def test_financial_extraction_is_sorted_list(self):
        extraction = self.result["financial_extraction"]
        self.assertIsInstance(extraction, list)
        self.assertGreater(len(extraction), 0)
        years = [e["year"] for e in extraction]
        self.assertEqual(years, sorted(years))

    def test_each_entry_has_year(self):
        for entry in self.result["financial_extraction"]:
            self.assertIn("year", entry)

    def test_entries_with_reported_financials_have_core_sections(self):
        for entry in self.result["financial_extraction"]:
            if "balance_sheet" not in entry:
                continue
            with self.subTest(year=entry["year"]):
                self.assertIn("income_statement", entry)
                self.assertIn("cash_flow_statement", entry)

    def test_2025_known_values(self):
        by_year = {e["year"]: e for e in self.result["financial_extraction"]}
        year = by_year.get(2025)
        if year is None:
            self.skipTest("No 2025 data")

        bs = year["balance_sheet"]
        self.assertEqual(bs["total_assets"], 359241000000)
        self.assertEqual(bs["cash_and_equivalents"], 35934000000.0)
        self.assertEqual(bs["accounts_receivable"], 39777000000)
        self.assertEqual(bs["inventory"], 5718000000)
        self.assertEqual(bs["current_assets"], 147957000000)
        self.assertEqual(bs["liabilities_current"], 165631000000)
        self.assertEqual(bs["liabilities_total"], 285508000000)
        self.assertEqual(bs["stockholders_equity"], 73733000000.0)
        self.assertEqual(bs["long_term_debt_current"], 12350000000.0)
        self.assertEqual(bs["long_term_debt_noncurrent"], 78328000000.0)
        self.assertEqual(bs["retained_earnings"], -14264000000)
        self.assertEqual(bs["ppe"], 49834000000.0)

        ic = year["income_statement"]
        self.assertEqual(ic["revenue"], 416161000000.0)
        self.assertEqual(ic["cost_of_sales"], 220960000000.0)
        self.assertEqual(ic["gross_profit"], 195201000000)
        self.assertEqual(ic["research_and_development"], 34550000000.0)
        self.assertEqual(ic["selling_general_admin"], 27601000000)

    def test_core_bs_metrics_present_in_2025(self):
        by_year = {e["year"]: e for e in self.result["financial_extraction"]}
        year = by_year.get(2025)
        if year is None:
            self.skipTest("No 2025 data")
        bs = year["balance_sheet"]
        for key in (
            "total_assets", "liabilities_total", "stockholders_equity",
            "cash_and_equivalents", "accounts_receivable",
            "inventory", "current_assets", "liabilities_current",
            "liabilities_noncurrent", "long_term_debt_current",
            "long_term_debt_noncurrent", "retained_earnings",
            "ppe",
        ):
            self.assertIn(key, bs)

    def test_core_ic_metrics_present_in_2025(self):
        by_year = {e["year"]: e for e in self.result["financial_extraction"]}
        year = by_year.get(2025)
        if year is None:
            self.skipTest("No 2025 data")
        ic = year["income_statement"]
        for key in (
            "revenue", "cost_of_sales", "gross_profit",
            "research_and_development", "selling_general_admin",
            "operating_expenses", "operating_income",
            "pre_tax_income", "income_tax_expense", "net_income",
            "eps_basic", "eps_diluted", "shares_basic", "shares_diluted",
        ):
            self.assertIn(key, ic)

    def test_core_cf_metrics_present_in_2025(self):
        by_year = {e["year"]: e for e in self.result["financial_extraction"]}
        year = by_year.get(2025)
        if year is None:
            self.skipTest("No 2025 data")
        cf = year["cash_flow_statement"]
        for key in (
            "net_cash_from_operations", "capital_expenditures",
            "depreciation_amortization", "dividends_paid",
            "repurchases_of_common_stock",
            "net_cash_from_investing", "net_cash_from_financing",
            "accounts_receivable_change", "inventory_change",
            "accounts_payable_change", "income_taxes_paid",
            "interest_paid",
        ):
            self.assertIn(key, cf)

    def test_computed_metrics_merged(self):
        extraction = self.result["financial_extraction"]
        self.assertTrue(
            any("book_value" in e for e in extraction),
            "No computed metrics found in any entry"
        )
        self.assertTrue(
            any("longterm_debt_total_capital" in e for e in extraction),
            "No longtermDebtTotalCapital found in any entry"
        )

    def test_non_null_key_2025_metrics(self):
        by_year = {e["year"]: e for e in self.result["financial_extraction"]}
        year = by_year.get(2025)
        if year is None:
            self.skipTest("No 2025 data")
        self.assertIsNotNone(year["income_statement"]["net_income"])
        self.assertIsNotNone(year["income_statement"]["operating_income"])
        self.assertIsNotNone(year["balance_sheet"]["total_assets"])
        self.assertIsNotNone(year["cash_flow_statement"]["net_cash_from_operations"])


if __name__ == "__main__":
    unittest.main()
