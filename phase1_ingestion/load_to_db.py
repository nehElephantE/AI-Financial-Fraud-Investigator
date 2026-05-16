import mysql.connector
from mysql.connector import Error
import pandas as pd
import uuid
from datetime import datetime
from tqdm import tqdm
import random
import numpy as np
import math
import os

# Use environment variables for Docker deployment
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'port': os.getenv('DB_PORT', '3306'),
    'database': os.getenv('DB_NAME', 'fraud_db'),
    'user': os.getenv('DB_USER', 'fraud_user'),
    'password': os.getenv('DB_PASSWORD', 'fraud123')
}

def safe_value(val):
    """Convert NaN, NaT, and other problematic values to None for MySQL"""
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or np.isnan(val)):
        return None
    if isinstance(val, pd.Timestamp):
        return val
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    if isinstance(val, (np.floating, np.float64)):
        return float(val) if not math.isnan(val) else None
    if pd.isna(val):
        return None
    return val

class DataLoader:
    def __init__(self):
        self.conn = None
        self.batch_id = str(uuid.uuid4())
        self.user_sk_map = {}
        
    def connect(self):
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            print("✅ Connected to MySQL")
            return True
        except Error as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def load_users(self, df):
        unique_users = df[['user_id']].drop_duplicates()
        
        cursor = self.conn.cursor()
        for _, row in unique_users.iterrows():
            user_id = str(row['user_id'])
            cursor.execute("""
                INSERT IGNORE INTO dim_user (user_id, email, phone, address, city, state, zip_code, country)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                f"user_{user_id[:8]}@example.com",
                f"+1-555-{random.randint(100,999)}-{random.randint(1000,9999)}",
                f"{random.randint(100,9999)} Main St",
                "New York",
                "NY",
                f"{random.randint(10000,99999)}",
                "USA"
            ))
        self.conn.commit()
        
        cursor.execute("SELECT user_sk, user_id FROM dim_user")
        for row in cursor.fetchall():
            self.user_sk_map[row[1]] = row[0]
        
        cursor.close()
        print(f"✅ Loaded {len(unique_users)} users")
    
    def load_transactions(self, df):
        cursor = self.conn.cursor()
        success_count = 0
        
        with tqdm(total=len(df), desc="Loading transactions") as pbar:
            for _, row in df.iterrows():
                user_sk = self.user_sk_map.get(str(row['user_id']))
                if not user_sk:
                    pbar.update(1)
                    continue
                
                try:
                    cursor.execute("""
                        INSERT IGNORE INTO fact_transaction (
                            transaction_id, user_sk, transaction_timestamp, amount, currency, 
                            card_number, card_provider, merchant_name, merchant_category,
                            merchant_city, merchant_state, merchant_country, latitude, longitude,
                            device_id, ip_address, is_foreign_transaction, is_weekend, hour_of_day,
                            is_fraud, fraud_type, fraud_score
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        safe_value(row['transaction_id']),
                        safe_value(user_sk),
                        safe_value(row['timestamp']),
                        safe_value(row['amount']),
                        safe_value(row.get('currency', 'USD')),
                        safe_value(row.get('card_number')),
                        safe_value(row.get('card_provider')),
                        safe_value(row.get('merchant_name')),
                        safe_value(row['merchant_category']),
                        safe_value(row.get('merchant_city')),
                        safe_value(row.get('merchant_state')),
                        safe_value(row.get('merchant_country', 'USA')),
                        safe_value(row.get('latitude')),
                        safe_value(row.get('longitude')),
                        safe_value(row.get('device_id')),
                        safe_value(row.get('ip_address')),
                        1 if safe_value(row.get('is_foreign_transaction', False)) else 0,
                        1 if safe_value(row.get('is_weekend', False)) else 0,
                        int(safe_value(row.get('hour_of_day', 12)) or 12),
                        1 if safe_value(row['is_fraud']) else 0,
                        safe_value(row.get('fraud_type')),
                        float(random.uniform(0.7, 0.99)) if safe_value(row['is_fraud']) else 0.0
                    ))
                    success_count += 1
                    pbar.update(1)
                except Exception as e:
                    pbar.update(1)
                    continue
        
        self.conn.commit()
        cursor.close()
        print(f"✅ Loaded {success_count} transactions")
        
        # Load fraud labels
        fraud_df = df[df['is_fraud']]
        if len(fraud_df) > 0:
            cursor = self.conn.cursor()
            for _, row in fraud_df.iterrows():
                cursor.execute("""
                    INSERT IGNORE INTO dim_fraud_label (transaction_id, is_fraud, fraud_type)
                    VALUES (%s, %s, %s)
                """, (
                    safe_value(row['transaction_id']),
                    1,
                    safe_value(row.get('fraud_type'))
                ))
            self.conn.commit()
            cursor.close()
            print(f"✅ Loaded {len(fraud_df)} fraud labels")
    
    def log_audit(self, records_count, fraud_count, status='SUCCESS'):
        cursor = self.conn.cursor()
        records_count = int(records_count) if isinstance(records_count, (np.integer, np.int64)) else records_count
        fraud_count = int(fraud_count) if isinstance(fraud_count, (np.integer, np.int64)) else fraud_count
        
        cursor.execute("""
            INSERT INTO audit_ingestion (batch_id, records_processed, fraud_count, start_time, end_time, status)
            VALUES (%s, %s, %s, NOW(), NOW(), %s)
        """, (self.batch_id, records_count, fraud_count, status))
        self.conn.commit()
        cursor.close()
    
    def close(self):
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("PHASE 1: DATA LOADING (MySQL)")
    print("=" * 50)
    
    print("📖 Reading transactions from CSV...")
    df = pd.read_csv('transactions_raw.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print(f"📊 Loaded {len(df)} transactions from CSV")
    print(f"🔍 Fraud transactions: {df['is_fraud'].sum()}")
    
    loader = DataLoader()
    if loader.connect():
        loader.load_users(df)
        loader.load_transactions(df)
        loader.log_audit(len(df), df['is_fraud'].sum())
        loader.close()
        print("\n✅ Data ingestion complete!")