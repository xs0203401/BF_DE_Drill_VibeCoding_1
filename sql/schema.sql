-- Raw landing table. Values remain text until validation succeeds.
CREATE TABLE IF NOT EXISTS stg_sales (
    order_id TEXT,
    order_date TEXT,
    customer_id TEXT,
    product_id TEXT,
    quantity TEXT,
    unit_price TEXT,
    discount_rate TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_products (
    product_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_sales (
    order_id TEXT PRIMARY KEY,
    order_date DATE NOT NULL,
    customer_id TEXT NOT NULL REFERENCES dim_customers (customer_id),
    product_id TEXT NOT NULL REFERENCES dim_products (product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price > 0),
    discount_rate NUMERIC(5, 4) NOT NULL CHECK (discount_rate BETWEEN 0 AND 1),
    gross_sales NUMERIC(14, 2) NOT NULL,
    discount_amount NUMERIC(14, 2) NOT NULL,
    net_sales NUMERIC(14, 2) NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ctl_rejected_sales (
    rejection_id BIGSERIAL PRIMARY KEY,
    order_id TEXT,
    reason TEXT NOT NULL,
    raw_record JSONB NOT NULL,
    rejected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fact_sales_order_date
    ON fact_sales (order_date);

CREATE INDEX IF NOT EXISTS idx_fact_sales_customer_id
    ON fact_sales (customer_id);

CREATE INDEX IF NOT EXISTS idx_fact_sales_product_id
    ON fact_sales (product_id);
