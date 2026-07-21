# Architecture
```
                    Orchestrator
                          │
                          │
                Financial Data Agent
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

### Core Technical Design Choices within `SKILL.md`

1. **No Conversational Prose**: Every agent produces strict object hierarchies, ensuring the outputs can be easily typed via frameworks like Pydantic or mapped directly to database schemas.
2. **Strict Financial Equations**: Includes specific mathematical instructions for calculating values like Discounted Cash Flows (DCF), Gordon Growth Terminal Values, margins, and the Margin of Safety.
3. **Data Verification Loops**: The **Data Validation Agent** serves as a guardrail, ensuring bad or unmapped API data from Finnhub or SEC EDGAR is caught and flagged before it can affect down-stream valuation and forecasting models.