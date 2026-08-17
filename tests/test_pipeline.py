import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from shutil import copytree

import pytest

from src.extractors import CSVExtractor, JSONExtractor
from src.models import Customer, Product, ValidatedSalesRecord
from src.pipeline import PipelineConfig, SalesPipeline
from src.transformers import SalesDataTransformer
from src.validators import SalesDataValidator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def sales_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "order_id": "O-TEST",
        "order_date": "2023-01-01",
        "customer_id": "C001",
        "product_id": "P001",
        "quantity": "2",
        "unit_price": "10.00",
        "discount_rate": "0.10",
    }
    row.update(overrides)
    return row


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


@pytest.mark.parametrize("field", sorted(SalesDataValidator.REQUIRED_FIELDS))
def test_validator_rejects_missing_required_fields(field: str) -> None:
    row = sales_row()
    del row[field]

    with pytest.raises(ValueError, match="missing required fields"):
        SalesDataValidator().validate(row, {"C001"}, {"P001"})


@pytest.mark.parametrize("value", [None, ""])
def test_validator_rejects_null_and_blank_required_fields(value: object) -> None:
    with pytest.raises(ValueError, match="must not be blank"):
        SalesDataValidator().validate(
            sales_row(order_id=value), {"C001"}, {"P001"}
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("quantity", "not-an-int", "quantity must be an integer"),
        ("quantity", "0", "quantity must be greater"),
        ("quantity", "-1", "quantity must be greater"),
        ("unit_price", "not-a-price", "unit_price must be a decimal"),
        ("unit_price", "0", "unit_price must be greater"),
        ("unit_price", "-1", "unit_price must be greater"),
        ("discount_rate", "not-a-rate", "discount_rate must be a decimal"),
        ("discount_rate", "-0.01", "discount_rate must be between"),
        ("discount_rate", "1.01", "discount_rate must be between"),
        ("order_date", "2023/01/01", "order_date must use"),
        ("order_date", "2023-02-30", "order_date is not a valid"),
    ],
)
def test_validator_rejects_invalid_field_values(
    field: str, value: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        SalesDataValidator().validate(
            sales_row(**{field: value}), {"C001"}, {"P001"}
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("customer_id", "C999", "unknown customer_id"),
        ("product_id", "P999", "unknown product_id"),
    ],
)
def test_validator_rejects_unknown_reference_ids(
    field: str, value: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        SalesDataValidator().validate(
            sales_row(**{field: value}), {"C001"}, {"P001"}
        )


def test_validator_keeps_duplicate_sales_at_order_grain_for_loader() -> None:
    rows = [sales_row(), sales_row(quantity="3")]

    valid, rejected = SalesDataValidator().validate_all(
        rows, [Customer("C001", "Customer", "North")], [Product("P001", "Product", "Office")]
    )

    assert len(valid) == 2
    assert not rejected
    assert {item.order_id for item in valid} == {"O-TEST"}


def test_duplicate_reference_ids_are_visible_to_loader_contract() -> None:
    customers = [Customer("C001", "Original", "North"), Customer("C001", "Updated", "South")]
    products = [Product("P001", "Original", "Office"), Product("P001", "Updated", "Home")]

    valid, rejected = SalesDataValidator().validate_all(
        [sales_row()], customers, products
    )

    assert len(valid) == 1
    assert not rejected
    assert len({item.customer_id for item in customers}) == 1
    assert len({item.product_id for item in products}) == 1


def test_validate_all_handles_all_valid_all_invalid_and_mixed_inputs() -> None:
    rows = [
        sales_row(order_id="valid-1"),
        sales_row(order_id="invalid-1", quantity="0"),
        sales_row(order_id="invalid-2", customer_id="C999"),
    ]
    customers = [Customer("C001", "Customer", "North")]
    products = [Product("P001", "Product", "Office")]

    valid, rejected = SalesDataValidator().validate_all(rows, customers, products)
    assert [item.order_id for item in valid] == ["valid-1"]
    assert {item.raw_record["order_id"] for item in rejected} == {
        "invalid-1", "invalid-2"
    }

    all_valid, no_rejections = SalesDataValidator().validate_all(
        [sales_row(order_id="valid-2")], customers, products
    )
    assert len(all_valid) == 1 and not no_rejections

    no_valid, all_rejections = SalesDataValidator().validate_all(
        [sales_row(quantity="0"), sales_row(product_id="P999")], customers, products
    )
    assert not no_valid and len(all_rejections) == 2


def test_extractors_handle_empty_and_malformed_csv(tmp_path: Path) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    assert CSVExtractor().extract(empty) == []

    malformed = tmp_path / "malformed.csv"
    malformed.write_text("order_id,quantity\nO1\n", encoding="utf-8")
    assert CSVExtractor().extract(malformed) == [{"order_id": "O1", "quantity": None}]


def test_json_extractor_handles_empty_and_malformed_json(tmp_path: Path) -> None:
    empty = tmp_path / "empty.json"
    empty.write_text("[]", encoding="utf-8")
    assert JSONExtractor().extract(empty) == []

    malformed = tmp_path / "malformed.json"
    malformed.write_text("{not-json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        JSONExtractor().extract(malformed)

    wrong_shape = tmp_path / "wrong-shape.json"
    wrong_shape.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Expected a JSON list"):
        JSONExtractor().extract(wrong_shape)


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


def test_pipeline_dry_run_summary_and_rejected_records(tmp_path: Path) -> None:
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "customers.json").write_text(
        json.dumps([{"customer_id": "C001", "name": "Customer", "region": "North"}]),
        encoding="utf-8",
    )
    (raw_dir / "products.json").write_text(
        json.dumps([{"product_id": "P001", "name": "Product", "category": "Office"}]),
        encoding="utf-8",
    )
    fields = list(SalesDataValidator.REQUIRED_FIELDS)
    (raw_dir / "sales_2023_01.csv").write_text(
        ",".join(fields) + "\n" + ",".join(str(sales_row()[field]) for field in fields)
        + "\n" + ",".join(str(sales_row(quantity="0")[field]) for field in fields) + "\n",
        encoding="utf-8",
    )

    summary = SalesPipeline(PipelineConfig.from_environment(tmp_path)).run(
        load_to_database=False
    )

    assert summary.extracted_sales == 2
    assert summary.valid_sales == 1
    assert summary.rejected_sales == 1
    assert summary.loaded_sales == 0
    rejected = (tmp_path / "data" / "rejected" / "rejected_sales.csv").read_text()
    assert "quantity must be greater than zero" in rejected


def test_fact_grain_and_duplicate_load_are_order_idempotent() -> None:
    schema = (PROJECT_ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    loader = (PROJECT_ROOT / "src" / "loaders.py").read_text(encoding="utf-8")

    assert "order_id TEXT PRIMARY KEY" in schema
    assert "ON CONFLICT (order_id) DO UPDATE" in loader
