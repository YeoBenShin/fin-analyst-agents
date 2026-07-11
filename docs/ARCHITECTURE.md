# Architecture
```
                    Orchestrator
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
 Financial Data Agent            Market Data Agent
        │                                   │
        └─────────────────┬─────────────────┘
                          │
                 Data Validation Agent
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
 Business Agent   Industry Agent   Competitor Agent
        │                 │                 │
        └─────────────────┬─────────────────┘
                          │
             Historical Analysis Agent
                          │
             Forecasting & Assumptions Agent
                          │
                 Valuation Agent
                          │
              Risk & Catalyst Agent
                          │
             Investment Thesis Agent
                          │
              Report Generation Agent
```
### Summary of Agent Skills & Structured Schemas

#### 1. Orchestrator Agent
* **Role**: Process controller and global state manager.
* **Deterministic Output**: Tracks active pipeline loops, records timestamps, and coordinates execution flags sequentially or in parallel based on validation conditions.
* **Key Fields**: `pipeline_status`, `completed_agents`, `execution_timestamps`.

#### 2. Financial Data Agent
* **Role**: Multi-year historical fundamental statement harvester.
* **Deterministic Output**: Automatically maps endpoints (Finnhub for fast prototyping; SEC EDGAR with custom `us-gaap:*` tags for production) into rigid structural tables spanning Income Statements, Balance Sheets, and Cash Flows over a 5–10 year lookback period.
* **Key Fields**: `raw_income_statement`, `raw_balance_sheet`, `raw_cash_flow`, `corporate_actions`.

#### 3. Market Data Agent
* **Role**: Real-time market indicator and derivative options extractor.
* **Deterministic Output**: Search for market sentiment via the internet and isolates structural options market indicators to evaluate current options flow metrics.
* **Key Fields**: `current_price`, `market_cap`, `options_insights` (`short_to_long_ratio`, `put_call_volume_ratio`).

#### 4. Data Validation Agent
* **Role**: Accounting identity sanity checker and uniform schema parser.
* **Deterministic Output**: Standardises line items across companies and enforces accounting rules, checking that $\text{Assets} = \text{Liabilities} + \text{Equity}$ and verifying that cash flows reconcile perfectly within an exact $\pm 0.01\%$ threshold.
* **Key Fields**: `validation_status`, `reconciliation_metrics`, `standardized_financials`.

#### 5. Historical Analysis Agent
* **Role**: Historical financial metric modeler.
* **Deterministic Output**: Quantifies historical trends over 3, 5, and 10 years, converting financial records into growth rates and margin histories.
* **Key Fields**: `growth_calculations` (3yr/5yr/10yr CAGRs for Revenue, EPS, FCF), `margin_trends`, `capital_efficiency_history` (ROIC/ROE tracker), `capital_allocation_mix_percentage`.

#### 6. Business Agent
* **Role**: Segment tracker and corporate guidance analyst.
* **Deterministic Output**: Splits enterprise financial figures into distinct corporate segments and geographies, and parses transcripts to extract explicit management target records. Also look into management structure and their guidance and plans for the near future. 
* **Key Fields**: `revenue_segmentation`, `geographic_segmentation`, `capital_allocation_actions`, `management_commentary_extracted` (numeric targets for growth, margins, guidance).

#### 7. Industry Agent
* **Role**: Macro-economic cycle and industry context modeler.
* **Deterministic Output**: Translates broader macro indicators into sector-specific lifecycle states and tracks structural headwinds or tailwinds.
* **Key Fields**: `lifecycle_stage`, `macro_economic_forecast`, `industry_headwinds`, `industry_tailwinds`.

#### 8. Competitor Agent
* **Role**: Peer group selector and quantitative/qualitative benchmarking analyst.
* **Deterministic Output**: Filters industry groups to identify the top 5 closest peers ranked by market capitalization. Runs direct comparative benchmarking across financials, multiples, growth dynamics, and competitive economic moats.
* **Key Fields**: `selected_peers`, `quantitative_matrix` (Financials, Valuation Multiples, Growth Rates, Operational Quality metrics for all 5 peers), `qualitative_moat_benchmarking` (Moat Type, Positioning, Capital Allocation Grades).

#### 9. Forecasting & Assumptions Agent
* **Role**: Multi-scenario assumption modeler.
* **Deterministic Output**: Synthesizes historical baselines, management guidance, and macro drivers to establish explicit forecast vectors across three distinct operational paths: **Bear, Base, and Bull cases**.
* **Key Fields**: `scenarios` (each detailing sequential lists for `revenue_growth_series`, `operating_margin_series`, `capex_percentage_of_revenue`, `working_capital_percentage_of_revenue`, alongside `terminal_growth_rate` and `wacc`).

#### 10. Valuation Agent
* **Role**: Mathematical valuation engine.
* **Deterministic Output**: Processes forecasting assumptions through multi-stage mathematical models, running Gordon Growth Discounted Cash Flows (DCF), Peer Multiple Valuations, and Asset-Based frameworks.
* **Key Fields**: `dcf_model_results` (per-case intrinsic values and upsides), `relative_valuation_results` (implied multiple prices), `asset_based_results` (Book Value, NAV), `blended_valuation_summary`.

#### 11. Risk & Catalyst Agent
* **Role**: Risk quantifier and catalyst tracker.
* **Deterministic Output**: Scores risks via explicit probability and impact matrices, defines critical structural failure conditions, and tracks upcoming events that could trigger valuation re-ratings.
* **Key Fields**: `risk_matrix` (`category`, `probability`, `impact_score`, `mitigation_strategy`, `evidence_source`), `critical_failure_points`, `key_investment_catalysts`.

#### 12. Investment Thesis Agent
* **Role**: Absolute strategic synthesizer.
* **Deterministic Output**: Computes the strict Margin of Safety, generates concise pros/cons, defines specific operational metrics to track in upcoming quarters, and assigns an absolute recommendation rating with an algorithmic confidence score.
* **Key Fields**: Matches your exact dashboard format: `executive_summary_dashboard` (`company`, `current_price`, `intrinsic_value`, `upside_percentage`, `rating`, `confidence_score_percentage`, `top_strengths`, `top_risks`, `catalysts`, `key_assumptions`, `margin_of_safety_percentage`) and `deep_dive_vectors` (`why_buy`, `why_not_buy`, `things_to_monitor_next_quarter`, `red_flags`).

#### 13. Report Generation Agent
* **Role**: Standardized output compiler.
* **Deterministic Output**: Formats global multi-agent states into human-readable Markdown templates and structured data files without altering underlying value fields.
* **Key Fields**: `file_type_generated`, `document_status`, `raw_markdown_string`.

---

### Core Technical Design Choices within `SKILL.md`

1. **No Conversational Prose**: Every agent produces strict object hierarchies, ensuring the outputs can be easily typed via frameworks like Pydantic or mapped directly to database schemas.
2. **Strict Financial Equations**: Includes specific mathematical instructions for calculating values like Discounted Cash Flows (DCF), Gordon Growth Terminal Values, margins, and the Margin of Safety.
3. **Data Verification Loops**: The **Data Validation Agent** serves as a guardrail, ensuring bad or unmapped API data from Finnhub or SEC EDGAR is caught and flagged before it can affect down-stream valuation and forecasting models.