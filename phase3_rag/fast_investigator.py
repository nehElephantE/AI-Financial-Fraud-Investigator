import asyncio
import decimal
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import mysql.connector
from datetime import datetime
import hashlib
import json
import diskcache as dc

# Fix imports - remove 'phase3_rag.' prefix
from optimized_rag import OptimizedRAG
from cached_llm import CachedLLM
from config import DB_CONFIG

class FastInvestigator:
    def __init__(self):
        """Initialize optimized fraud investigator"""
        self.rag = OptimizedRAG()
        self.llm = CachedLLM()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.transaction_cache = dc.Cache('./transaction_cache')
        
        print("✅ Fast Investigator initialized")
        print("   Features: RAG caching + LLM response caching + Thread pool")
    
    def investigate(self, transaction_id: str) -> Dict:
        """Complete investigation with caching"""
        
        cache_key = f"invest_{transaction_id}"
        if cache_key in self.transaction_cache:
            print("⚡ Transaction cache hit")
            return self.transaction_cache[cache_key]
        
        transaction = self._get_transaction_cached(transaction_id)
        if not transaction:
            return {"error": "Transaction not found"}
        
        if 'amount' in transaction and isinstance(transaction['amount'], decimal.Decimal):
            transaction['amount'] = float(transaction['amount'])
        
        similar_cases = self.rag.retrieve_similar_cases(transaction)
        summary = self.llm.generate_investigation_summary(transaction, similar_cases)
        sar = self.llm.generate_sar_report(transaction, similar_cases, summary)
        
        result = {
            "transaction_id": transaction_id,
            "summary": summary,
            "sar_report": sar,
            "similar_cases_count": len(similar_cases),
            "timestamp": datetime.now().isoformat()
        }
        
        self.transaction_cache.set(cache_key, result, expire=3600)
        return result
    
    def _get_transaction_cached(self, transaction_id: str) -> Dict:
        """Get transaction with caching"""
        cache_key = f"txn_{transaction_id}"
        
        if cache_key in self.transaction_cache:
            return self.transaction_cache[cache_key]
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT transaction_id, amount, merchant_category, hour_of_day, 
                   is_foreign_transaction, fraud_type
            FROM fact_transaction 
            WHERE transaction_id = %s
        """, (transaction_id,))
        
        transaction = cursor.fetchone()
        conn.close()
        
        if transaction:
            if 'amount' in transaction and isinstance(transaction['amount'], decimal.Decimal):
                transaction['amount'] = float(transaction['amount'])
            self.transaction_cache.set(cache_key, transaction, expire=3600)
        
        return transaction
    
    def clear_cache(self):
        """Clear all caches"""
        self.transaction_cache.clear()
        self.llm.cache.clear()
        print("✅ All caches cleared")

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING FAST INVESTIGATOR")
    print("=" * 60)
    
    investigator = FastInvestigator()
    
    print("\n📊 First investigation (cache miss)...")
    result = investigator.investigate("a9929f62-d259-4356-ba1b-8fa2f7cdf124")
    print(f"\n✅ Investigation complete!")
    print(f"   Similar cases found: {result['similar_cases_count']}")
    print(f"   Summary: {result['summary'][:300]}...")
    
    print("\n⚡ Second investigation (cache hit - should be instant)...")
    import time
    start = time.time()
    result2 = investigator.investigate("a9929f62-d259-4356-ba1b-8fa2f7cdf124")
    elapsed = time.time() - start
    print(f"✅ Response time: {elapsed:.2f} seconds (from cache)")