import streamlit as st
import requests
import json
from datetime import datetime
import mysql.connector
import os  # ← ADD THIS LINE
from config import DB_CONFIG

# Page configuration
st.set_page_config(
    page_title="AI Financial Fraud Investigator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better spacing and styling
st.markdown("""
<style>
    .main > div {
        padding: 0rem 1rem;
    }
    
    h1 {
        font-size: 2.2rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        font-size: 1.5rem !important;
        margin-top: 0rem !important;
        margin-bottom: 1rem !important;
    }
    
    h3 {
        font-size: 1.2rem !important;
        margin-top: 0rem !important;
        margin-bottom: 0.8rem !important;
    }
    
    [data-testid="stSidebar"] {
        padding-top: 1rem;
    }
    
    .stInfo {
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .stSuccess {
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .stWarning {
        padding: 0.3rem 0.5rem;
        margin: 0.3rem 0;
    }
    
    .streamlit-expanderHeader {
        font-size: 0.9rem;
    }
    
    .caption {
        color: #888;
        font-size: 0.8rem;
    }
    
    hr {
        margin: 1rem 0;
    }
    
    .transaction-button {
        width: 100%;
        text-align: left;
        padding: 8px 12px;
        margin: 4px 0;
        background-color: #f0f2f6;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-family: monospace;
        font-size: 12px;
    }
    
    .transaction-button:hover {
        background-color: #e0e2e6;
    }
</style>
""", unsafe_allow_html=True)

# API endpoint
# API endpoint - use environment variable or default
API_URL = os.getenv('API_URL', 'http://localhost:8002')
# Initialize session state
if 'investigation' not in st.session_state:
    st.session_state.investigation = None
if 'transaction_id' not in st.session_state:
    st.session_state.transaction_id = ""
if 'question_input' not in st.session_state:
    st.session_state.question_input = ""

# Function to fetch transactions from database
@st.cache_data(ttl=300)
def fetch_transactions(limit=20):
    """Fetch recent transactions from database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT transaction_id, amount, merchant_category, fraud_type, is_fraud
            FROM fact_transaction 
            ORDER BY transaction_timestamp DESC 
            LIMIT %s
        """, (limit,))
        
        transactions = cursor.fetchall()
        conn.close()
        
        # Convert Decimal to float for display
        for txn in transactions:
            if 'amount' in txn:
                txn['amount'] = float(txn['amount'])
        
        return transactions
    except Exception as e:
        st.error(f"Error fetching transactions: {e}")
        return []

