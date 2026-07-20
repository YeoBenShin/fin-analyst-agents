import sqlite3

def _get(key, d, fallback=None):
    v = d.get(key)
    return v if v is not None else fallback

_INCOME_STATEMENT_FIELDS = [
    "revenue", "cost_of_sales", "gross_profit", "research_and_development",
    "selling_general_admin", "operating_expense", "operating_income",
    "ebitda", "income_tax_expense", "net_income",
]

_BALANCE_SHEET_FIELDS = [
    "total_assets", "liabilities_total", "stockholders_equity",
    "cash_and_equivalents", "accounts_receivable", "accounts_payable",
    "inventory", "ppe", "short_term_debt", "long_term_debt",
    "retained_earnings", "shares_outstanding",
]

_CASH_FLOW_FIELDS = [
    "net_cash_from_operations", "capital_expenditures",
    "depreciation_amortization", "share_based_compensation",
    "repurchases_of_common_stock", "dividends_paid",
    "proceeds_from_issuance_of_long_term_debt",
    "repayments_of_long_term_debt", "free_cash_flow",
]

_COMPUTED_METRICS_FIELDS = [
    "book_value", "gross_margin", "operating_margin", "pretax_margin",
    "net_margin", "roa", "roe", "roic", "current_ratio", "cash_ratio",
    "quick_ratio", "payout_ratio", "dividend_yield", "eps", "pb", "pe",
    "ev_ebitda", "ev_revenue", "total_debt_to_equity",
]

