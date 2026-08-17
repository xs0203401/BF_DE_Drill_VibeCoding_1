"""Validation rules for raw sales records."""

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

from .models import (
    Customer,
    Product,
    RawSalesRecord,
    RejectedRecord,
    ValidatedSalesRecord,
)


class SalesDataValidator:
    """Validate sales rows against field and reference-data rules."""

    REQUIRED_FIELDS = {
        "order_id",
        "order_date",
        "customer_id",
        "product_id",
        "quantity",
        "unit_price",
        "discount_rate",
    }

    def validate(
        self,
        record: dict[str, Any],
        customer_ids: set[str],
        product_ids: set[str],
    ) -> ValidatedSalesRecord:
        missing = sorted(self.REQUIRED_FIELDS - record.keys())
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")

        if any(not str(record[field]).strip() for field in self.REQUIRED_FIELDS):
            raise ValueError("required fields must not be blank")

        order_date_text = str(record["order_date"])
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", order_date_text):
            raise ValueError("order_date must use YYYY-MM-DD format")
        try:
            order_date = date.fromisoformat(order_date_text)
        except ValueError as error:
            raise ValueError("order_date is not a valid calendar date") from error

        try:
            quantity = int(str(record["quantity"]))
        except (TypeError, ValueError) as error:
            raise ValueError("quantity must be an integer") from error
        if quantity <= 0:
            raise ValueError("quantity must be greater than zero")

        unit_price = self._decimal(record["unit_price"], "unit_price")
        if unit_price <= 0:
            raise ValueError("unit_price must be greater than zero")

        discount_rate = self._decimal(record["discount_rate"], "discount_rate")
        if not Decimal("0") <= discount_rate <= Decimal("1"):
            raise ValueError("discount_rate must be between zero and one")

        customer_id = str(record["customer_id"])
        if customer_id not in customer_ids:
            raise ValueError(f"unknown customer_id: {customer_id}")

        product_id = str(record["product_id"])
        if product_id not in product_ids:
            raise ValueError(f"unknown product_id: {product_id}")

        return ValidatedSalesRecord(
            order_id=str(record["order_id"]),
            order_date=order_date,
            customer_id=customer_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            discount_rate=discount_rate,
        )

    def validate_all(
        self,
        records: Iterable[dict[str, Any]],
        customers: Iterable[Customer],
        products: Iterable[Product],
    ) -> tuple[list[ValidatedSalesRecord], list[RejectedRecord]]:
        customer_ids = {customer.customer_id for customer in customers}
        product_ids = {product.product_id for product in products}
        valid: list[ValidatedSalesRecord] = []
        rejected: list[RejectedRecord] = []

        for raw_record in records:
            try:
                valid.append(self.validate(raw_record, customer_ids, product_ids))
            except ValueError as error:
                rejected.append(RejectedRecord(dict(raw_record), str(error)))

        return valid, rejected

    @staticmethod
    def _decimal(value: Any, field_name: str) -> Decimal:
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise ValueError(f"{field_name} must be a decimal number") from error


def raw_sales_record(row: dict[str, Any]) -> RawSalesRecord:
    """Convert an extracted row into the raw sales data contract."""
    return RawSalesRecord(**{field: str(row[field]) for field in SalesDataValidator.REQUIRED_FIELDS})
