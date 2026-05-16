import os
from typing import List, Dict, Any
import warnings
warnings.filterwarnings('ignore')

# Fix import - remove 'phase3_rag.' prefix
from config import USE_LOCAL_LLM, LOCAL_LLM_PATH

class LLMInvestigator:
    def __init__(self):
        """Initialize LLM for fraud investigation"""
        self.llm = None
        self.use_local = False
        
        if USE_LOCAL_LLM and os.path.exists(LOCAL_LLM_PATH):
            try:
                from llama_cpp import Llama
                print(f"📥 Loading Phi-2 LLM from {LOCAL_LLM_PATH}...")
                print("   (First load takes 10-20 seconds)")
                
                self.llm = Llama(
                    model_path=LOCAL_LLM_PATH,
                    n_ctx=512,
                    n_threads=4,
                    n_gpu_layers=0,
                    verbose=False
                )
                self.use_local = True
                print("✅ Phi-2 LLM initialized successfully!")
            except Exception as e:
                print(f"⚠️ LLM failed to load: {e}")
                self.use_local = False
        else:
            print("📝 Using template mode (no LLM)")
    
    # Rest of the class remains the same (all methods unchanged)
    def generate_investigation_summary(self, transaction: Dict, similar_cases: List[Dict]) -> str:
        """Generate investigation summary using LLM"""
        if self.use_local:
            prompt = self._create_investigation_prompt(transaction, similar_cases)
            return self._call_llm(prompt)
        else:
            return self._template_summary(transaction, similar_cases)
    
    def generate_sar_report(self, transaction: Dict, similar_cases: List[Dict], investigation_summary: str) -> str:
        """Generate SAR report using LLM"""
        if self.use_local:
            prompt = self._create_sar_prompt(transaction, similar_cases, investigation_summary)
            return self._call_llm(prompt)
        else:
            return self._template_sar(transaction, similar_cases)
    
    def answer_question(self, question: str, transaction: Dict, similar_cases: List[Dict]) -> str:
        """Answer questions using LLM"""
        if self.use_local:
            prompt = self._create_qa_prompt(question, transaction, similar_cases)
            return self._call_llm(prompt)
        else:
            return self._template_answer(question, transaction, similar_cases)
    
    def _call_llm(self, prompt: str) -> str:
        """Call Phi-2 LLM with proper formatting"""
        try:
            formatted_prompt = f"Instruct: {prompt}\nOutput:"
            
            response = self.llm(
                formatted_prompt,
                max_tokens=200,
                temperature=0.3,
                top_p=0.9,
                stop=["Instruct:", "\n\n", "Output:", "<|endoftext|>"],
                echo=False
            )
            
            result = response['choices'][0]['text'].strip()
            result = result.replace("<|endoftext|>", "").strip()
            
            if result:
                return result
            else:
                print("⚠️ LLM returned empty, using template fallback")
                return self._template_summary({}, [])
                
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return self._template_summary({}, [])
    
    def _create_investigation_prompt(self, transaction: Dict, similar_cases: List[Dict]) -> str:
        """Create prompt for investigation summary - Phi-2 optimized"""
        
        amount = transaction.get('amount', 0)
        fraud_type = transaction.get('fraud_type', 'none')
        merchant = transaction.get('merchant_category', 'unknown')
        hour = transaction.get('hour_of_day', 0)
        
        if fraud_type == 'none' or fraud_type is None:
            return f"""Analyze this bank transaction and provide a brief fraud assessment.

Transaction details:
- Amount: ${amount:.2f}
- Merchant: {merchant}
- Time: {hour}:00
- Fraud indicators: None detected

Provide a 1-sentence assessment of the transaction."""

        cases_text = ""
        for i, case in enumerate(similar_cases[:2], 1):
            meta = case.get('metadata', {})
            cases_text += f"- Similar case {i}: ${float(meta.get('amount',0)):.2f} ({meta.get('fraud_type','unknown')})\n"
        
        return f"""Analyze this bank transaction for fraud and provide a brief assessment.

Transaction details:
- Amount: ${amount:.2f}
- Fraud type: {fraud_type}
- Merchant: {merchant}
- Time: {hour}:00

Similar historical fraud cases:
{cases_text}

Provide a 2-sentence assessment covering:
1. Why this transaction is suspicious
2. Recommended action (Block/Flag/Release)"""
    
    def _create_qa_prompt(self, question: str, transaction: Dict, similar_cases: List[Dict]) -> str:
        """Create prompt for Q&A"""
        
        amount = transaction.get('amount', 0)
        fraud_type = transaction.get('fraud_type', 'none')
        merchant = transaction.get('merchant_category', 'unknown')
        
        return f"""Answer this question about a bank transaction.

Transaction: ${amount:.2f} at {merchant}
Fraud type: {fraud_type}

Question: {question}

Provide a one-sentence answer:"""
    
    def _create_sar_prompt(self, transaction: Dict, similar_cases: List[Dict], summary: str) -> str:
        """Create prompt for SAR report"""
        
        amount = transaction.get('amount', 0)
        fraud_type = transaction.get('fraud_type', 'none')
        
        if fraud_type == 'none' or fraud_type is None:
            return "Legitimate transaction - No SAR needed."
        
        return f"""Write a one-sentence Suspicious Activity Report for a ${amount:.2f} {fraud_type} fraud transaction."""
    
    def _template_summary(self, transaction: Dict, similar_cases: List[Dict]) -> str:
        """Fallback template summary"""
        fraud_type = transaction.get('fraud_type', 'none')
        amount = transaction.get('amount', 0)
        merchant = transaction.get('merchant_category', 'unknown')
        
        if fraud_type == 'none' or fraud_type is None:
            return f"✅ LEGITIMATE: ${amount:.2f} at {merchant} - No fraud detected. LOW RISK. RELEASE."
        
        templates = {
            'structuring': f"🚨 FRAUD: Transaction ${amount:.2f} shows structuring pattern (just below $10k threshold). HIGH RISK. BLOCK.",
            'off_hours': f"🚨 FRAUD: Transaction ${amount:.2f} at off-hour is suspicious. HIGH RISK. BLOCK.",
            'amount_anomaly': f"🚨 FRAUD: Amount ${amount:.2f} is anomalous for this user. HIGH RISK. BLOCK.",
            'velocity': f"🚨 FRAUD: Unusual transaction frequency detected. HIGH RISK. BLOCK.",
            'location_mismatch': f"🚨 FRAUD: Geographic inconsistency detected. HIGH RISK. BLOCK."
        }
        return templates.get(fraud_type, f"🚨 FRAUD: Suspicious {fraud_type} transaction ${amount:.2f}. HIGH RISK. BLOCK.")
    
    def _template_sar(self, transaction: Dict, similar_cases: List[Dict]) -> str:
        """Fallback template SAR"""
        amount = transaction.get('amount', 0)
        fraud_type = transaction.get('fraud_type', 'none')
        
        if fraud_type == 'none' or fraud_type is None:
            return f"No SAR needed - Legitimate transaction ${amount:.2f}"
        
        return f"SAR: ${amount:.2f} {fraud_type} fraud detected. Transaction blocked for review."
    
    def _template_answer(self, question: str, transaction: Dict, similar_cases: List[Dict]) -> str:
        """Fallback template answer"""
        fraud_type = transaction.get('fraud_type', 'none')
        amount = transaction.get('amount', 0)
        
        if "why" in question.lower():
            if fraud_type == 'none' or fraud_type is None:
                return f"This is a legitimate transaction of ${amount:.2f}. No fraud detected."
            return f"This transaction was flagged for {fraud_type} fraud. Amount ${amount:.2f} shows suspicious pattern."
        elif "similar" in question.lower():
            return f"Found {len(similar_cases)} similar historical fraud cases."
        else:
            return f"{fraud_type.title() if fraud_type != 'none' else 'Legitimate'} transaction of ${amount:.2f}."

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING LLM INVESTIGATOR")
    print("=" * 60)
    
    llm = LLMInvestigator()
    
    test_transaction = {
        "transaction_id": "TEST-001",
        "amount": 9850.00,
        "fraud_type": "structuring",
        "merchant_category": "Other",
        "hour_of_day": 14,
    }
    
    print("\n🔍 Testing fraud transaction with LLM...")
    summary = llm.generate_investigation_summary(test_transaction, [])
    print(summary)