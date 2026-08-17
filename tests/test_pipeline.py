from datetime import date
from decimal import Decimal
from pathlib import Path
from shutil import copytree

from src.extractors import CSVExtractor, JSONExtractor
from src.models import Customer, Product, ValidatedSalesRecord
from src.pipeline import PipelineConfig, SalesPipeline
from src.transformers import SalesDataTransformer
from src.validators import SalesDataValidator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def load_reference_data() -> tuple[list[Customer], list[Product]]:
    customers = [
        Customer(**record)
        for record in JSONExtractor().extract(RAW_DIR / "customers.json")
    ]
    products = [
        Product(**record)
        for record in JSONExtractor().extract(RAW_DIR / "products.json")
    ]
    return customers, products


def test_validator_separates_valid_and_rejected_sales() -> None:
    rows = CSVExtractor().extract(RAW_DIR / "sales_2023_01.csv")
    customers, products = load_reference_data()

    valid, rejected = SalesDataValidator().validate_all(rows, customers, products)

    assert len(valid) + len(rejected) == len(rows)
    assert any("unknown customer_id" in item.reason for item in rejected)
    assert any("quantity must be greater" in item.reason for item in rejected)


def test_transformer_calculates_sales_measures() -> None:
    record = ValidatedSalesRecord(
        order_id="O-TEST",
        order_date=date(2023, 1, 1),
        customer_id="C001",
        product_id="P001",
        quantity=2,
        unit_price=Decimal("10.00"),
        discount_rate=Decimal("0.10"),
    )

    fact = SalesDataTransformer().transform_sales(record)

    assert fact.gross_sales == Decimal("20.00")
    assert fact.discount_amount == Decimal("2.00")
    assert fact.net_sales == Decimal("18.00")


def test_pipeline_runs_without_database(tmp_path: Path) -> None:
    copytree(RAW_DIR, tmp_path / "data" / "raw")

    summary = SalesPipeline(PipelineConfig.from_environment(tmp_path)).run(
        load_to_database=False
    )

    assert summary.extracted_sales == (
        summary.valid_sales + summary.rejected_sales
    )
    assert summary.valid_sales >= 0
    assert summary.rejected_sales >= 0
    assert summary.loaded_sales == 0
    assert (tmp_path / "data" / "rejected" / "rejected_sales.csv").exists()
