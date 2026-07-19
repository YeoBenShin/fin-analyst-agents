from dotenv import load_dotenv
import finnhub
import os

from db_helper import save_to_db, load_from_db

def _get_finnhub_client(env_path: str = None) -> finnhub.Client:
    """
    Initializes and returns the Finnhub API client using the API key defined
    in the environment variables.
    """
    if env_path:
        load_dotenv(dotenv_path=env_path)
    else:
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
    client = _get_finnhub_client(env_path)
    symbol = symbol.upper()

    try:
        profile = client.company_profile2(symbol=symbol)
    except Exception as e:
        profile = {"error": str(e)}

    try:
        reported_financials = client.financials_reported(symbol=symbol, freq="annual")
    except Exception as e:
        reported_financials = {"error": str(e), "data": []}

    try:
        basic_financials = client.company_basic_financials(symbol=symbol, metric="all")
    except Exception as e:
        basic_financials = {"error": str(e)}

    return {
        "symbol": symbol,
        "profile": profile,
        "reported_financials": reported_financials,
        "basic_financials": basic_financials,
    }

def clean_concept(concept: str) -> str:
    """
    Cleans the concept string by removing the 'us-gaap_' prefix if present.
    """
    if concept.startswith("us-gaap_"):
        return concept[len("us-gaap_"):]
    return concept

def _process_reported_financials(report_list: list):
    """
    Converts a list of reported financials into a dictionary keyed by the concept.
    + Returns a set of unique concepts found in the report_list to identify unique financial metrics.
    """
    if not report_list:
        return None

    dict_to_return = {}
    set_of_concepts = set() 
    for item in report_list:
        concept = clean_concept(item.get("concept"))
        item["concept"] = concept  # Update the concept in the item
        set_of_concepts.add(concept)
        dict_to_return[concept] = item

    return dict_to_return, set_of_concepts

def _get_value(report_dict: dict, values_to_find: list, concept_set: set = None):
    """
    Helper function to get the value of a concept from a report dict
    User can provide a list of possible concept names to find the value for.
    """
    if not report_dict:
        return None
    for value in values_to_find:
        if value in report_dict: 
            concept_set.discard(value) if concept_set else None # Remove the found concept from the set
            return report_dict[value].get("value", None)
    return None

