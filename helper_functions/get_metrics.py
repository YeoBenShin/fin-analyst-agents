from dotenv import load_dotenv
import finnhub
import os
import sys

def get_finnhub_client(env_path: str = None) -> finnhub.Client:
    """
    Initializes and returns the Finnhub API client using the API key defined
    in the environment variables.
    """
    # Load .env file. If env_path is not specified, it will look up the directory tree.
    if env_path:
        load_dotenv(dotenv_path=env_path)
    else:
        # Default fallback to parent directories where .env might be
        load_dotenv()
        
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise ValueError("FINNHUB_API_KEY is not defined in the environment variables.")
    
    return finnhub.Client(api_key=api_key)

def extract_company_data(symbol: str, env_path: str = None) -> dict:
    """
    Extracts all raw company information from Finnhub endpoints:
    - Company profile (sector, country, industry, shares outstanding)
    - Quote (current stock price)
    - Reported financials (annual SEC filings - BS, IC, CF)
    - Basic financials (valuation metrics, margins, etc.)
    """
    client = get_finnhub_client(env_path)
    symbol = symbol.upper()
    
    # 1. Fetch Company Profile (contains country, industry, name, shares outstanding)
    try:
        profile = client.company_profile2(symbol=symbol)
    except Exception as e:
        profile = {"error": str(e)}
        
    # 2. Fetch Current Price Quote
    try:
        quote = client.quote(symbol=symbol)
    except Exception as e:
        quote = {"error": str(e)}
        
    # 3. Fetch Reported Financials (as filed to SEC)
    try:
        reported_financials = client.financials_reported(symbol=symbol, freq="annual")
    except Exception as e:
        reported_financials = {"error": str(e), "data": []}
        
    # 4. Fetch Basic Financials (fallback metrics and series data)
    try:
        basic_financials = client.company_basic_financials(symbol=symbol, metric="all")
    except Exception as e:
        basic_financials = {"error": str(e)}
        
    return {
        "symbol": symbol,
        "profile": profile,
        "quote": quote,
        "reported_financials": reported_financials,
        "basic_financials": basic_financials
    }

def _get_concept_value(report_list: list, concepts: list) -> float:
    """
    Helper function to search for specific US GAAP concepts in reported filings,
    removing namespaces for robust matching.
    """
    if not report_list:
        return None
    for item in report_list:
        concept = item.get("concept", "")
        # Remove namespace (e.g. 'us-gaap_')
        clean_concept = concept.split("_")[-1] if "_" in concept else concept
        for target in concepts:
            clean_target = target.split("_")[-1] if "_" in target else target
            if clean_concept.lower() == clean_target.lower():
                return item.get("value")
    return None

