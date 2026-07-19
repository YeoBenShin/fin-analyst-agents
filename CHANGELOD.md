# Rules
- When adding a new change, keep it concise and straight to the point. 
- Only add changes to `Summary of current changes`

# Summary of current changes 

## End-to-End Pipeline Test
- Added `test_process_metrics.py` in `.agents/skills/financial-data-agent/scripts/test/` to validate the full `process_metrics` pipeline using `finnhub_api_output.json`.
- Fixed type mismatch bug in `_extract_year()` (returned `str` instead of `int`), which prevented basic financials computed metrics from being merged into reported financials by year.
- Fixed "Cash Flow Statement Metrics" being incorrectly stored in `ic_metrics` (income statement dict) instead of `cf_metrics` (cash flow statement dict).
- Fixed `else` branch in computed metrics merging to include `year` key for years without reported financials.

## Annual Metrics Parser
- Created `parse_annual_metrics(data)` in `helper_functions/parse_annual_metrics.py` to flatten the `series.annual` Finnhub structure into `{year: {metric: value}}` format.
- Added unit tests in `helper_functions/test/test_parse_annual_metrics.py`.

## SQLite Caching for Financial Historical Data
- Added a SQLite caching layer to `fao_pipeline` in `helper_functions/get_metrics.py`.
- Stored retrieved financial records in `financial_data.db` under two tables: `company_info` and `financial_metrics`.
- Implemented database queries to check for existing records before performing API queries.
- Added comprehensive unit tests in `helper_functions/test/test_db_cache.py`.

## Custom Database Query and Analysis Function
- Created `query_database(query, db_path)` in `helper_functions/get_metrics.py` to allow querying/inspecting the database.
- Implemented a default summary analysis mode when `query` is omitted, returning schema metadata, company counts, metrics counts, and stored years for all companies.
- Added corresponding unit tests in `helper_functions/test/test_db_cache.py`.

## Modularized Database Implementation
- Extracted SQLite initialization, loading, saving, and querying code from `helper_functions/get_metrics.py` into a dedicated [helper_functions/db_helper.py](file:///Users/yeobe/SideProjects/Antigravity/fin-analyst-agents/helper_functions/db_helper.py) module.
- Modified `helper_functions/get_metrics.py` to import these helper functions and keep file modularized (single-responsibility principle).

# Summary of past changes