def _extract_yearly_metrics(
    report: dict | None = None,
) -> dict:
    """
    Extracts key financial metrics from a single fiscal year's report.
    (input is from Finnhub's reported financials annual section)
    """
    report = report or {}

    # Process the reported financials into dictionaries for easier access
    bs, bs_concepts = _process_reported_financials(report.get("bs", []))
    ic, ic_concepts = _process_reported_financials(report.get("ic", []))
    cf, cf_concepts = _process_reported_financials(report.get("cf", []))

    # Extract key metrics from the balance sheet, income statement, and cash flow statement
    bs_metrics = {}
    ic_metrics = {}
    cf_metrics = {}

    # Balance Sheet Metrics
    bs_metrics["accounts_payable"] = _get_value(bs, ["AccountsPayableCurrent"], concept_set=bs_concepts)
    bs_metrics["accounts_receivable"] = _get_value(bs, ["AccountsReceivableNetCurrent"], concept_set=bs_concepts)
    bs_metrics["total_assets"] = _get_value(bs, ["Assets"], concept_set=bs_concepts)
    bs_metrics["accumulated_other_comprehensive_income"] = _get_value(bs, ["AccumulatedOtherComprehensiveIncomeLossNetOfTax"], concept_set=bs_concepts)
    bs_metrics["current_assets"] = _get_value(bs, ["AssetsCurrent"], concept_set=bs_concepts)
    bs_metrics["non-current_assets"] = _get_value(bs, ["AssetsNoncurrent"], concept_set=bs_concepts)
    bs_metrics["marketable_securities_short_term"] = _get_value(bs, ["AvailableForSaleSecuritiesCurrent"], concept_set=bs_concepts)
    bs_metrics["marketable_securities_long_term"] = _get_value(bs, ["AvailableForSaleSecuritiesNoncurrent"], concept_set=bs_concepts)
    bs_metrics["cash_and_cash_equivalents"] = _get_value(bs, ["CashAndCashEquivalentsAtCarryingValue"], concept_set=bs_concepts)
    bs_metrics["commercial_paper"] = _get_value(bs, ["CommercialPaper"], concept_set=bs_concepts)
    bs_metrics["deferred_revenue"] = _get_value(bs, ["DeferredRevenueCurrent"], concept_set=bs_concepts)
    bs_metrics["deferred_revenue_noncurrent"] = _get_value(bs, ["DeferredRevenueNoncurrent"], concept_set=bs_concepts)
    bs_metrics["inventory"] = _get_value(bs, ["InventoryNet"], concept_set=bs_concepts)
    bs_metrics["liabilities_current"] = _get_value(bs, ["LiabilitiesCurrent"], concept_set=bs_concepts)
    bs_metrics["liabilities_noncurrent"] = _get_value(bs, ["LiabilitiesNoncurrent"], concept_set=bs_concepts)
    bs_metrics["liabilities_total"] = _get_value(bs, ["Liabilities"], concept_set=bs_concepts)
    bs_metrics["long_term_debt_current"] = _get_value(bs, ["LongTermDebtCurrent"], concept_set=bs_concepts)
    bs_metrics["long_term_debt_noncurrent"] = _get_value(bs, ["LongTermDebtNoncurrent"], concept_set=bs_concepts)
    bs_metrics["nontrade_receivables_current"] = _get_value(bs, ["NontradeReceivablesCurrent"], concept_set=bs_concepts)
    bs_metrics["other_current_assets"] = _get_value(bs, ["OtherAssetsCurrent"], concept_set=bs_concepts)
    bs_metrics["other_noncurrent_assets"] = _get_value(bs, ["OtherAssetsNoncurrent"], concept_set=bs_concepts)
    bs_metrics["other_current_liabilities"] = _get_value(bs, ["OtherLiabilitiesCurrent"], concept_set=bs_concepts)
    bs_metrics["other_noncurrent_liabilities"] = _get_value(bs, ["OtherLiabilitiesNoncurrent"], concept_set=bs_concepts)
    bs_metrics["propertyPlantAndEquipmentNet"] = _get_value(bs, ["PropertyPlantAndEquipmentNet"], concept_set=bs_concepts)
    bs_metrics["retained_earnings"] = _get_value(bs, ["RetainedEarningsAccumulatedDeficit"], concept_set=bs_concepts)
    bs_metrics["stockholders_equity"] = _get_value(bs, ["StockholdersEquity"], concept_set=bs_concepts)

    # Income Statement Metrics
    ic_metrics["revenue"] = _get_value(ic, ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"], concept_set=ic_concepts)
    ic_metrics["cost_of_sales"] = _get_value(ic, ["CostOfGoodsAndServicesSold"], concept_set=ic_concepts)
    ic_metrics["gross_profit"] = _get_value(ic, ["GrossProfit"], concept_set=ic_concepts)
    ic_metrics["research_and_development"] = _get_value(ic, ["ResearchAndDevelopmentExpense"], concept_set=ic_concepts)
    ic_metrics["selling_general_admin"] = _get_value(ic, ["SellingGeneralAndAdministrativeExpense"], concept_set=ic_concepts)
    ic_metrics["operating_expenses"] = _get_value(ic, ["OperatingExpenses"], concept_set=ic_concepts)
    ic_metrics["operating_income"] = _get_value(ic, ["OperatingIncomeLoss"], concept_set=ic_concepts)
    ic_metrics["non_operating_income"] = _get_value(ic, ["NonoperatingIncomeExpense"], concept_set=ic_concepts)
    ic_metrics["pre_tax_income"] = _get_value(ic, ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"], concept_set=ic_concepts)
    ic_metrics["income_tax_expense"] = _get_value(ic, ["IncomeTaxExpenseBenefit"], concept_set=ic_concepts)
    ic_metrics["net_income"] = _get_value(ic, ["NetIncomeLoss"], concept_set=ic_concepts)
    ic_metrics["eps_basic"] = _get_value(ic, ["EarningsPerShareBasic"], concept_set=ic_concepts)
    ic_metrics["eps_diluted"] = _get_value(ic, ["EarningsPerShareDiluted"], concept_set=ic_concepts)
    ic_metrics["shares_basic"] = _get_value(ic, ["WeightedAverageNumberOfSharesOutstandingBasic"], concept_set=ic_concepts)
    ic_metrics["shares_diluted"] = _get_value(ic, ["WeightedAverageNumberOfDilutedSharesOutstanding"], concept_set=ic_concepts)
    ic_metrics["fx_adjustment"] = _get_value(ic, ["OtherComprehensiveIncomeLossForeignCurrencyTransactionAndTranslationAdjustmentNetOfTax"], concept_set=ic_concepts)

    # Cash Flow Statement Metrics
    cf_metrics["depreciation_amortization"] = _get_value(cf, ["DepreciationDepletionAndAmortization"], concept_set=cf_concepts)
    cf_metrics["share_based_compensation"] = _get_value(cf, ["ShareBasedCompensation"], concept_set=cf_concepts)
    cf_metrics["other_non_cash_expense"] = _get_value(cf, ["OtherNoncashIncomeExpense"], concept_set=cf_concepts)
    cf_metrics["accounts_receivable_change"] = _get_value(cf, ["IncreaseDecreaseInAccountsReceivable"], concept_set=cf_concepts)
    cf_metrics["nontrade_receivables_change"] = _get_value(cf, ["IncreaseDecreaseInOtherReceivables"], concept_set=cf_concepts)
    cf_metrics["inventory_change"] = _get_value(cf, ["IncreaseDecreaseInInventories"], concept_set=cf_concepts)
    cf_metrics["assets_change"] = _get_value(cf, ["IncreaseDecreaseInOtherOperatingAssets"], concept_set=cf_concepts)
    cf_metrics["accounts_payable_change"] = _get_value(cf, ["IncreaseDecreaseInAccountsPayable"], concept_set=cf_concepts)
    cf_metrics["liabilities_change"] = _get_value(cf, ["IncreaseDecreaseInOtherOperatingLiabilities"], concept_set=cf_concepts)
    cf_metrics["net_cash_from_operations"] = _get_value(cf, ["NetCashProvidedByUsedInOperatingActivities"], concept_set=cf_concepts)
    cf_metrics["marketable_securities_purchase"] = _get_value(cf, ["PaymentsToAcquireAvailableForSaleSecuritiesDebt"], concept_set=cf_concepts)
    cf_metrics["marketable_securities_maturity_proceeds"] = _get_value(cf, ["ProceedsFromMaturitiesPrepaymentsAndCallsOfAvailableForSaleSecurities"], concept_set=cf_concepts)
    cf_metrics["marketable_securities_sale"] = _get_value(cf, ["ProceedsFromSaleOfAvailableForSaleSecuritiesDebt"], concept_set=cf_concepts)
    cf_metrics["capital_expenditures"] = _get_value(cf, ["PaymentsToAcquirePropertyPlantAndEquipment"], concept_set=cf_concepts)
    cf_metrics["other_investing_activities"] = _get_value(cf, ["PaymentsForProceedsFromOtherInvestingActivities"], concept_set=cf_concepts)
    cf_metrics["net_cash_from_investing"] = _get_value(cf, ["NetCashProvidedByUsedInInvestingActivities"], concept_set=cf_concepts)
    cf_metrics["tax_withholding_for_share_based_comp"] = _get_value(cf, ["PaymentsRelatedToTaxWithholdingForShareBasedCompensation"], concept_set=cf_concepts)
    cf_metrics["dividends_paid"] = _get_value(cf, ["PaymentsOfDividends", "PaymentsOfDividendsCommonStock"], concept_set=cf_concepts)
    cf_metrics["repurchases_of_common_stock"] = _get_value(cf, ["PaymentsForRepurchaseOfCommonStock"], concept_set=cf_concepts)
    cf_metrics["proceeds_from_issuance_of_long_term_debt"] = _get_value(cf, ["ProceedsFromIssuanceOfLongTermDebt"], concept_set=cf_concepts)
    cf_metrics["repayments_of_long_term_debt"] = _get_value(cf, ["RepaymentsOfLongTermDebt"], concept_set=cf_concepts)
    cf_metrics["proceeds_from_repayments_of_commercial_paper"] = _get_value(cf, ["ProceedsFromRepaymentsOfCommercialPaper"], concept_set=cf_concepts)
    cf_metrics["proceeds_from_other_financing_activities"] = _get_value(cf, ["ProceedsFromOtherFinancingActivities"], concept_set=cf_concepts)
    cf_metrics["net_cash_from_financing"] = _get_value(cf, ["NetCashProvidedByUsedInFinancingActivities"], concept_set=cf_concepts)
    cf_metrics["net_change_in_cash"] = _get_value(cf, ["CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect", 
                                         "EffectOfExchangeRateOnCashAndCashEquivalents", "NetChangeInCashCashEquivalentsAndRestrictedCash"], concept_set=cf_concepts)
    cf_metrics["income_taxes_paid"] = _get_value(cf, ["IncomeTaxesPaidNet"], concept_set=cf_concepts)
    cf_metrics["interest_paid"] = _get_value(cf, ["InterestPaidNet"], concept_set=cf_concepts)

    # Settle the remaining concepts that were not extracted.
    for concept in bs_concepts:
        bs_metrics[concept] = bs.get(concept)
    for concept in ic_concepts:
        ic_metrics[concept] = ic.get(concept)
    for concept in cf_concepts:
        cf_metrics[concept] = cf.get(concept)
    
    return {
        "balance_sheet": bs_metrics,
        "income_statement": ic_metrics,
        "cash_flow_statement": cf_metrics
    }

def _extract_year(date: str) -> int:
    return int(date.split("-")[0])

def _sort_computed_annual_metrics(
    report: dict | None = None,
) -> dict:
    """
    Extracts computed financial metrics from the basic financials annual reports and groups them by fiscal year.
    (input is from Finnhub's basic financials annual section)
    """
    report = report or {}
    grouped = {}
    for metric_key, entries in report.items():
        for entry in entries:
            period = entry.get("period")
            value = entry.get("v")
            if not period or value is None:
                continue
            year = _extract_year(period)
            if year not in grouped:
                grouped[year] = {}
            if metric_key not in grouped[year]:
                grouped[year][metric_key] = value

    return dict(sorted(grouped.items()))


def process_metrics(extracted_data: dict) -> dict:
    """
    Processes financial metrics from extracted data and reshapes them into one
    JSON object per fiscal year.
    """
    symbol = extracted_data.get("symbol")
    profile = extracted_data.get("profile", {})
    raw_reported_financials = extracted_data.get("reported_financials", {}).get("data", []) 
    basic_financials = extracted_data.get("basic_financials", {})

    company_info = {
        "symbol": symbol,
        "name": profile.get("name"),
        "country": profile.get("country"),
        "sector": profile.get("finnhubIndustry"),
        "industry": profile.get("finnhubIndustry"),
        "currency": profile.get("currency"),
        "shares_outstanding": profile.get("shareOutstanding")
    }

    # Process each fiscal year's reported financials
    metrics_by_year = {}
    if isinstance(raw_reported_financials, list) and len(raw_reported_financials) > 0:
        sorted_filings = sorted(raw_reported_financials, key=lambda x: x.get("year", 0))
        
        for filing in sorted_filings:
            year = filing.get("year")
            report = filing.get("report", {})

            # call function, each report now is for each year
            yearly_metrics = _extract_yearly_metrics(report=report)
            yearly_metrics["year"] = year
            metrics_by_year[year] = yearly_metrics

    # Sort the computed annual metrics from the basic financials by fiscal year
    computed_metrics = _sort_computed_annual_metrics(basic_financials.get("series", {}).get("annual", {}))

    # Merge the computed metrics into the metrics_by_year for each fiscal year
    for year, computed in computed_metrics.items():
        if year in metrics_by_year:
            metrics_by_year[year].update(computed)
        else:
            metrics_by_year[year] = {"year": year, **computed}
    
    # merge the company info into the final output
    return {
        "company_info": company_info,
        "financial_extraction": [metrics_by_year[y] for y in sorted(metrics_by_year)]
    }


def fda_pipeline(symbol: str, env_path: str = None, db_path: str = None) -> dict:
    """
    Financial Analysis Orchestration Pipeline.
    Given a stock symbol, extracts its profile and financials,
    and computes the key financial ratios.
    Uses SQLite database as a cache layer for historical data queries.
    """
    if db_path is None:
        db_path = os.getenv("DB_PATH", "financial_data.db")

    cached_metrics = load_from_db(symbol, db_path)
    if cached_metrics is not None:
        return cached_metrics

    data = extract_company_data(symbol, env_path)
    metrics = process_metrics(data)

    save_to_db(metrics, db_path)

    return metrics
