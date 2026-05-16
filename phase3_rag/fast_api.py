from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
from typing import Optional
import uvicorn
import json
from datetime import datetime

# Fix import - remove 'phase3_rag.' prefix
from fast_investigator import FastInvestigator

app = FastAPI(title="Fast Fraud Investigation API")
investigator = FastInvestigator()

class InvestigateRequest(BaseModel):
    transaction_id: str
    stream: bool = False

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/investigate")
async def investigate(request: InvestigateRequest):
    """Investigate transaction with optional streaming"""
    
    if request.stream:
        async def generate():
            result = investigator.investigate(request.transaction_id)
            for chunk in result['summary'].split('. '):
                yield f"data: {json.dumps({'chunk': chunk + '.'})}\n\n"
                await asyncio.sleep(0.1)
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        result = investigator.investigate(request.transaction_id)
        return result

@app.post("/clear-cache")
async def clear_cache():
    """Clear all caches"""
    investigator.clear_cache()
    return {"status": "Cache cleared"}

@app.post("/ask")
async def ask_question(transaction_id: str, question: str):
    """Ask a specific question about a transaction"""
    try:
        transaction = investigator._get_transaction_cached(transaction_id)
        if not transaction:
            return {"error": "Transaction not found"}
        
        similar_cases = investigator.rag.retrieve_similar_cases(transaction)
        answer = investigator.llm.answer_question(question, transaction, similar_cases)
        
        return {
            "transaction_id": transaction_id,
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("=" * 60)
    print("STARTING FAST FRAUD INVESTIGATION API")
    print("=" * 60)
    print(f"API: http://localhost:8002")
    print(f"Docs: http://localhost:8002/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8002)