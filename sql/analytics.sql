-- 1. How much net revenue did we make each day?
SELECT
    order_date,
    SUM(net_sales) AS daily_net_sales
FROM fact_sales
GROUP BY order_date
ORDER BY order_date;

-- 2. Which products generated the most revenue?
SELECT
    p.product_id,
    p.name AS product_name,
    SUM(f.quantity) AS units_sold,
    SUM(f.net_sales) AS total_net_sales
FROM fact_sales AS f
JOIN dim_products AS p ON p.product_id = f.product_id
GROUP BY p.product_id, p.name
ORDER BY total_net_sales DESC;

-- 3. Which regions had the highest sales?
SELECT
    c.region,
    SUM(f.net_sales) AS total_net_sales
FROM fact_sales AS f
JOIN dim_customers AS c ON c.customer_id = f.customer_id
GROUP BY c.region
ORDER BY total_net_sales DESC;

-- 4. Which customers had the highest lifetime value?
SELECT
    c.customer_id,
    c.name AS customer_name,
    SUM(f.net_sales) AS lifetime_value
FROM fact_sales AS f
JOIN dim_customers AS c ON c.customer_id = f.customer_id
GROUP BY c.customer_id, c.name
ORDER BY lifetime_value DESC;

-- 5. Which validation failures were captured?
SELECT
    reason,
    COUNT(*) AS rejected_count
FROM ctl_rejected_sales
GROUP BY reason
ORDER BY rejected_count DESC, reason;
