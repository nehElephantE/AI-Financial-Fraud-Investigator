import os
import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')

# ============================================
# CONFIGURATION (Using Environment Variables)
# ============================================

# Database - Use environment variables for Docker
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'port': os.getenv('DB_PORT', '3306'),
    'database': os.getenv('DB_NAME', 'fraud_db'),
    'user': os.getenv('DB_USER', 'fraud_user'),
    'password': os.getenv('DB_PASSWORD', 'fraud123')
}

# Model paths
MODEL_PATH = 'models/'
os.makedirs(MODEL_PATH, exist_ok=True)

# Features columns
NUMERIC_FEATURES = [
    'amount', 'hour_of_day', 'amount_zscore_user', 
    'txn_count_1h', 'txn_count_24h', 'unique_merchants_1h',
    'amount_to_avg_ratio', 'days_since_last_txn'
]

CATEGORICAL_FEATURES = [
    'merchant_category', 'is_weekend', 'is_foreign_transaction',
    'card_provider'
]

TARGET = 'is_fraud'

# ============================================
# FEATURE ENGINEERING
# ============================================

class FeatureEngineer:
    def __init__(self):
        self.label_encoders = {}
        
    def fetch_data(self):
        """Fetch transactions from MySQL database"""
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            
            query = """
                SELECT 
                    ft.transaction_id,
                    ft.user_sk,
                    ft.transaction_timestamp,
                    ft.amount,
                    ft.currency,
                    ft.card_provider,
                    ft.merchant_name,
                    ft.merchant_category,
                    ft.merchant_city,
                    ft.merchant_state,
                    ft.merchant_country,
                    ft.latitude,
                    ft.longitude,
                    ft.is_foreign_transaction,
                    ft.is_weekend,
                    ft.hour_of_day,
                    ft.is_fraud,
                    ft.fraud_type
                FROM fact_transaction ft
                ORDER BY ft.user_sk, ft.transaction_timestamp
            """
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            print(f"✅ Fetched {len(df)} transactions")
            return df
            
        except Error as e:
            print(f"❌ Database error: {e}")
            return None
    
    def create_user_features(self, df):
        """Create user-level features"""
        print("Creating user-level features...")
        
        # Sort by user and time
        df = df.sort_values(['user_sk', 'transaction_timestamp'])
        
        # Amount Z-score per user
        df['amount_zscore_user'] = df.groupby('user_sk')['amount'].transform(
            lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
        )
        
        # Initialize columns
        df['txn_count_1h'] = 0
        df['txn_count_24h'] = 0
        df['unique_merchants_1h'] = 0
        df['days_since_last_txn'] = 0
        df['amount_to_avg_ratio'] = 1
        
        for user_sk in tqdm(df['user_sk'].unique(), desc="Processing users"):
            user_mask = df['user_sk'] == user_sk
            user_df = df[user_mask].copy().reset_index(drop=True)
            
            for idx in range(len(user_df)):
                current_time = user_df.loc[idx, 'transaction_timestamp']
                
                # Get previous transactions
                prev_df = user_df[user_df['transaction_timestamp'] < current_time]
                
                if len(prev_df) > 0:
                    past_1h = prev_df[prev_df['transaction_timestamp'] >= current_time - pd.Timedelta(hours=1)]
                    past_24h = prev_df[prev_df['transaction_timestamp'] >= current_time - pd.Timedelta(hours=24)]
                    
                    df.loc[user_mask & (df['transaction_timestamp'] == current_time), 'txn_count_1h'] = len(past_1h)
                    df.loc[user_mask & (df['transaction_timestamp'] == current_time), 'txn_count_24h'] = len(past_24h)
                    
                    unique_merchants = past_1h['merchant_category'].nunique()
                    df.loc[user_mask & (df['transaction_timestamp'] == current_time), 'unique_merchants_1h'] = unique_merchants
                    
                    last_txn = prev_df.iloc[-1]['transaction_timestamp']
                    days_diff = (current_time - last_txn).total_seconds() / 86400
                    df.loc[user_mask & (df['transaction_timestamp'] == current_time), 'days_since_last_txn'] = days_diff
                    
                    if len(past_24h) > 0:
                        avg_amount = past_24h['amount'].mean()
                        current_amount = user_df.loc[idx, 'amount']
                        ratio = current_amount / avg_amount if avg_amount > 0 else 1
                        df.loc[user_mask & (df['transaction_timestamp'] == current_time), 'amount_to_avg_ratio'] = ratio
        
        return df
    
    def encode_categorical(self, df):
        """Encode categorical features"""
        print("Encoding categorical features...")
        
        for col in ['merchant_category', 'card_provider']:
            if col in df.columns:
                le = LabelEncoder()
                df[f'{col}_encoded'] = le.fit_transform(df[col].fillna('Unknown').astype(str))
                self.label_encoders[col] = le
        
        df['is_weekend'] = df['is_weekend'].astype(int)
        df['is_foreign_transaction'] = df['is_foreign_transaction'].astype(int)
        
        return df
    
    def prepare_features(self, df):
        """Prepare final feature matrix"""
        print("Preparing feature matrix...")
        
        feature_cols = [
            'amount', 'hour_of_day', 'amount_zscore_user',
            'txn_count_1h', 'txn_count_24h', 'unique_merchants_1h',
            'days_since_last_txn', 'amount_to_avg_ratio',
            'is_weekend', 'is_foreign_transaction',
            'merchant_category_encoded', 'card_provider_encoded'
        ]
        
        X = df[feature_cols].fillna(0)
        y = df['is_fraud'].astype(int)
        
        print(f"✅ Feature matrix shape: {X.shape}")
        print(f"   Features: {feature_cols}")
        print(f"   Fraud ratio: {y.mean():.4f}")
        
        return X, y, feature_cols

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 2: FEATURE ENGINEERING")
    print("=" * 60)
    
    engineer = FeatureEngineer()
    
    df = engineer.fetch_data()
    if df is None:
        exit()
    
    df = engineer.create_user_features(df)
    df = engineer.encode_categorical(df)
    
    X, y, features = engineer.prepare_features(df)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    train_df = X_train.copy()
    train_df['is_fraud'] = y_train
    train_df.to_csv('train_data.csv', index=False)
    
    test_df = X_test.copy()
    test_df['is_fraud'] = y_test
    test_df.to_csv('test_data.csv', index=False)
    
    print("\n✅ Data saved to train_data.csv and test_data.csv")
    print(f"   Training set: {len(X_train)} transactions ({y_train.mean():.4f} fraud rate)")
    print(f"   Test set: {len(X_test)} transactions ({y_test.mean():.4f} fraud rate)")
    print(f"   Features: {len(features)} features")