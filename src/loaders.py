"""Persistence components for rejected records and PostgreSQL tables."""

import csv
from pathlib import Path
from typing import Any, Iterable

import psycopg2
from psycopg2.extras import execute_values

from .models import Customer, FactSalesRecord, Product, RejectedRecord


class RejectedRecordWriter:
    """Write invalid records and their validation reasons to CSV."""

    def write(self, records: Iterable[RejectedRecord], path: Path) -> None:
        records = list(records)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not records:
            path.write_text("reason\n", encoding="utf-8")
            return

        raw_fields = list(records[0].raw_record)
        with path.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=["reason", *raw_fields])
            writer.writeheader()
            for record in records:
                writer.writerow({"reason": record.reason, **record.raw_record})


class PostgreSQLLoader:
    """Create the warehouse schema and load transformed records."""

    def __init__(self, **connection_kwargs: Any) -> None:
        self.connection_kwargs = connection_kwargs

    def create_schema(self, schema_path: Path) -> None:
        schema_sql = schema_path.read_text(encoding="utf-8")
        with psycopg2.connect(**self.connection_kwargs) as connection:
            with connection.cursor() as cursor:
                cursor.execute(schema_sql)

    def load(
        self,
        customers: Iterable[Customer],
        products: Iterable[Product],
        sales: Iterable[FactSalesRecord],
    ) -> None:
        customers = list(customers)
        products = list(products)
        sales = list(sales)

        with psycopg2.connect(**self.connection_kwargs) as connection:
            with connection.cursor() as cursor:
                execute_values(
                    cursor,
                    """
                    INSERT INTO dim_customers (customer_id, name, region)
                    VALUES %s
                    ON CONFLICT (customer_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        region = EXCLUDED.region
                    """,
                    [(item.customer_id, item.name, item.region) for item in customers],
                )
                execute_values(
                    cursor,
                    """
                    INSERT INTO dim_products (product_id, name, category)
                    VALUES %s
                    ON CONFLICT (product_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        category = EXCLUDED.category
                    """,
                    [(item.product_id, item.name, item.category) for item in products],
                )
                execute_values(
                    cursor,
                    """
                    INSERT INTO fact_sales (
                        order_id, order_date, customer_id, product_id, quantity,
                        unit_price, discount_rate, gross_sales, discount_amount, net_sales
                    )
                    VALUES %s
                    ON CONFLICT (order_id) DO UPDATE SET
                        order_date = EXCLUDED.order_date,
                        customer_id = EXCLUDED.customer_id,
                        product_id = EXCLUDED.product_id,
                        quantity = EXCLUDED.quantity,
                        unit_price = EXCLUDED.unit_price,
                        discount_rate = EXCLUDED.discount_rate,
                        gross_sales = EXCLUDED.gross_sales,
                        discount_amount = EXCLUDED.discount_amount,
                        net_sales = EXCLUDED.net_sales
                    """,
                    [
                        (
                            item.order_id,
                            item.order_date,
                            item.customer_id,
                            item.product_id,
                            item.quantity,
                            item.unit_price,
                            item.discount_rate,
                            item.gross_sales,
                            item.discount_amount,
                            item.net_sales,
                        )
                        for item in sales
                    ],
                )

    def close(self) -> None:
        """Retained for API compatibility; connections are context-managed per operation."""


__all__ = ["PostgreSQLLoader", "RejectedRecordWriter"]
