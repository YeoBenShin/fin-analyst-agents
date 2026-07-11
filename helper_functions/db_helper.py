import sqlite3
import json


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
    for year, m in metrics.get("metrics_by_year", {}).items():
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
                m.get("source"),
                m.get("revenue"),
                m.get("net_income"),
                m.get("operating_income"),
                m.get("ebitda"),
                m.get("ebitda_margin"),
                m.get("current_ratio"),
                m.get("book_value"),
                m.get("dividends_paid"),
                m.get("dividend_per_share"),
                m.get("dividend_yield"),
                m.get("pe_ratio"),
                m.get("pb_ratio"),
                m.get("income_growth_rate"),
                m.get("revenue_growth_rate"),
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

    conn.close()

    return {
        "company_info": company_info,
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
