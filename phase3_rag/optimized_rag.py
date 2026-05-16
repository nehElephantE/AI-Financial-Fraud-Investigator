import hashlib
import json
from functools import lru_cache
from typing import List, Dict, Any
import warnings
warnings.filterwarnings('ignore')

# Fix import - remove 'phase3_rag.' prefix
from vector_store import FraudVectorStore

class OptimizedRAG:
    def __init__(self):
        """Initialize RAG with caching and optimized retrieval"""
        self.vector_store = FraudVectorStore()
        self.similarity_cache = {}
        
    def retrieve_similar_cases(self, transaction: Dict, n_results: int = 3) -> List[Dict]:
        """Retrieve similar cases with query optimization"""
        
        cache_key = self._create_cache_key(transaction, n_results)
        
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        optimized_transaction = self._optimize_transaction(transaction)
        query = self._create_optimized_query(optimized_transaction)
        results = self.vector_store.search_similar_cases(query, n_results=n_results * 2)
        ranked_results = self._fast_rerank(optimized_transaction, results)
        self.similarity_cache[cache_key] = ranked_results[:n_results]
        
        return ranked_results[:n_results]
    
    def _create_cache_key(self, transaction: Dict, n_results: int) -> str:
        amount = transaction.get('amount', 0)
        if hasattr(amount, '__class__') and 'Decimal' in str(amount.__class__):
            amount = float(amount)
        
        key_data = {
            'amount': round(float(amount), -1) if amount else 0,
            'fraud_type': transaction.get('fraud_type', 'unknown'),
            'merchant': transaction.get('merchant_category', 'unknown'),
            'hour': transaction.get('hour_of_day', 0) // 4,
            'n_results': n_results
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _optimize_transaction(self, transaction: Dict) -> Dict:
        amount = transaction.get('amount', 0)
        if hasattr(amount, '__class__') and 'Decimal' in str(amount.__class__):
            amount = float(amount)
        
        return {
            'amount': float(amount),
            'fraud_type': transaction.get('fraud_type', 'unknown'),
            'merchant_category': transaction.get('merchant_category', 'unknown'),
            'hour_of_day': transaction.get('hour_of_day', 0),
            'is_foreign_transaction': transaction.get('is_foreign_transaction', False)
        }
    
    def _create_optimized_query(self, transaction: Dict) -> str:
        parts = []
        amount = transaction.get('amount', 0)
        
        if amount > 5000:
            parts.append(f"large amount ${amount:.0f}")
        elif amount < 100:
            parts.append(f"small amount ${amount:.0f}")
        
        fraud_type = transaction.get('fraud_type')
        if fraud_type and fraud_type != 'unknown':
            parts.append(fraud_type)
        
        merchant = transaction.get('merchant_category')
        if merchant and merchant != 'unknown':
            parts.append(merchant)
        
        return " ".join(parts) if parts else "suspicious transaction"
    
    def _fast_rerank(self, transaction: Dict, results: List[Dict]) -> List[Dict]:
        txn_amount = float(transaction.get('amount', 0))
        txn_fraud_type = transaction.get('fraud_type', '')
        txn_merchant = transaction.get('merchant_category', '')
        
        for result in results:
            score = 0
            metadata = result.get('metadata', {})
            
            if metadata.get('fraud_type') == txn_fraud_type:
                score += 0.5
            if metadata.get('merchant_category') == txn_merchant:
                score += 0.3
            
            case_amount = metadata.get('amount', 0)
            if case_amount:
                if hasattr(case_amount, '__class__') and 'Decimal' in str(case_amount.__class__):
                    case_amount = float(case_amount)
                else:
                    case_amount = float(case_amount)
                if abs(case_amount - txn_amount) < 100:
                    score += 0.2
            
            result['similarity'] = score
        
        return sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)

if __name__ == "__main__":
    rag = OptimizedRAG()
    print("✅ Optimized RAG ready")