# Title
st.title("🔍 AI Financial Fraud Investigator")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("### 📊 Investigation Dashboard")
    st.markdown("")
    
    # Transaction input - text box
    transaction_id = st.text_input(
        "**Enter Transaction ID:**",
        placeholder="Paste transaction ID here",
        value=st.session_state.transaction_id
    )
    
    st.markdown("")
    
    if transaction_id:
        if st.button("🔍 Start Investigation", type="primary", use_container_width=True):
            with st.spinner("🔎 Analyzing transaction..."):
                try:
                    response = requests.post(
                        f"{API_URL}/investigate",
                        json={"transaction_id": transaction_id},
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        st.session_state.investigation = response.json()
                        st.session_state.transaction_id = transaction_id
                        st.success("✅ Investigation complete!")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {response.status_code}")
                except Exception as e:
                    st.error(f"🔌 Connection error: {e}")
    
    st.markdown("---")
    st.markdown("### 📋 Select from Database")
    st.markdown("")
    
    # Fetch and display transactions from database
    transactions = fetch_transactions(15)
    
    if transactions:
        for txn in transactions:
            # Determine fraud indicator
            if txn['is_fraud']:
                fraud_badge = "🚨 FRAUD"
                badge_color = "#ff6b6b"
            else:
                fraud_badge = "✅ LEGIT"
                badge_color = "#51cf66"
            
            # Create button label
            short_id = txn['transaction_id'][:20] + "..."
            label = f"{short_id} | ${txn['amount']:.2f} | {txn['merchant_category']} | {fraud_badge}"
            
            # Display as button
            if st.button(label, key=txn['transaction_id'], use_container_width=True):
                st.session_state.transaction_id = txn['transaction_id']
                st.rerun()
    else:
        st.info("No transactions found")

# Main content area - Two columns
col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.markdown("### 🔬 Investigation Results")
    st.markdown("")
    
    if st.session_state.investigation:
        inv = st.session_state.investigation
        
        # Handle error case
        if 'error' in inv:
            st.error(f"❌ {inv['error']}")
        else:
            # Summary section
            st.markdown("**📝 Investigation Summary**")
            st.markdown("")
            summary_text = inv.get('summary', 'No summary available')
            st.markdown(f"{summary_text}")
            st.markdown("")
            
            # Recommendations (extracted from summary)
            st.markdown("**🎯 Recommendations**")
            st.markdown("")
            summary = inv.get('summary', '')
            recommendations = []
            
            if "BLOCK" in summary.upper():
                recommendations.append("🚫 Block transaction immediately")
            if "FLAG" in summary.upper():
                recommendations.append("⚠️ Flag for manual review by fraud analyst")
            if "REVIEW" in summary.upper():
                recommendations.append("🔍 Review transaction manually")
            if "CONTACT" in summary.upper():
                recommendations.append("📞 Contact cardholder for verification")
            if "HIGH" in summary.upper():
                recommendations.append("📈 High risk - prioritize investigation")
            
            if not recommendations:
                recommendations.append("📊 Monitor transaction for additional activity")
                recommendations.append("🔍 Review within 24 hours")
            
            for rec in recommendations:
                st.warning(rec)
            
            st.markdown("")
            
            # SAR Report - Collapsible
            with st.expander("📄 View SAR Report", expanded=False):
                st.code(inv.get('sar_report', 'No SAR report available'), language='text')
            
            st.markdown("")
            
            # Metadata
            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Similar cases found:** `{inv.get('similar_cases_count', 0)}`")
            with col_b:
                st.markdown(f"**Investigation time:** `{inv.get('timestamp', 'N/A')[:19]}`")
    
    else:
        st.info("💡 Enter a transaction ID or click one from the sidebar to start investigation")
        st.markdown("")
        st.markdown("""
        ### How it works:
        1. **Enter a transaction ID** in the sidebar, OR
        2. **Click on any transaction** from the list
        3. Review the AI-generated fraud analysis
        4. Ask specific questions about the transaction
        """)

with col2:
    st.markdown("### 💬 Ask Questions")
    st.markdown("")
    
    if st.session_state.investigation and 'error' not in st.session_state.investigation:
        # Question input with session state
        question = st.text_area(
            "**Your question:**",
            placeholder="e.g., Why was this transaction flagged?",
            value=st.session_state.question_input,
            height=80,
            key="question_area"
        )
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            ask_button = st.button("🔍 Ask", type="secondary", use_container_width=True)
        with col_btn2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.question_input = ""
                st.rerun()
        
        if ask_button and question:
            with st.spinner("💭 Analyzing..."):
                try:
                    response = requests.post(
                        f"{API_URL}/ask",
                        params={
                            "transaction_id": st.session_state.transaction_id,
                            "question": question
                        },
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.markdown("")
                        st.markdown("**✅ Answer:**")
                        st.markdown("")
                        st.info(data.get('answer', 'No answer available'))
                    else:
                        st.error(f"Error: {response.status_code}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        
        st.markdown("---")
        st.markdown("### 📌 Sample Questions")
        st.markdown("")
        
        # Sample questions as buttons that auto-fill
        sample_questions = [
            "Why was this transaction flagged?",
            "What similar fraud patterns exist?",
            "What action do you recommend?",
            "Is this transaction high risk?"
        ]
        
        for sq in sample_questions:
            if st.button(sq, key=sq, use_container_width=True):
                st.session_state.question_input = sq
                st.rerun()
    
    else:
        st.info("🔍 Complete an investigation first to ask questions")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888; font-size: 0.8rem; padding: 1rem;'>
    🔍 AI Financial Fraud Investigator | Powered by XGBoost, RAG, and Phi-2 LLM
    </div>
    """,
    unsafe_allow_html=True
)