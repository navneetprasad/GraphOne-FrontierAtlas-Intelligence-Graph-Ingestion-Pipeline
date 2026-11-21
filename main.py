import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import config
from src.crawlers.bulk_startups import BulkStartupsCrawler
from src.crawlers.bulk_products import BulkProductsCrawler
from src.crawlers.bulk_papers import BulkPapersCrawler
from src.crawlers.news_monitor import NewsMonitorCrawler
from src.crawlers.jobs_monitor import JobsMonitorCrawler
from src.resolution.entity_resolver import entity_resolver
from src.llm.orchestrator import llm_orchestrator
from src.exporters.sheets_exporter import SheetsExporter
from src.schemas import StartupEntity

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("FrontierAtlas")

async def run_phase_1():
    """Phase I: Massive Bulk Ingestion (Startups >=1k, Products >=1k, Papers >=1k)."""
    logger.info("=== STARTING PHASE I: MASSIVE BULK INGESTION ===")
    startups_crawler = BulkStartupsCrawler(target_count=config.TARGET_STARTUPS_COUNT)
    products_crawler = BulkProductsCrawler(target_count=config.TARGET_PRODUCTS_COUNT)
    papers_crawler = BulkPapersCrawler(target_count=config.TARGET_PAPERS_COUNT)

    # Run in parallel or sequence
    startups = await startups_crawler.run()
    products = await products_crawler.run()
    papers = await papers_crawler.run()

    logger.info(
        "=== PHASE I COMPLETE ===\n"
        "  - Startups Extracted: %d\n"
        "  - Products Extracted: %d\n"
        "  - Research Papers Extracted: %d",
        len(startups), len(products), len(papers)
    )
    return startups, products, papers

async def run_phase_2():
    """Phase II: High-Fidelity Signal Ingestion (5 News Sources & 5 Job Boards <=24h)."""
    logger.info("=== STARTING PHASE II: HIGH-FIDELITY 24-HOUR SIGNAL INGESTION ===")
    news_crawler = NewsMonitorCrawler()
    jobs_crawler = JobsMonitorCrawler()

    news_items = await news_crawler.run()
    job_items = await jobs_crawler.run()

    logger.info(
        "=== PHASE II COMPLETE ===\n"
        "  - 24-hr News Extracted: %d\n"
        "  - 24-hr Jobs Extracted: %d",
        len(news_items), len(job_items)
    )
    return news_items, job_items

async def run_phase_3():
    """Phase III: Multi-Tier LLM Extraction Engine Verification."""
    logger.info("=== STARTING PHASE III: MULTI-TIER LLM EXTRACTION VERIFICATION ===")
    sample_text = (
        "<html><body><article><h1>Mistral AI</h1><p>Mistral AI is an AI lab based in Paris "
        "employing 80 research scientists and engineers building frontier open-weights models.</p></article></body></html>"
    )
    extracted = await llm_orchestrator.extract_structured_entity(
        raw_content=sample_text,
        entity_type="STARTUP",
        source_url="https://mistral.ai",
        source_name="Mistral Web",
        schema_class=StartupEntity
    )
    logger.info("LLM Extraction Result: %s", extracted.model_dump_json(indent=2))
    return extracted

def run_phase_4():
    """Phase IV: Deterministic Entity Resolution Benchmarking."""
    logger.info("=== STARTING PHASE IV: DETERMINISTIC ENTITY RESOLUTION BENCHMARK ===")
    test_cases = [
        ("OpenAI, Inc.", "https://example.com/1"),
        ("Open AI", "https://example.com/2"),
        ("openai llc", "https://example.com/3"),
        ("Anthropic PBC", "https://example.com/4"),
        ("HuggingFace", "https://example.com/5"),
        ("google brain", "https://example.com/6"),
        ("Perplexity AI Inc.", "https://example.com/7"),
        ("Databricks, Inc.", "https://example.com/8"),
        ("Scale AI, Inc.", "https://example.com/9"),
        ("Cursor AI", "https://example.com/10"),
    ]
    for raw, url in test_cases:
        res = entity_resolver.resolve(raw, url)
        logger.info("Resolved: '%s' -> '%s'", raw, res)

    logger.info("Entity Mapping Log contains %d recorded resolutions.", len(entity_resolver.get_mapping_log()))

async def run_export(startups, products, papers, jobs, news):
    """Export all datasets to 6-tab Excel, CSVs, and optional Google Sheets."""
    logger.info("=== EXPORTING 6-TAB INTELLIGENCE GRAPH DATASET ===")
    exporter = SheetsExporter()
    mappings = entity_resolver.get_mapping_log()

    excel_path = exporter.export_to_excel_and_csv(
        startups=startups,
        products=products,
        papers=papers,
        jobs=jobs,
        news=news,
        entity_mappings=mappings
    )
    logger.info("Export file generated: %s", excel_path)

    # Optional Google Sheets remote sync
    sheet_url = exporter.sync_to_google_sheets(excel_path)
    if sheet_url:
        logger.info("Public Google Sheets Link: %s", sheet_url)

    return excel_path

async def main():
    parser = argparse.ArgumentParser(description="GraphOne / FrontierAtlas Intelligence Ingestion Pipeline")
    parser.add_argument("--all", action="store_true", help="Run complete end-to-end pipeline and export")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4], help="Run a specific phase (1, 2, 3, or 4)")
    parser.add_argument("--export", action="store_true", help="Export existing checkpoint data to Excel and CSVs")
    args = parser.parse_args()

    if not any([args.all, args.phase, args.export]):
        parser.print_help()
        sys.exit(0)

    startups, products, papers = [], [], []
    jobs, news = [], []

    if args.phase == 1 or args.all:
        startups, products, papers = await run_phase_1()

    if args.phase == 2 or args.all:
        news, jobs = await run_phase_2()

    if args.phase == 3:
        await run_phase_3()

    if args.phase == 4:
        run_phase_4()

    if args.all or args.export:
        # If running export standalone, load from checkpoints
        if not startups and (config.CHECKPOINT_DIR / "startups.jsonl").exists():
            with open(config.CHECKPOINT_DIR / "startups.jsonl", "r", encoding="utf-8") as f:
                startups = [StartupEntity.model_validate_json(line) for line in f if line.strip()]
        if not products and (config.CHECKPOINT_DIR / "products.jsonl").exists():
            from src.schemas import ProductEntity
            with open(config.CHECKPOINT_DIR / "products.jsonl", "r", encoding="utf-8") as f:
                products = [ProductEntity.model_validate_json(line) for line in f if line.strip()]
        if not papers and (config.CHECKPOINT_DIR / "papers.jsonl").exists():
            from src.schemas import ResearchPaperEntity
            with open(config.CHECKPOINT_DIR / "papers.jsonl", "r", encoding="utf-8") as f:
                papers = [ResearchPaperEntity.model_validate_json(line) for line in f if line.strip()]
        if not jobs and (config.CHECKPOINT_DIR / "jobs.jsonl").exists():
            from src.schemas import JobEntity
            with open(config.CHECKPOINT_DIR / "jobs.jsonl", "r", encoding="utf-8") as f:
                jobs = [JobEntity.model_validate_json(line) for line in f if line.strip()]
        if not news and (config.CHECKPOINT_DIR / "news.jsonl").exists():
            from src.schemas import NewsEntity
            with open(config.CHECKPOINT_DIR / "news.jsonl", "r", encoding="utf-8") as f:
                news = [NewsEntity.model_validate_json(line) for line in f if line.strip()]

        await run_export(startups, products, papers, jobs, news)

if __name__ == "__main__":
    asyncio.run(main())
