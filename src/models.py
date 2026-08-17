"""Data contracts used by the sales pipeline."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class Customer:
    customer_id: str
    name: str
    region: str


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    category: str


@dataclass(frozen=True)
class RawSalesRecord:
    order_id: str
    order_date: str
    customer_id: str
    product_id: str
    quantity: str
    unit_price: str
    discount_rate: str


@dataclass(frozen=True)
class ValidatedSalesRecord:
    order_id: str
    order_date: date
    customer_id: str
    product_id: str
    quantity: int
    unit_price: Decimal
    discount_rate: Decimal


@dataclass(frozen=True)
class FactSalesRecord:
    order_id: str
    order_date: date
    customer_id: str
    product_id: str
    quantity: int
    unit_price: Decimal
    discount_rate: Decimal
    gross_sales: Decimal
    discount_amount: Decimal
    net_sales: Decimal


@dataclass(frozen=True)
class RejectedRecord:
    raw_record: dict[str, Any]
    reason: str
