```json
{
  "financial_extraction": 
    "company_info": {
      "symbol": "string",
      "name": "string",
      "country": "string",
      "sector": "string",
      "industry": "string",
      "currency": "string",
    }
    "metrics": [
      {
        "metadata": {
          "shares_outstanding": "float"
          "year": "int"
        }
        "ticker": "string",
        "source_utilized": "string",
        "fiscal_year": "integer",
        "income_statement": {
          "revenue": "float",
          "cost_of_sales": "float",
          "gross_profit": "float",
          "research_and_development": "float",
          "selling_general_admin": "float",
          "operating_expense": "float",
          "operating_income": "float",
          "ebitda": "float",
          "income_tax_expense": "float",
          "net_income": "float",
        },
        "balance_sheet": {
          "total_assets": "float",
          "liabilities_total": "float",
          "stockholders_equity": "float",
          "cash_and_equivalents": "float",
          "accounts_receivable": "float",
          "accounts_payable": "float",
          "inventory": "float",
          "ppe": "float",
          "short_term_debt": "float",
          "long_term_debt": "float",
          "retained_earnings": "float"
        },
        "cash_flow_statement": {
          "net_cash_from_operations": "float",
          "capital_expenditures": "float",
          "depreciation_amortization": "float",
          "share_based_compensation": "float",
          "repurchases_of_common_stock": "float",
          "dividends_paid": "float",
          "proceeds_from_issuance_of_long_term_debt": "float",
          "repayments_of_long_term_debt": "float",
          "free_cash_flow": "float"
        },
        "computed_metrics": {
          "book_value": "float",
          "gross_margin": "float",
          "operating_margin": "float",
          "pretax_margin": "float",
          "net_margin": "float",
          "roa": "float",
          "roe": "float",
          "roic": "float",
          "current_ratio": "float",
          "cash_ratio": "float",
          "quick_ratio": "float",
          "payout_ratio": "float",
          "dividend_yield": "float",
          "eps": "float",
          "pb": "float",
          "pe": "float",
          "ev_ebitda": "float",
          "ev_revenue": "float",
          "total_debt_to_equity": "float"
        }
      }
    ]
}
```