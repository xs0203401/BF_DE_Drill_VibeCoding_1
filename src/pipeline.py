"""End-to-end orchestration for the sales data pipeline."""

import os
from dataclasses import dataclass
from pathlib import Path

from .extractors import CSVExtractor, JSONExtractor
from .loaders import PostgreSQLLoader, RejectedRecordWriter
from .models import Customer, Product
from .transformers import SalesDataTransformer
from .validators import SalesDataValidator


@dataclass(frozen=True)
class PipelineConfig:
    """Runtime paths and PostgreSQL settings."""

    project_root: Path
    database: str = "name_database"
    user: str = "postgres"
    password: str = "your_password"
    host: str = "localhost"
    port: int = 5432

    @classmethod
    def from_environment(cls, project_root: Path | None = None) -> "PipelineConfig":
        return cls(
            project_root=project_root or Path.cwd(),
            database=os.getenv("POSTGRES_DB", "name_database"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "your_password"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
        )

    @property
    def raw_dir(self) -> Path:
        return self.project_root / "data" / "raw"

    @property
    def rejected_path(self) -> Path:
        return self.project_root / "data" / "rejected" / "rejected_sales.csv"

    @property
    def schema_path(self) -> Path:
        return self.project_root / "sql" / "schema.sql"


@dataclass(frozen=True)
class PipelineSummary:
    extracted_sales: int
    valid_sales: int
    rejected_sales: int
    loaded_sales: int


class SalesPipeline:
    """Coordinate extraction, validation, transformation, and loading."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.csv_extractor = CSVExtractor()
        self.json_extractor = JSONExtractor()
        self.transformer = SalesDataTransformer()
        self.validator = SalesDataValidator()
        self.rejected_writer = RejectedRecordWriter()

    def run(self, load_to_database: bool = True) -> PipelineSummary:
        raw_dir = self.config.raw_dir
        raw_sales = self.csv_extractor.extract(raw_dir / "sales_2023_01.csv")
        customers = [
            Customer(**record)
            for record in self.json_extractor.extract(raw_dir / "customers.json")
        ]
        products = [
            Product(**record)
            for record in self.json_extractor.extract(raw_dir / "products.json")
        ]

        valid_sales, rejected_sales = self.validator.validate_all(
            raw_sales, customers, products
        )
        facts = self.transformer.transform_all(valid_sales)
        self.rejected_writer.write(rejected_sales, self.config.rejected_path)

        if load_to_database:
            loader = PostgreSQLLoader(
                dbname=self.config.database,
                user=self.config.user,
                password=self.config.password,
                host=self.config.host,
                port=self.config.port,
            )
            loader.create_schema(self.config.schema_path)
            loader.load_staging(raw_sales)
            loader.load(customers, products, facts, rejected_sales)

        return PipelineSummary(
            extracted_sales=len(raw_sales),
            valid_sales=len(valid_sales),
            rejected_sales=len(rejected_sales),
            loaded_sales=len(facts) if load_to_database else 0,
        )
