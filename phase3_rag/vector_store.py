import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import json
import hashlib
from typing import List, Dict, Any
import warnings
warnings.filterwarnings('ignore')

# Fix import - remove 'phase3_rag.' prefix
from config import EMBEDDING_MODEL, CHROMA_PERSIST_DIR

class FraudVectorStore:
    def __init__(self):
        """Initialize ChromaDB for fraud case storage"""
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name="fraud_cases",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"✅ Vector store initialized: {CHROMA_PERSIST_DIR}")
        print(f"   Collection: fraud_cases")
        print(f"   Existing documents: {self.collection.count()}")
    
    def add_fraud_case(self, case: Dict[str, Any]):
        case_id = str(case.get('case_id', hashlib.md5(
            f"{case.get('transaction_id')}_{case.get('timestamp')}".encode()
        ).hexdigest()))
        
        document = self._create_document_text(case)
        metadata = {
            "fraud_type": case.get('fraud_type', 'unknown'),
            "amount": float(case.get('amount', 0)),
            "merchant_category": case.get('merchant_category', 'unknown'),
            "is_foreign": case.get('is_foreign_transaction', False),
            "investigation_outcome": case.get('outcome', 'pending'),
            "timestamp": str(case.get('timestamp', ''))
        }
        
        self.collection.upsert(ids=[case_id], documents=[document], metadatas=[metadata])
        return case_id
    
    def add_batch_cases(self, cases: List[Dict[str, Any]]):
        ids = []
        documents = []
        metadatas = []
        
        for case in cases:
            case_id = str(case.get('case_id', hashlib.md5(
                f"{case.get('transaction_id')}_{case.get('timestamp')}".encode()
            ).hexdigest()))
            ids.append(case_id)
            documents.append(self._create_document_text(case))
            metadatas.append({
                "fraud_type": case.get('fraud_type', 'unknown'),
                "amount": float(case.get('amount', 0)),
                "merchant_category": case.get('merchant_category', 'unknown'),
                "is_foreign": case.get('is_foreign_transaction', False),
                "investigation_outcome": case.get('outcome', 'pending'),
                "timestamp": str(case.get('timestamp', ''))
            })
        
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"✅ Added {len(cases)} cases to vector store")
    
    def search_similar_cases(self, query: str, n_results: int = 5, filter_dict: Dict = None) -> List[Dict]:
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_dict
        )
        
        similar_cases = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                similar_cases.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if results.get('distances') else None
                })
        return similar_cases
    
    def search_by_transaction(self, transaction: Dict, n_results: int = 5) -> List[Dict]:
        query = self._create_document_text(transaction)
        return self.search_similar_cases(query, n_results)
    
    def _create_document_text(self, case: Dict) -> str:
        return f"""
        Fraud Case Summary:
        - Fraud Type: {case.get('fraud_type', 'unknown')}
        - Amount: ${case.get('amount', 0):,.2f}
        - Merchant: {case.get('merchant_category', 'unknown')}
        - Time: Hour {case.get('hour_of_day', 0)}
        - Foreign Transaction: {case.get('is_foreign_transaction', False)}
        - Investigation Outcome: {case.get('outcome', 'pending')}
        - Notes: {case.get('investigation_notes', 'No notes available')}
        
        Pattern Description: {case.get('pattern_description', '')}
        """
    
    def get_stats(self) -> Dict:
        return {
            "total_documents": self.collection.count(),
            "collection_name": self.collection.name,
            "persist_directory": CHROMA_PERSIST_DIR
        }

if __name__ == "__main__":
    print("=" * 60)
    print("VECTOR STORE SETUP")
    print("=" * 60)
    vs = FraudVectorStore()
    print(f"\n📊 Statistics: {vs.get_stats()}")