def compute_fao_metrics(extracted_data: dict) -> dict:
    """
    Computes financial metrics from extracted data:
    - Price to Earnings (P/E)
    - Price to Book Value (P/B)
    - EBITDA Margins
    - Income Growth Rates (YoY)
    - Current Ratios
    - Dividend details (payments, dividend per share, yield)
    
    Includes a fallback mechanism to Finnhub's pre-calculated basic_financials
    if reported filings are unavailable or missing required data.
    """
    symbol = extracted_data.get("symbol")
    profile = extracted_data.get("profile", {})
    quote = extracted_data.get("quote", {})
    reported = extracted_data.get("reported_financials", {})
    basic = extracted_data.get("basic_financials", {})
    
    # 1. Company Information
    # In company_profile2, 'finnhubIndustry' represents sector/industry classification
    company_info = {
        "symbol": symbol,
        "name": profile.get("name"),
        "country": profile.get("country"),
        "sector": profile.get("finnhubIndustry"),
        "industry": profile.get("finnhubIndustry"),
        "currency": profile.get("currency")
    }
    
    shares_outstanding = profile.get("shareOutstanding")
    current_price = quote.get("c")
    filings = reported.get("data", [])
    
    metrics_by_year = {}
    
    # Case A: We have SEC reported filings data
    if isinstance(filings, list) and len(filings) > 0:
        # Sort by year ascending to compute YoY growth rates
        sorted_filings = sorted(filings, key=lambda x: x.get("year", 0))
        
        intermediate_results = []
        for filing in sorted_filings:
            year = filing.get("year")
            form = filing.get("form")
            report = filing.get("report", {})
            
            bs = report.get("bs", [])
            ic = report.get("ic", [])
            cf = report.get("cf", [])
            
            # Extract raw metrics from statements
            revenue = _get_concept_value(ic, [
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "SalesRevenueNet",
                "Revenues",
                "SalesRevenueGoodsNet"
            ])
            
            net_income = _get_concept_value(ic, [
                "NetIncomeLoss",
                "NetIncomeLossAvailableToCommonStockholdersBasic"
            ])
            
            operating_income = _get_concept_value(ic, [
                "OperatingIncomeLoss",
                "OperatingLoss"
            ])
            
            depreciation_amortization = _get_concept_value(cf, [
                "DepreciationDepletionAndAmortization",
                "DepreciationAndAmortization",
                "Depreciation",
                "AmortizationOfIntangibleAssets"
            ])
            
            total_assets = _get_concept_value(bs, ["Assets"])
            total_liabilities = _get_concept_value(bs, ["Liabilities"])
            current_assets = _get_concept_value(bs, ["AssetsCurrent"])
            current_liabilities = _get_concept_value(bs, ["LiabilitiesCurrent"])
            
            equity = _get_concept_value(bs, [
                "StockholdersEquity",
                "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"
            ])
            
            dividends_paid = _get_concept_value(cf, [
                "PaymentsOfDividends",
                "PaymentsOfDividendsCommonStock",
                "Dividends"
            ])
            
            # Calculate computed metrics
            ebitda = None
            if operating_income is not None:
                ebitda = operating_income + (depreciation_amortization or 0)
                
            ebitda_margin = None
            if ebitda is not None and revenue:
                ebitda_margin = ebitda / revenue
                
            current_ratio = None
            if current_assets is not None and current_liabilities:
                current_ratio = current_assets / current_liabilities
                
            book_value = equity
            if book_value is None and total_assets is not None and total_liabilities is not None:
                book_value = total_assets - total_liabilities
                
            intermediate_results.append({
                "year": year,
                "form": form,
                "revenue": revenue,
                "net_income": net_income,
                "operating_income": operating_income,
                "ebitda": ebitda,
                "ebitda_margin": ebitda_margin,
                "current_ratio": current_ratio,
                "book_value": book_value,
                "dividends_paid": dividends_paid
            })
            
        # Compute YoY metrics & price ratios
        for i, res in enumerate(intermediate_results):
            year = res["year"]
            
            income_growth_rate = None
            revenue_growth_rate = None
            if i > 0:
                prev_ni = intermediate_results[i-1]["net_income"]
                prev_rev = intermediate_results[i-1]["revenue"]
                if prev_ni and res["net_income"] is not None:
                    income_growth_rate = (res["net_income"] - prev_ni) / abs(prev_ni)
                if prev_rev and res["revenue"] is not None:
                    revenue_growth_rate = (res["revenue"] - prev_rev) / abs(prev_rev)
                    
            pe_ratio = None
            if current_price and shares_outstanding and res["net_income"]:
                market_cap = current_price * (shares_outstanding * 1_000_000)
                pe_ratio = market_cap / res["net_income"]
                
            pb_ratio = None
            if current_price and shares_outstanding and res["book_value"]:
                market_cap = current_price * (shares_outstanding * 1_000_000)
                pb_ratio = market_cap / res["book_value"]
                
            dividend_per_share = None
            dividend_yield = None
            if res["dividends_paid"] is not None and shares_outstanding:
                div_paid_positive = abs(res["dividends_paid"])
                dividend_per_share = div_paid_positive / (shares_outstanding * 1_000_000)
                if current_price:
                    dividend_yield = dividend_per_share / current_price
                    
            metrics_by_year[str(year)] = {
                "source": "reported_financials",
                "revenue": res["revenue"],
                "net_income": res["net_income"],
                "operating_income": res["operating_income"],
                "ebitda": res["ebitda"],
                "ebitda_margin": res["ebitda_margin"],
                "current_ratio": res["current_ratio"],
                "book_value": res["book_value"],
                "dividends_paid": res["dividends_paid"],
                "dividend_per_share": dividend_per_share,
                "dividend_yield": dividend_yield,
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "income_growth_rate": income_growth_rate,
                "revenue_growth_rate": revenue_growth_rate
            }
            
    # Case B: Fallback to basic financials series data (if reported is empty/unsupported)
    if not metrics_by_year and "series" in basic:
        annual_series = basic["series"].get("annual", {})
        
        # Collect all years represented in basic financials
        years = set()
        for series_key, series_list in annual_series.items():
            for item in series_list:
                period = item.get("period")
                if period:
                    # Period is usually 'YYYY-MM-DD' or 'YYYY'
                    year_str = period.split("-")[0]
                    years.add(year_str)
                    
        sorted_years = sorted(list(years))
        
        # Fetch series lists into dictionaries for quick lookup by year
        series_lookups = {}
        for key, series_list in annual_series.items():
            lookup = {}
            for item in series_list:
                period = item.get("period", "")
                year_str = period.split("-")[0]
                lookup[year_str] = item.get("v")
            series_lookups[key] = lookup
            
        for i, year in enumerate(sorted_years):
            pe = series_lookups.get("pe", {}).get(year)
            pb = series_lookups.get("pb", {}).get(year)
            current_ratio = series_lookups.get("currentRatio", {}).get(year)
            ebitda = series_lookups.get("ebitda", {}).get(year)
            book_value = series_lookups.get("bookValue", {}).get(year)
            
            # Growth rates from series
            income_growth = None
            if i > 0:
                prev_eps = series_lookups.get("eps", {}).get(sorted_years[i-1])
                curr_eps = series_lookups.get("eps", {}).get(year)
                if prev_eps and curr_eps is not None:
                    income_growth = (curr_eps - prev_eps) / abs(prev_eps)
                    
            payout_ratio = series_lookups.get("payoutRatio", {}).get(year)
            eps = series_lookups.get("eps", {}).get(year)
            
            dividend_per_share = None
            dividend_yield = None
            if eps is not None and payout_ratio is not None:
                # payout ratio is typically expressed as % or ratio
                ratio = payout_ratio / 100.0 if payout_ratio > 1.0 else payout_ratio
                dividend_per_share = eps * ratio
                if current_price:
                    dividend_yield = dividend_per_share / current_price
                    
            metrics_by_year[year] = {
                "source": "basic_financials_series",
                "revenue": None, # Basic financials series doesn't always have revenue
                "net_income": None,
                "operating_income": None,
                "ebitda": ebitda,
                "ebitda_margin": None,
                "current_ratio": current_ratio,
                "book_value": book_value,
                "dividends_paid": None,
                "dividend_per_share": dividend_per_share,
                "dividend_yield": dividend_yield,
                "pe_ratio": pe,
                "pb_ratio": pb,
                "income_growth_rate": income_growth,
                "revenue_growth_rate": None
            }
            
    # TTM or Single Metric Fallback (if no series data exists)
    if not metrics_by_year and "metric" in basic:
        m = basic["metric"]
        metrics_by_year["TTM"] = {
            "source": "basic_financials_metrics",
            "revenue": None,
            "net_income": None,
            "operating_income": None,
            "ebitda": None,
            "ebitda_margin": m.get("ebitdaMarginTTM"),
            "current_ratio": m.get("currentRatioAnnual"),
            "book_value": m.get("tbvPerShareAnnual"),
            "dividends_paid": None,
            "dividend_per_share": m.get("dividendsPerShareTTM"),
            "dividend_yield": m.get("dividendYieldIndicatedAnnual"),
            "pe_ratio": m.get("peTTM") or m.get("peAnnual"),
            "pb_ratio": m.get("pbAnnual"),
            "income_growth_rate": m.get("epsGrowth3Y") or m.get("epsGrowth5Y"),
            "revenue_growth_rate": m.get("revenueGrowth3Y") or m.get("revenueGrowth5Y")
        }
        
    return {
        "company_info": company_info,
        "metrics_by_year": metrics_by_year
    }

def fao_pipeline(symbol: str, env_path: str = None) -> dict:
    """
    Financial Analysis Orchestration Pipeline.
    Given a stock symbol, extracts its profile and financials, 
    and computes the key financial ratios.
    """
    data = extract_company_data(symbol, env_path)
    metrics = compute_fao_metrics(data)
    return metrics
