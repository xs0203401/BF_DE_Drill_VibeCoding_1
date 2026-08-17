"""Command-line entry point for the sales data pipeline."""

import argparse
from pathlib import Path

from src.pipeline import PipelineConfig, SalesPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the sales ETL pipeline.")
    parser.add_argument(
        "--no-load",
        action="store_true",
        help="Run extraction, validation, and transformation without PostgreSQL.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = SalesPipeline(
        PipelineConfig.from_environment(Path(__file__).resolve().parent)
    ).run(load_to_database=not args.no_load)
    print(
        "Pipeline complete: "
        f"extracted={summary.extracted_sales}, "
        f"valid={summary.valid_sales}, "
        f"rejected={summary.rejected_sales}, "
        f"loaded={summary.loaded_sales}"
    )


if __name__ == "__main__":
    main()
