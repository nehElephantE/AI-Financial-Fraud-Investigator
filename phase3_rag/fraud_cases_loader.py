import json
import pandas as pd
import mysql.connector
from datetime import datetime
# Fix imports - remove 'phase3_rag.' prefix
from vector_store import FraudVectorStore
from config import DB_CONFIG
import warnings
warnings.filterwarnings('ignore')

def load_historical_fraud_cases_from_db():
    """Load historical fraud cases from MySQL database"""
    print("📊 Loading historical fraud cases from database...")
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        
        query = """
            SELECT 
                ft.transaction_id,
                ft.amount,
                ft.merchant_category,
                ft.hour_of_day,
                ft.is_foreign_transaction,
                ft.fraud_type,
                ft.transaction_timestamp as timestamp,
                ft.user_sk,
                'confirmed_fraud' as outcome,
                'Detected by ML model' as investigation_notes,
                CONCAT('Fraud pattern: ', ft.fraud_type, 
                       '. Amount anomaly detected. Transaction flagged for review.') as pattern_description
            FROM fact_transaction ft
            WHERE ft.is_fraud = 1
            LIMIT 500
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        cases = df.to_dict('records')
        print(f"✅ Loaded {len(cases)} historical fraud cases")
        return cases
        
    except Exception as e:
        print(f"❌ Error loading cases: {e}")
        return []

def load_sample_fraud_cases():
    """Load sample fraud cases (if database is empty)"""
    return [
        {
            "case_id": "CASE-001",
            "transaction_id": "TXN-001",
            "fraud_type": "structuring",
            "amount": 9850.00,
            "merchant_category": "Other",
            "hour_of_day": 14,
            "is_foreign_transaction": False,
            "outcome": "confirmed_fraud",
            "investigation_notes": "Multiple transactions just below reporting threshold. Pattern indicates structuring to avoid CTR filing.",
            "pattern_description": "Amounts consistently between $9,500-$9,990 across multiple days"
        },
        {
            "case_id": "CASE-002",
            "transaction_id": "TXN-002",
            "fraud_type": "velocity",
            "amount": 150.00,
            "merchant_category": "Retail",
            "hour_of_day": 2,
            "is_foreign_transaction": False,
            "outcome": "confirmed_fraud",
            "investigation_notes": "15 transactions within 2 hours from different merchants. Card likely compromised.",
            "pattern_description": "High frequency of small transactions in short time window"
        },
        {
            "case_id": "CASE-003",
            "transaction_id": "TXN-003",
            "fraud_type": "location_mismatch",
            "amount": 2500.00,
            "merchant_category": "Electronics",
            "hour_of_day": 19,
            "is_foreign_transaction": True,
            "outcome": "confirmed_fraud",
            "investigation_notes": "Transaction from foreign country while cardholder reported being at home. International fraud ring suspected.",
            "pattern_description": "Geographic anomaly - transaction location far from cardholder's typical location"
        },
        {
            "case_id": "CASE-004",
            "transaction_id": "TXN-004",
            "fraud_type": "amount_anomaly",
            "amount": 8500.00,
            "merchant_category": "Electronics",
            "hour_of_day": 15,
            "is_foreign_transaction": False,
            "outcome": "confirmed_fraud",
            "investigation_notes": "Amount 10x higher than user's average transaction. No prior history of large purchases.",
            "pattern_description": "Sudden spike in transaction amount compared to historical behavior"
        },
        {
            "case_id": "CASE-005",
            "transaction_id": "TXN-005",
            "fraud_type": "off_hours",
            "amount": 3200.00,
            "merchant_category": "Travel",
            "hour_of_day": 3,
            "is_foreign_transaction": False,
            "outcome": "confirmed_fraud",
            "investigation_notes": "Unusual hour (3 AM) for travel booking. Cardholder confirmed they were asleep.",
            "pattern_description": "Large transaction during off-hours (1 AM - 5 AM)"
        }
    ]

def populate_vector_store():
    """Populate vector store with fraud cases"""
    print("=" * 60)
    print("POPULATING VECTOR STORE WITH FRAUD CASES")
    print("=" * 60)
    
    vs = FraudVectorStore()
    cases = load_historical_fraud_cases_from_db()
    
    if not cases:
        print("⚠️ No cases found in database. Using sample cases...")
        cases = load_sample_fraud_cases()
    
    vs.add_batch_cases(cases)
    
    print(f"\n✅ Vector store populated with {len(cases)} fraud cases")
    print(f"📊 Statistics: {vs.get_stats()}")
    
    print("\n🔍 Testing search with sample query...")
    test_query = "transaction with unusual amount"
    results = vs.search_similar_cases(test_query, n_results=3)
    
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"    Distance: {result['distance']:.4f}")
        print(f"    Metadata: {result['metadata']}")

if __name__ == "__main__":
    populate_vector_store()