def save_to_db(metrics: dict, db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS company_info (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            country TEXT,
            sector TEXT,
            industry TEXT,
            currency TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS income_statements (
            symbol TEXT, year INTEGER, revenue REAL, cost_of_sales REAL,
            gross_profit REAL, research_and_development REAL,
            selling_general_admin REAL, operating_expense REAL,
            operating_income REAL, ebitda REAL, income_tax_expense REAL,
            net_income REAL,
            PRIMARY KEY (symbol, year),
            FOREIGN KEY (symbol) REFERENCES company_info(symbol)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS balance_sheets (
            symbol TEXT, year INTEGER, total_assets REAL,
            liabilities_total REAL, stockholders_equity REAL,
            cash_and_equivalents REAL, accounts_receivable REAL,
            accounts_payable REAL, inventory REAL, ppe REAL,
            short_term_debt REAL, long_term_debt REAL,
            retained_earnings REAL, shares_outstanding REAL,
            PRIMARY KEY (symbol, year),
            FOREIGN KEY (symbol) REFERENCES company_info(symbol)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cash_flow_statements (
            symbol TEXT, year INTEGER, net_cash_from_operations REAL,
            capital_expenditures REAL, depreciation_amortization REAL,
            share_based_compensation REAL, repurchases_of_common_stock REAL,
            dividends_paid REAL,
            proceeds_from_issuance_of_long_term_debt REAL,
            repayments_of_long_term_debt REAL, free_cash_flow REAL,
            PRIMARY KEY (symbol, year),
            FOREIGN KEY (symbol) REFERENCES company_info(symbol)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS computed_metrics (
            symbol TEXT, year INTEGER, book_value REAL, gross_margin REAL,
            operating_margin REAL, pretax_margin REAL, net_margin REAL,
            roa REAL, roe REAL, roic REAL, current_ratio REAL,
            cash_ratio REAL, quick_ratio REAL, payout_ratio REAL,
            dividend_yield REAL, eps REAL, pb REAL, pe REAL,
            ev_ebitda REAL, ev_revenue REAL, total_debt_to_equity REAL,
            PRIMARY KEY (symbol, year),
            FOREIGN KEY (symbol) REFERENCES company_info(symbol)
        )
        """
    )

    ci = metrics.get("company_info", {})
    cursor.execute(
        """
        INSERT OR REPLACE INTO company_info
        (symbol, name, country, sector, industry, currency)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            ci.get("symbol"),
            ci.get("name"),
            ci.get("country"),
            ci.get("sector"),
            ci.get("industry"),
            ci.get("currency"),
        ),
    )

    symbol = ci.get("symbol")
    entries = metrics.get("financial_extraction", [])

    for entry in entries:
        year = entry.get("year")
        bs = entry.get("balance_sheet", {})
        ic = entry.get("income_statement", {})
        cf = entry.get("cash_flow_statement", {})

        ic_values = [_get(f, ic) for f in _INCOME_STATEMENT_FIELDS]
        cursor.execute(
            f"""
            INSERT OR REPLACE INTO income_statements
            (symbol, year, {', '.join(_INCOME_STATEMENT_FIELDS)})
            VALUES ({', '.join(['?'] * (2 + len(_INCOME_STATEMENT_FIELDS)))})
            """,
            [symbol, year] + ic_values,
        )

        bs_values = [_get(f, bs) for f in _BALANCE_SHEET_FIELDS[:-1]]
        bs_values.append(ci.get("shares_outstanding"))
        cursor.execute(
            f"""
            INSERT OR REPLACE INTO balance_sheets
            (symbol, year, {', '.join(_BALANCE_SHEET_FIELDS)})
            VALUES ({', '.join(['?'] * (2 + len(_BALANCE_SHEET_FIELDS)))})
            """,
            [symbol, year] + bs_values,
        )

        cf_values = [_get(f, cf) for f in _CASH_FLOW_FIELDS]
        cursor.execute(
            f"""
            INSERT OR REPLACE INTO cash_flow_statements
            (symbol, year, {', '.join(_CASH_FLOW_FIELDS)})
            VALUES ({', '.join(['?'] * (2 + len(_CASH_FLOW_FIELDS)))})
            """,
            [symbol, year] + cf_values,
        )

        cm_values = [_get(f, entry) for f in _COMPUTED_METRICS_FIELDS]
        cursor.execute(
            f"""
            INSERT OR REPLACE INTO computed_metrics
            (symbol, year, {', '.join(_COMPUTED_METRICS_FIELDS)})
            VALUES ({', '.join(['?'] * (2 + len(_COMPUTED_METRICS_FIELDS)))})
            """,
            [symbol, year] + cm_values,
        )

    conn.commit()
    conn.close()


def load_from_db(symbol: str, db_path: str) -> dict | None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='company_info'"
    )
    if not cursor.fetchone():
        conn.close()
        return None

    cursor.execute(
        "SELECT name, country, sector, industry, currency "
        "FROM company_info WHERE symbol = ?",
        (symbol,),
    )
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return None

    company_info = {
        "symbol": symbol,
        "name": row[0],
        "country": row[1],
        "sector": row[2],
        "industry": row[3],
        "currency": row[4],
    }

    cursor.execute(
        "SELECT year FROM income_statements WHERE symbol = ? ORDER BY year",
        (symbol,),
    )
    years = [r[0] for r in cursor.fetchall()]

    financial_extraction = []
    for year in years:
        entry = {"year": year}

        cursor.execute(
            f"SELECT {', '.join(_INCOME_STATEMENT_FIELDS)} "
            "FROM income_statements WHERE symbol = ? AND year = ?",
            (symbol, year),
        )
        row = cursor.fetchone()
        entry["income_statement"] = (
            dict(zip(_INCOME_STATEMENT_FIELDS, row)) if row else {f: None for f in _INCOME_STATEMENT_FIELDS}
        )

        cursor.execute(
            f"SELECT {', '.join(_BALANCE_SHEET_FIELDS)} "
            "FROM balance_sheets WHERE symbol = ? AND year = ?",
            (symbol, year),
        )
        row = cursor.fetchone()
        if row:
            bs_dict = dict(zip(_BALANCE_SHEET_FIELDS, row))
            bs_dict.pop("shares_outstanding", None)
            entry["balance_sheet"] = bs_dict
        else:
            entry["balance_sheet"] = {f: None for f in _BALANCE_SHEET_FIELDS if f != "shares_outstanding"}

        cursor.execute(
            f"SELECT {', '.join(_CASH_FLOW_FIELDS)} "
            "FROM cash_flow_statements WHERE symbol = ? AND year = ?",
            (symbol, year),
        )
        row = cursor.fetchone()
        entry["cash_flow_statement"] = (
            dict(zip(_CASH_FLOW_FIELDS, row)) if row else {f: None for f in _CASH_FLOW_FIELDS}
        )

        cursor.execute(
            f"SELECT {', '.join(_COMPUTED_METRICS_FIELDS)} "
            "FROM computed_metrics WHERE symbol = ? AND year = ?",
            (symbol, year),
        )
        row = cursor.fetchone()
        computed = dict(zip(_COMPUTED_METRICS_FIELDS, row)) if row else {f: None for f in _COMPUTED_METRICS_FIELDS}
        entry.update(computed)

        financial_extraction.append(entry)

    conn.close()

    return {
        "company_info": company_info,
        "financial_extraction": financial_extraction,
    }


def query_database(query: str = None, db_path: str = None) -> list | dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if query is None:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT symbol, name FROM company_info")
        companies = {}
        for row in cursor.fetchall():
            companies[row["symbol"]] = {"name": row["name"], "years": []}

        cursor.execute(
            "SELECT symbol, year FROM income_statements ORDER BY year"
        )
        for row in cursor.fetchall():
            sym = row["symbol"]
            if sym in companies:
                companies[sym]["years"].append(str(row["year"]))

        conn.close()
        return {
            "tables": tables,
            "company_count": len(companies),
            "metrics_count": sum(len(c["years"]) for c in companies.values()),
            "companies": companies,
        }

    cursor.execute(query)
    if cursor.description is None:
        conn.commit()
        conn.close()
        return []
    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return results
