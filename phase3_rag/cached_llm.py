import hashlib
import json
import decimal
from functools import lru_cache
from typing import List, Dict, Any
import warnings
import diskcache as dc
warnings.filterwarnings('ignore')

# Fix import - remove 'phase3_rag.' prefix
from llm_investigator import LLMInvestigator

def convert_decimal(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

class CachedLLM:
    def __init__(self, cache_dir='./llm_cache'):
        """Initialize LLM with disk caching"""
        self.llm = LLMInvestigator()
        self.cache = dc.Cache(cache_dir)
        print(f"✅ Cached LLM initialized (cache dir: {cache_dir})")
    
    def generate_investigation_summary(self, transaction: Dict, similar_cases: List[Dict]) -> str:
        """Generate summary with caching"""
        cache_key = self._create_cache_key(transaction, similar_cases)
        
        if cache_key in self.cache:
            print("⚡ Cache hit - returning cached response")
            return self.cache[cache_key]
        
        print("🔄 Cache miss - generating new response")
        response = self.llm.generate_investigation_summary(transaction, similar_cases)
        self.cache.set(cache_key, response, expire=86400)
        return response
    
    def generate_sar_report(self, transaction: Dict, similar_cases: List[Dict], summary: str) -> str:
        """Generate SAR with caching"""
        cache_key = hashlib.md5(
            f"{transaction.get('transaction_id')}_sar".encode()
        ).hexdigest()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        response = self.llm.generate_sar_report(transaction, similar_cases, summary)
        self.cache.set(cache_key, response, expire=86400)
        return response
    
    def answer_question(self, question: str, transaction: Dict, similar_cases: List[Dict]) -> str:
        """Answer question with caching"""
        cache_key = hashlib.md5(
            f"{transaction.get('transaction_id')}_{question}".encode()
        ).hexdigest()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        response = self.llm.answer_question(question, transaction, similar_cases)
        self.cache.set(cache_key, response, expire=3600)
        return response
    
    def _create_cache_key(self, transaction: Dict, similar_cases: List[Dict]) -> str:
        """Create cache key from transaction data with Decimal handling"""
        amount = transaction.get('amount', 0)
        if isinstance(amount, decimal.Decimal):
            amount = float(amount)
        
        key_data = {
            'amount': round(amount, -1) if amount else 0,
            'fraud_type': str(transaction.get('fraud_type', 'unknown')),
            'merchant': str(transaction.get('merchant_category', 'unknown')),
            'hour': transaction.get('hour_of_day', 0) // 4,
            'similar_count': len(similar_cases)
        }
        
        key_str = json.dumps(key_data, sort_keys=True, default=convert_decimal)
        return hashlib.md5(key_str.encode()).hexdigest()

if __name__ == "__main__":
    cached_llm = CachedLLM()
    print("✅ Cached LLM ready")