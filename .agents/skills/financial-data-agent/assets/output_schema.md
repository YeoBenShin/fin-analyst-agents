```json
{
  "financial_extraction": [
    {
      "ticker": "string",
      "source_utilized": "string",
      "fiscal_year": "integer",
      "income_statement": {
        "revenue": "float",
        "gross_profit": "float",
        "ebitda": "float",
        "operating_income": "float",
        "net_income": "float",
        "eps_diluted": "float",
        "tax_expense": "float"
      },
      "balance_sheet": {
        "total_assets": "float",
        "cash_and_equivalents": "float",
        "receivables": "float",
        "inventory": "float",
        "total_liabilities": "float",
        "short_term_debt": "float",
        "long_term_debt": "float",
        "total_equity": "float",
        "retained_earnings": "float"
      },
      "cash_flow_statement": {
        "net_cash_provided_by_operating_activities": "float",
        "capital_expenditures": "float",
        "free_cash_flow": "float",
        "dividends_paid": "float",
        "repurchase_of_common_stock": "float"
      },
      "corporate_actions": {
        "dividend_history": [{"ex_date": "string", "amount": "float"}],
        "buyback_history": [{"fiscal_year": "integer", "total_spend": "float"}]
      },
      "computed_metrics": {
        "ebitda_margin": "float",
        "current_ratio": "float",
        "book_value": "float",
        "dividend_per_share": "float",
        "dividend_yield": "float",
        "pe_ratio": "float",
        "pb_ratio": "float",
        "income_growth_rate": "float",
        "revenue_growth_rate": "float"
      }
    }
  ]
}
```
## output that is stored in the data that is received and processed from finnhub
{
  'symbol': 'AAPL',
  'year': '2025',
  'source': 'reported_financials',
  'revenue': 416161000000.0,
  'net_income': 112010000000.0,
  'operating_income': 133050000000.0,
  'ebitda': 144748000000.0, 
  'ebitda_margin': 0.3478173110887373, 
  'current_ratio': 0.8932929222186667, 
  'book_value': 73733000000.0, 
  'dividends_paid': 15421000000.0, 
  'dividend_per_share': 1.0499504335700902, 
  'dividend_yield': 0.0033297933323927762, 
  'pe_ratio': 41.346472236407465, 
  'pb_ratio': 62.81065947676075, 
  'income_growth_rate': 0.19495177946573355, 
  'revenue_growth_rate': 0.0642551178283274
}