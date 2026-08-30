# Steam Store BI Lakehouse

End-to-end BI project: raw Kaggle data → Medallion Lakehouse (Databricks) → Power BI dashboard.
Built as a portfolio project targeting an **Administrative BI Assistant** role, using the exact
stack required: Python, SQL, Databricks (Community Edition), PySpark/Delta Lake basics, Power BI.

## Business Problem

> How can a digital game store understand market trends, pricing strategies, and platform
> performance to optimize its catalog and marketing?

## Architecture

```
Kaggle CSV → Bronze (raw landing) → Silver (cleaned/normalized) → Gold (aggregated) → Power BI
```

*(diagram: `docs/architecture_diagram.png` — TODO, add after Phase 2)*

| Layer  | Tool           | Purpose                                                        |
|--------|----------------|-----------------------------------------------------------------|
| Bronze | Databricks / Delta | Raw, unmodified, auditable landing zone                    |
| Silver | PySpark / SQL  | Cleaned, typed, normalized (genres/categories exploded)         |
| Gold   | SQL views/tables | Business-ready aggregates for BI                              |
| BI     | Power BI       | 3-page dashboard, connected via JDBC/ODBC                       |

## Repo Structure

See [`docs/`](docs/) for the full data dictionary and profiling notes. Key folders:

- `src/` — Python extract/utility scripts
- `notebooks/` — exploratory profiling
- `databricks/` — Bronze/Silver/Gold notebook source (PySpark + SQL)
- `sql/` — Gold layer view definitions
- `powerbi/` — `.pbix` file + `dax_measures.md` (DAX documented as text for version control)
- `docs/` — data dictionary, profiling report, architecture diagram, dashboard screenshots

## Dataset

[Steam Store Games](https://www.kaggle.com/datasets/nikdavis/steam-store-games) (Kaggle, ~27K games).
Only `steam.csv` is used — see `docs/profiling_report.md` for why.

## Dashboard Pages

1. **Market Overview** — total games, avg price, genre distribution
2. **Pricing & Reviews** — price vs. review correlation, free-to-play split, price tiers
3. **Temporal Trends** — releases by year, platform evolution, developer market share

*(screenshots: TODO, add after Phase 4)*

## Project Status

| Phase                                       | Status         |
|----------------------------------------------|----------------|
| 1. Python ETL & Profiling                    | ✅ Done        |
| 2. Databricks Medallion Setup                 | ⬜ Not started |
| 3. SQL Analytics & Gold Tables                | ⬜ Not started |
| 4. Power BI Modeling & DAX                    | ⬜ Not started |
| 5. Publish & Documentation                    | ⬜ Not started |

## How to Run

```bash
pip install -r requirements.txt
python src/extract/download_kaggle.py
```

See `docs/profiling_report.md` for the data quality findings that shaped the Silver layer design.