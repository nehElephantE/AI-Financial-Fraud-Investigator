# 🔍 AI Financial Fraud Investigator

An end-to-end AI-powered fraud detection system with RAG (Retrieval-Augmented Generation) and LLM integration.

## 🚀 Quick Start for New Users

### Prerequisites
- Python 3.10+
- Docker Desktop (optional, for containerized deployment)
- 8GB RAM minimum (16GB recommended)

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/fraud-detection.git
cd fraud-detection

# Run complete setup (generates data, trains models, builds vector store)
make deploy-local

# Start the application
make run-all