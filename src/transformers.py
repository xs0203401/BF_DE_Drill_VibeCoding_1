"""Transform validated input records into analytics-ready models."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable

from .models import (
    Customer,
    FactSalesRecord,
    Product,
    ValidatedSalesRecord,
)


class SalesDataTransformer:
    """Convert extracted records and calculate sales measures."""

    CENT = Decimal("0.01")

    @staticmethod
    def customer_from_dict(record: dict[str, Any]) -> Customer:
        return Customer(
            customer_id=str(record["customer_id"]),
            name=str(record["name"]),
            region=str(record["region"]),
        )

    @staticmethod
    def product_from_dict(record: dict[str, Any]) -> Product:
        return Product(
            product_id=str(record["product_id"]),
            name=str(record["name"]),
            category=str(record["category"]),
        )

    def transform_sales(
        self, record: ValidatedSalesRecord
    ) -> FactSalesRecord:
        gross_sales = self._money(record.quantity * record.unit_price)
        discount_amount = self._money(gross_sales * record.discount_rate)
        net_sales = self._money(gross_sales - discount_amount)

        return FactSalesRecord(
            order_id=record.order_id,
            order_date=record.order_date,
            customer_id=record.customer_id,
            product_id=record.product_id,
            quantity=record.quantity,
            unit_price=record.unit_price,
            discount_rate=record.discount_rate,
            gross_sales=gross_sales,
            discount_amount=discount_amount,
            net_sales=net_sales,
        )

    def transform_all(
        self, records: Iterable[ValidatedSalesRecord]
    ) -> list[FactSalesRecord]:
        return [self.transform_sales(record) for record in records]

    @classmethod
    def _money(cls, value: Decimal) -> Decimal:
        return value.quantize(cls.CENT, rounding=ROUND_HALF_UP)
