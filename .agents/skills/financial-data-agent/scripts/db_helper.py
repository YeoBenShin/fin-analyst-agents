import sqlite3
import json


def _normalize_financial_extractions(metrics: dict) -> list[dict]:
    financial_extraction = metrics.get("financial_extraction")
    if isinstance(financial_extraction, list):
        return financial_extraction

    legacy_years = metrics.get("metrics_by_year", {})
    normalized = []
    company_info = metrics.get("company_info", {})
    symbol = company_info.get("symbol")
    for year, summary in legacy_years.items():
        normalized.append({
            "ticker": symbol,
            "source_utilized": summary.get("source"),
            "fiscal_year": int(year) if isinstance(year, str) and year.isdigit() else year,
            "income_statement": {
                "revenue": summary.get("revenue"),
                "gross_profit": None,
                "ebitda": summary.get("ebitda"),
                "operating_income": summary.get("operating_income"),
                "net_income": summary.get("net_income"),
                "eps_diluted": None,
                "tax_expense": None,
            },
            "balance_sheet": {
                "total_assets": None,
                "cash_and_equivalents": None,
                "receivables": None,
                "inventory": None,
                "total_liabilities": None,
                "short_term_debt": None,
                "long_term_debt": None,
                "total_equity": None,
                "retained_earnings": None,
            },
            "cash_flow_statement": {
                "net_cash_provided_by_operating_activities": None,
                "capital_expenditures": None,
                "free_cash_flow": summary.get("free_cash_flow"),
                "dividends_paid": summary.get("dividends_paid"),
                "repurchase_of_common_stock": None,
            },
            "corporate_actions": {
                "dividend_history": [],
                "buyback_history": [],
            },
            "option_behaviours": {
                "ebitda_margin": summary.get("ebitda_margin"),
                "current_ratio": summary.get("current_ratio"),
                "book_value": summary.get("book_value"),
                "dividend_per_share": summary.get("dividend_per_share"),
                "dividend_yield": summary.get("dividend_yield"),
                "pe_ratio": summary.get("pe_ratio"),
                "pb_ratio": summary.get("pb_ratio"),
                "income_growth_rate": summary.get("income_growth_rate"),
                "revenue_growth_rate": summary.get("revenue_growth_rate"),
            },
        })
    return normalized


def _row_to_financial_extraction(symbol: str, row: sqlite3.Row) -> dict:
    year = row[1]
    source = row[2]
    revenue = row[3]
    net_income = row[4]
    operating_income = row[5]
    ebitda = row[6]
    ebitda_margin = row[7]
    current_ratio = row[8]
    book_value = row[9]
    dividends_paid = row[10]
    dividend_per_share = row[11]
    dividend_yield = row[12]
    pe_ratio = row[13]
    pb_ratio = row[14]
    income_growth_rate = row[15]
    revenue_growth_rate = row[16]

    return {
        "ticker": symbol,
        "source_utilized": source,
        "fiscal_year": int(year) if isinstance(year, str) and year.isdigit() else year,
        "income_statement": {
            "revenue": revenue,
            "gross_profit": None,
            "ebitda": ebitda,
            "operating_income": operating_income,
            "net_income": net_income,
            "eps_diluted": None,
            "tax_expense": None,
        },
        "balance_sheet": {
            "total_assets": None,
            "cash_and_equivalents": None,
            "receivables": None,
            "inventory": None,
            "total_liabilities": None,
            "short_term_debt": None,
            "long_term_debt": None,
            "total_equity": None,
            "retained_earnings": None,
        },
        "cash_flow_statement": {
            "net_cash_provided_by_operating_activities": None,
            "capital_expenditures": None,
            "free_cash_flow": None,
            "dividends_paid": dividends_paid,
            "repurchase_of_common_stock": None,
        },
        "corporate_actions": {
            "dividend_history": [],
            "buyback_history": [],
        },
        "option_behaviours": {
            "ebitda_margin": ebitda_margin,
            "current_ratio": current_ratio,
            "book_value": book_value,
            "dividend_per_share": dividend_per_share,
            "dividend_yield": dividend_yield,
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "income_growth_rate": income_growth_rate,
            "revenue_growth_rate": revenue_growth_rate,
        },
    }


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
        CREATE TABLE IF NOT EXISTS financial_metrics (
            symbol TEXT,
            year TEXT,
            source TEXT,
            revenue REAL,
            net_income REAL,
            operating_income REAL,
            ebitda REAL,
            ebitda_margin REAL,
            current_ratio REAL,
            book_value REAL,
            dividends_paid REAL,
            dividend_per_share REAL,
            dividend_yield REAL,
            pe_ratio REAL,
            pb_ratio REAL,
            income_growth_rate REAL,
            revenue_growth_rate REAL,
            PRIMARY KEY (symbol, year),
            FOREIGN KEY (symbol) REFERENCES company_info(symbol)
        )
        """
    )

    ci = metrics.get("company_info", {})
    cursor.execute(
        """
        INSERT OR REPLACE INTO company_info (symbol, name, country, sector, industry, currency)
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
    financial_extraction = _normalize_financial_extractions(metrics)
    for entry in financial_extraction:
        year = entry.get("fiscal_year")
        income_statement = entry.get("income_statement", {})
        cash_flow_statement = entry.get("cash_flow_statement", {})
        option_behaviours = entry.get("option_behaviours", {})
        cursor.execute(
            """
            INSERT OR REPLACE INTO financial_metrics (
                symbol, year, source, revenue, net_income, operating_income,
                ebitda, ebitda_margin, current_ratio, book_value, dividends_paid,
                dividend_per_share, dividend_yield, pe_ratio, pb_ratio,
                income_growth_rate, revenue_growth_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol,
                year,
                entry.get("source_utilized"),
                income_statement.get("revenue"),
                income_statement.get("net_income"),
                income_statement.get("operating_income"),
                income_statement.get("ebitda"),
                option_behaviours.get("ebitda_margin"),
                option_behaviours.get("current_ratio"),
                option_behaviours.get("book_value"),
                cash_flow_statement.get("dividends_paid"),
                option_behaviours.get("dividend_per_share"),
                option_behaviours.get("dividend_yield"),
                option_behaviours.get("pe_ratio"),
                option_behaviours.get("pb_ratio"),
                option_behaviours.get("income_growth_rate"),
                option_behaviours.get("revenue_growth_rate"),
            ),
        )

    conn.commit()
    conn.close()


def load_from_db(symbol: str, db_path: str) -> dict | None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='company_info'")
    if not cursor.fetchone():
        conn.close()
        return None

    cursor.execute(
        "SELECT name, country, sector, industry, currency FROM company_info WHERE symbol = ?",
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
        "SELECT * FROM financial_metrics WHERE symbol = ? ORDER BY year",
        (symbol,),
    )
    columns = [desc[0] for desc in cursor.description]
    metrics_by_year = {}
    financial_extraction = []
    for row in cursor.fetchall():
        year = None
        m = {}
        for i, col in enumerate(columns):
            if col == "year":
                year = row[i]
            elif col not in ("symbol",):
                m[col] = row[i]
        if year is not None:
            metrics_by_year[str(year)] = m
            financial_extraction.append(_row_to_financial_extraction(symbol, row))

    conn.close()

    return {
        "company_info": company_info,
        "financial_extraction": financial_extraction,
        "metrics_by_year": metrics_by_year,
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

        cursor.execute("SELECT symbol, year FROM financial_metrics ORDER BY year")
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
    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return results
