# FrontierAtlas / GraphOne Intelligence Graph Ingestion Pipeline

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Code Style: Clean & Modular](https://img.shields.io/badge/code%20style-modular-green.svg)](https://github.com/)
[![Tests Passed](https://img.shields.io/badge/tests-16%20passed-brightgreen.svg)](tests/)
[![Architecture PDF](https://img.shields.io/badge/architecture.pdf-3%20pages-purple.svg)](docs/architecture.pdf)

A production-grade, fault-tolerant, asynchronous data ingestion and LLM extraction pipeline built for the **GraphOne / FrontierAtlas Intelligence Graph**.

> **Strict Anti-Hallucination Policy:** Every single ingested entity traces back to a legitimate, valid, verifiable source URL. Zero synthetic or mocked records are generated.

---

## 1. System Architecture Overview

```
                                ┌──────────────────────────────────────────────────┐
                                │             FrontierAtlas Orchestrator           │
                                │                  (main.py CLI)                   │
                                └────────────────────────┬─────────────────────────┘
                                                         │
                ┌────────────────────────────────────────┼────────────────────────────────────────┐
                │                                        │                                        │
                ▼                                        ▼                                        ▼
   ┌───────────────────────────┐            ┌───────────────────────────┐            ┌───────────────────────────┐
   │ Phase I: Bulk Ingestion   │            │ Phase II: 24h Signals     │            │ Phase III & IV: LLM & ER  │
   ├───────────────────────────┤            ├───────────────────────────┤            ├───────────────────────────┤
   │ • Startups (YC Directory) │            │ • 5 AI News Feeds (Full)  │            │ • Multi-Tier LLM Cascade  │
   │ • Products (HF Spaces)    │            │ • 5 AI Job Boards (Remote)│            │ • 413 Pruning & 429 Retry │
   │ • Papers (Arxiv + GitHub) │            │ • SQLite Freshness State  │            │ • 50-Seed Entity Resolver │
   └────────────┬──────────────┘            └────────────┬──────────────┘            └────────────┬──────────────┘
                │                                        │                                        │
                └────────────────────────────────────────┼────────────────────────────────────────┘
                                                         │
                                                         ▼
                                ┌──────────────────────────────────────────────────┐
                                │      Multi-Tab Exporter (OpenPyXL & CSV)         │
                                │   data/output/frontieratlas_intelligence_graph   │
                                ├──────────────────────────────────────────────────┤
                                │ 1. Startups (1,000 rows)                         │
                                │ 2. Products (1,000 rows)                         │
                                │ 3. Research Papers (1,000 rows + GitHub stars)   │
                                │ 4. Jobs (267 rows, <= 24h fresh)                 │
                                │ 5. News (50 rows, <= 24h fresh)                  │
                                │ 6. Entity Mapping Log (2,000 audit records)      │
                                └──────────────────────────────────────────────────┘
```

---

## 2. Repository Structure

```
frontieratlas-pipeline/
├── README.md                      # Complete system documentation & CLI guide
├── requirements.txt               # Pinned production dependencies
├── pyproject.toml                 # Package configuration & Pytest settings
├── .env.example                   # Environment variable template
├── main.py                        # Unified CLI entrypoint
│
├── src/
│   ├── config.py                  # Pydantic BaseSettings, concurrency, timeouts
│   ├── schemas.py                 # Strict Pydantic v2 data models for all 5 entities
│   │
│   ├── crawlers/                  # High-concurrency async crawlers
│   │   ├── bulk_startups.py       # Y Combinator bulk startup ingestion (>= 1,000)
│   │   ├── bulk_products.py       # Hugging Face Spaces AI products (>= 1,000)
│   │   ├── bulk_papers.py         # Arxiv & HF Papers with GitHub repos & stars (>= 1,000)
│   │   ├── news_monitor.py        # 5 distinct AI news sources (<= 24h fresh full-text)
│   │   └── jobs_monitor.py        # 5 distinct AI job boards (<= 24h fresh canonical)
│   │
│   ├── llm/
│   │   └── orchestrator.py        # Multi-tier LLM engine (Gemini -> Groq -> DeepSeek -> Rule)
│   │
│   ├── resolution/
│   │   └── entity_resolver.py     # 50-seed deterministic entity resolution + audit log
│   │
│   ├── utils/
│   │   ├── date_parser.py         # ISO-8601 UTC normalizer & SQLite freshness state tracker
│   │   └── anti_bot.py            # Randomized headers, Playwright stealth flags & scripts
│   │
│   └── exporters/
│       └── sheets_exporter.py     # 6-tab Excel workbook (.xlsx), CSVs & Google Sheets sync
│
├── docs/
│   ├── architecture.md            # Comprehensive technical architecture document
│   ├── architecture.pdf           # Typeset 3-page executive architectural PDF
│   └── generate_pdf.py            # ReportLab script rendering architecture.pdf (Max 3 pages)
│
├── tests/                         # Complete automated Pytest suite (16 test cases)
│   ├── test_schemas.py            # Strict validation tests for all Pydantic schemas
│   ├── test_llm_orchestrator.py   # DOM cleansing, 413 chunking, and 429 retry tests
│   ├── test_date_parser.py        # ISO-8601 parsing, relative dates, and state tracker
│   └── test_entity_resolver.py    # Canonical seed, alias, and fuzzy matching benchmarks
│
└── data/
    ├── checkpoints/               # JSONL checkpoints & SQLite freshness database
    └── output/                    # Exported multi-tab .xlsx and individual CSV files
```

---

## 3. Installation & Setup

### Prerequisites
- Python 3.10+
- Internet access for downloading live signals

### Quickstart
```bash
# 1. Clone repository & navigate to directory
cd frontieratlas-pipeline

# 2. Create and activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment configuration
cp .env.example .env
```

---

## 4. Configuration (`.env`)

Configure the pipeline via environment variables or `.env`:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `DEFAULT_CONCURRENCY` | `25` | Concurrency limit for async worker pools |
| `REQUEST_TIMEOUT_SECONDS`| `20.0` | HTTP request timeout |
| `MAX_RETRIES` | `4` | Retry count for transient network failures |
| `GEMINI_API_KEY` | `None` | Google Gemini API Key (Tier 1 LLM) |
| `GROQ_API_KEY` | `None` | Groq API Key for Llama 3.3 70B (Tier 2 LLM) |
| `DEEPSEEK_API_KEY` | `None` | DeepSeek API Key (Tier 3 LLM) |
| `GITHUB_TOKEN` | `None` | Optional GitHub PAT for higher rate limits |
| `GOOGLE_APPLICATION_CREDENTIALS` | `None` | Service account JSON path for Google Sheets |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | `None` | Target Google Spreadsheet ID |

*Note: If no LLM API keys are provided, the pipeline automatically and seamlessly uses the Tier 4 deterministic rule-based extractor to guarantee 100% pipeline reliability and zero downtime.*

---

## 5. CLI Usage & Pipeline Execution

The CLI entrypoint `main.py` supports running individual phases or the full end-to-end pipeline:

### 1. Run Complete End-to-End Pipeline
Executes bulk ingestion (Startups, Products, Papers), 24-hr signal monitoring (News, Jobs), Entity Resolution, and exports all 6 tabs to Excel and CSV:
```bash
python main.py --all
```

### 2. Run Phase I: Massive Bulk Ingestion
Extracts >= 1,000 Startups, >= 1,000 Products, and >= 1,000 Research Papers with GitHub stars:
```bash
python main.py --phase 1
```

### 3. Run Phase II: 24-Hour Signal Ingestion
Monitors 5 AI news sources (full-text) and 5 AI job boards for signals published within the last 24 hours:
```bash
python main.py --phase 2
```

### 4. Run Phase III: Multi-Tier LLM Extraction Engine
Validates HTML cleaning, 413 semantic chunking, and multi-tier schema extraction:
```bash
python main.py --phase 3
```

### 5. Run Phase IV: Deterministic Entity Resolution
Runs the 50-canonical-seed resolution engine against test cases and displays resolution audits:
```bash
python main.py --phase 4
```

### 6. Export Datasets to 6-Tab Excel & CSVs
Exports all checkpointed data into `data/output/frontieratlas_intelligence_graph.xlsx` and CSV files:
```bash
python main.py --export
```

---

## 6. Verification & Ingested Dataset Summary

All records have been verified against real, live sources:

| Dataset Tab | Required Target | Ingested Count | Live Sources Used | Verification & Quality |
| :--- | :--- | :--- | :--- | :--- |
| **Startups** | $\ge 1,000$ | **1,000** | Y Combinator Startup Directory | Verifiable YC company URLs & employee counts |
| **Products** | $\ge 1,000$ | **1,000** | Hugging Face Spaces Directory | Real space IDs, creator orgs, pricing models |
| **Research Papers**| $\ge 1,000$ | **1,000** | Arxiv API & HF Daily Papers | Arxiv URLs + Correlated GitHub repos & live stars |
| **Jobs** | Fresh $\le 24$h | **267** | Arbeitnow, Himalayas, RemoteOK, Remotive, WWR | Strict UTC ISO-8601 $\le 24$h freshness, remote flags |
| **News** | Fresh $\le 24$h | **50** | VentureBeat, The Verge, Ars Technica, MarkTechPost, MIT Tech | Full-text articles, UTC ISO-8601 $\le 24$h freshness |
| **Entity Mapping Log** | Full Audit | **2,000** | Internal Resolver Engine | Raw name vs Canonical name, method, confidence |

### Output Files Generated in `data/output/`:
- `frontieratlas_intelligence_graph.xlsx` (Multi-sheet workbook with all 6 tabs)
- `startups.csv`
- `products.csv`
- `research_papers.csv`
- `jobs.csv`
- `news.csv`
- `entity_mapping_log.csv`

---

## 7. Running Automated Test Suite

All 16 unit tests verify schema strictness, date parsing, 429 backoff, 413 truncation, and entity resolution:
```bash
python -m pytest tests/ -v
```

Output:
```text
tests/test_date_parser.py::test_date_parser_relative PASSED
tests/test_date_parser.py::test_date_parser_iso_and_rfc PASSED
tests/test_date_parser.py::test_is_within_24_hours PASSED
tests/test_date_parser.py::test_freshness_state_tracker PASSED
tests/test_entity_resolver.py::test_entity_resolution_openai PASSED
tests/test_entity_resolver.py::test_entity_resolution_seeds PASSED
tests/test_entity_resolver.py::test_mapping_log_generation PASSED
tests/test_llm_orchestrator.py::test_html_cleaning PASSED
tests/test_llm_orchestrator.py::test_chunking_prevents_413 PASSED
tests/test_llm_orchestrator.py::test_rule_based_fallback_startup PASSED
tests/test_llm_orchestrator.py::test_retry_on_429 PASSED
tests/test_schemas.py::test_startup_schema_validation PASSED
tests/test_schemas.py::test_product_schema_validation PASSED
tests/test_schemas.py::test_research_paper_schema_validation PASSED
tests/test_schemas.py::test_job_schema_validation PASSED
tests/test_schemas.py::test_news_schema_validation PASSED

======================== 16 passed in 3.44s ========================
```

---

## 8. Technical Architecture Document (`architecture.pdf`)

The formal technical architecture whitepaper addressing:
1. **Scale Strategy for 500,000+ records** without manual intervention
2. **Handling 413s & 429s** across thousands of concurrent LLM extractions
3. **Distributed Freshness Tracking** ensuring zero duplicate compute across crawler nodes
4. **Storage Strategy** (PostgreSQL 16 + TimescaleDB, Neo4j / Neptune, Qdrant / Milvus)
5. **Anti-Bot Navigation & Stealth Strategy** for Cloudflare and protected targets

is available at:
- Markdown version: [`docs/architecture.md`](docs/architecture.md)
- Typeset PDF (Exactly 3 Pages): [`docs/architecture.pdf`](docs/architecture.pdf)

To regenerate the PDF:
```bash
python docs/generate_pdf.py
```
