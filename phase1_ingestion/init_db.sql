-- Create database
DROP DATABASE IF EXISTS fraud_db;
CREATE DATABASE fraud_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE fraud_db;

-- Users table
CREATE TABLE dim_user (
    user_sk INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE,
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50),
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE fact_transaction (
    transaction_sk INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(36) NOT NULL UNIQUE,
    user_sk INT,
    transaction_timestamp DATETIME NOT NULL,
    amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    card_number VARCHAR(19),
    card_provider VARCHAR(50),
    merchant_name VARCHAR(255),
    merchant_category VARCHAR(100),
    merchant_city VARCHAR(100),
    merchant_state VARCHAR(50),
    merchant_country VARCHAR(50),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    device_id VARCHAR(255),
    ip_address VARCHAR(45),
    is_foreign_transaction BOOLEAN,
    is_weekend BOOLEAN,
    hour_of_day INT,
    is_fraud BOOLEAN DEFAULT FALSE,
    fraud_type VARCHAR(50),
    fraud_score DECIMAL(5,4),
    ingested_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_sk) REFERENCES dim_user(user_sk)
);

-- Indexes
CREATE INDEX idx_transaction_user ON fact_transaction(user_sk, transaction_timestamp DESC);
CREATE INDEX idx_transaction_time ON fact_transaction(transaction_timestamp DESC);
CREATE INDEX idx_transaction_fraud ON fact_transaction(is_fraud);

-- Fraud labels table
CREATE TABLE dim_fraud_label (
    label_sk INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(36) NOT NULL UNIQUE,
    is_fraud BOOLEAN,
    fraud_type VARCHAR(50),
    confirmed_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed_by VARCHAR(100) DEFAULT 'system'
);

-- Audit log (fixed timestamp defaults)
CREATE TABLE audit_ingestion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id VARCHAR(36),
    records_processed INT,
    fraud_count INT,
    start_time DATETIME,
    end_time DATETIME,
    status VARCHAR(20)
);

-- Fraud summary view
CREATE OR REPLACE VIEW view_fraud_summary AS
SELECT 
    DATE(transaction_timestamp) as transaction_date,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN is_fraud = TRUE THEN 1 ELSE 0 END) as fraud_count,
    ROUND(100.0 * SUM(CASE WHEN is_fraud = TRUE THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) as fraud_rate,
    AVG(amount) as avg_amount,
    MAX(amount) as max_amount
FROM fact_transaction
GROUP BY DATE(transaction_timestamp)
ORDER BY transaction_date DESC;