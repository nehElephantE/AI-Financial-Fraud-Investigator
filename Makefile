# ============================================
# AI Financial Fraud Investigator - Makefile
# ============================================
# Usage: make <command>
# ============================================

.PHONY: help setup init-db data train vector run-api run-ui run-all
.PHONY: docker-build docker-run docker-stop docker-restart docker-clean docker-logs docker-shell
.PHONY: deploy-local deploy-docker deploy-aws
.PHONY: status test clean quickstart

# Colors for output
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# ============================================
# HELP
# ============================================

help:
	@echo "$(GREEN)╔══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║     AI Financial Fraud Investigator - Commands               ║$(NC)"
	@echo "$(GREEN)╚══════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)📦 Setup & Installation$(NC)"
	@echo "  make setup          - Install all Python dependencies"
	@echo "  make init-db        - Start MySQL database only"
	@echo ""
	@echo "$(YELLOW)📊 Data & Training$(NC)"
	@echo "  make data           - Generate dummy transactions (Phase 1)"
	@echo "  make train          - Train ML models (Phase 2)"
	@echo "  make vector         - Build vector store (Phase 3)"
	@echo ""
	@echo "$(YELLOW)🚀 Run Services (Local)$(NC)"
	@echo "  make run-api        - Start FastAPI server (port 8002)"
	@echo "  make run-ui         - Start Streamlit UI (port 8501)"
	@echo "  make run-all        - Start both API and UI"
	@echo ""
	@echo "$(YELLOW)🐳 Docker Commands$(NC)"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-run     - Start all containers"
	@echo "  make docker-stop    - Stop all containers"
	@echo "  make docker-restart - Restart all containers"
	@echo "  make docker-clean   - Remove containers, volumes, and images"
	@echo "  make docker-logs    - View container logs"
	@echo "  make docker-shell   - Enter API container shell"
	@echo ""
	@echo "$(YELLOW)🚀 One-Click Deployment$(NC)"
	@echo "  make deploy-local   - Complete local setup (data + train + vector)"
	@echo "  make deploy-docker  - Complete Docker deployment"
	@echo "  make deploy-aws     - Deploy to AWS EC2"
	@echo ""
	@echo "$(YELLOW)🔧 Utilities$(NC)"
	@echo "  make status         - Check service status"
	@echo "  make test           - Run tests"
	@echo "  make clean          - Clean generated files"
	@echo "  make help           - Show this help"

# ============================================
# SETUP & INSTALLATION
# ============================================

setup:
	@echo "$(GREEN)📦 Installing Python dependencies...$(NC)"
	pip install -r phase1_ingestion/requirements.txt
	pip install -r phase2_models/requirements.txt
	pip install -r phase3_rag/requirements.txt
	@echo "$(GREEN)✅ Setup complete!$(NC)"

init-db:
	@echo "$(GREEN)🐳 Starting MySQL database...$(NC)"
	docker-compose up -d mysql
	@sleep 15
	@echo "$(GREEN)✅ Database ready!$(NC)"

# ============================================
# PHASE 1: DATA GENERATION
# ============================================

data: init-db
	@echo "$(GREEN)📊 Generating dummy transaction data...$(NC)"
	cd phase1_ingestion && python generate_transactions.py
	cd phase1_ingestion && python load_to_db.py
	@echo "$(GREEN)✅ Data generation complete!$(NC)"
	@echo "   Generated 10,000 transactions with 5% fraud rate"

# ============================================
# PHASE 2: MODEL TRAINING
# ============================================

train:
	@echo "$(GREEN)🤖 Training ML models...$(NC)"
	cd phase2_models && python feature_engineering.py
	cd phase2_models && python train_xgboost.py
	cd phase2_models && python train_isolation_forest.py
	@echo "$(GREEN)✅ Model training complete!$(NC)"

# ============================================
# PHASE 3: VECTOR STORE & RAG
# ============================================

vector:
	@echo "$(GREEN)🔍 Building vector store...$(NC)"
	cd phase3_rag && python fraud_cases_loader.py
	@echo "$(GREEN)✅ Vector store ready!$(NC)"

# ============================================
# RUN SERVICES (LOCAL)
# ============================================

run-api:
	@echo "$(GREEN)🚀 Starting FastAPI server...$(NC)"
	@echo "   API: $(BLUE)http://localhost:8002$(NC)"
	@echo "   Docs: $(BLUE)http://localhost:8002/docs$(NC)"
	cd phase3_rag && python fast_api.py

run-ui:
	@echo "$(GREEN)🎨 Starting Streamlit UI...$(NC)"
	@echo "   UI: $(BLUE)http://localhost:8501$(NC)"
	cd phase3_rag && streamlit run chat_ui.py --server.port=8501

run-all:
	@echo "$(GREEN)🚀 Starting all services...$(NC)"
	@make -j2 run-api run-ui

# ============================================
# DOCKER COMMANDS
# ============================================

docker-build:
	@echo "$(GREEN)🐳 Building Docker images...$(NC)"
	docker-compose build --no-cache
	@echo "$(GREEN)✅ Docker images built!$(NC)"

docker-run:
	@echo "$(GREEN)🐳 Starting Docker containers...$(NC)"
	docker-compose up -d
	@sleep 30
	@echo "$(GREEN)✅ All containers running!$(NC)"
	@echo ""
	@echo "   $(BLUE)UI:  http://localhost:8501$(NC)"
	@echo "   $(BLUE)API: http://localhost:8002$(NC)"
	@echo "   $(BLUE)Docs: http://localhost:8002/docs$(NC)"
	@echo ""
	@echo "Run '$(YELLOW)make docker-logs$(NC)' to view logs"

docker-stop:
	@echo "$(YELLOW)🛑 Stopping Docker containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Containers stopped!$(NC)"

docker-restart:
	@echo "$(YELLOW)🔄 Restarting Docker containers...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✅ Containers restarted!$(NC)"

docker-clean:
	@echo "$(RED)🧹 Cleaning Docker resources...$(NC)"
	@echo "Stopping containers..."
	docker-compose down -v
	@echo "Removing images..."
	docker rmi fraud-api fraud-ui 2>/dev/null || true
	@echo "Pruning system..."
	docker system prune -f
	@echo "$(GREEN)✅ Docker clean complete!$(NC)"

docker-logs:
	@echo "$(YELLOW)📋 Viewing logs (Ctrl+C to exit)...$(NC)"
	docker-compose logs -f

docker-shell:
	@echo "$(YELLOW)🐚 Entering API container shell...$(NC)"
	docker exec -it fraud_api /bin/bash

docker-rebuild:
	@echo "$(RED)🔄 Rebuilding and restarting containers...$(NC)"
	@make docker-clean
	@make docker-build
	@make docker-run
	@echo "$(GREEN)✅ Rebuild complete!$(NC)"

# ============================================
# ONE-CLICK DEPLOYMENT
# ============================================

deploy-local:
	@echo "$(GREEN)╔══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║                    LOCAL DEPLOYMENT                           ║$(NC)"
	@echo "$(GREEN)╚══════════════════════════════════════════════════════════════╝$(NC)"
	@make setup
	@make data
	@make train
	@make vector
	@echo ""
	@echo "$(GREEN)✅ Local deployment complete!$(NC)"
	@echo ""
	@echo "Run '$(YELLOW)make run-all$(NC)' to start the application"
	@echo "Or run services separately:"
	@echo "  Terminal 1: $(YELLOW)make run-api$(NC)"
	@echo "  Terminal 2: $(YELLOW)make run-ui$(NC)"

deploy-docker:
	@echo "$(GREEN)╔══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║                    DOCKER DEPLOYMENT                          ║$(NC)"
	@echo "$(GREEN)╚══════════════════════════════════════════════════════════════╝$(NC)"
	@make docker-build
	@make docker-run
	@echo ""
	@echo "$(GREEN)✅ Docker deployment complete!$(NC)"
	@echo ""
	@echo "Access your application:"
	@echo "  $(BLUE)UI:  http://localhost:8501$(NC)"
	@echo "  $(BLUE)API: http://localhost:8002/docs$(NC)"

deploy-aws:
	@echo "$(GREEN)╔══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║                    AWS EC2 DEPLOYMENT                         ║$(NC)"
	@echo "$(GREEN)╚══════════════════════════════════════════════════════════════╝$(NC)"
	chmod +x deploy_aws.sh
	./deploy_aws.sh

# ============================================
# UTILITIES
# ============================================

status:
	@echo "$(GREEN)📊 Service Status$(NC)"
	@echo "=================="
	@echo -n "$(YELLOW)MySQL: $(NC)"
	@docker ps --filter "name=fraud_mysql" --format "table {{.Status}}" | tail -n1 || echo "Not running"
	@echo -n "$(YELLOW)API: $(NC)"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/health 2>/dev/null || echo "Not running"
	@echo ""
	@echo -n "$(YELLOW)UI: $(NC)"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 2>/dev/null || echo "Not running"
	@echo ""
	@echo -n "$(YELLOW)Docker Containers: $(NC)"
	@docker-compose ps --services 2>/dev/null || echo "Not running"

test:
	@echo "$(GREEN)🧪 Running tests...$(NC)"
	cd phase2_models && python -c "import pandas as pd; print('✅ Phase 2 OK')"
	cd phase3_rag && python -c "import chromadb; print('✅ Phase 3 OK')"
	@echo "$(GREEN)✅ All tests passed!$(NC)"

clean:
	@echo "$(YELLOW)🧹 Cleaning generated files...$(NC)"
	rm -rf phase2_models/__pycache__
	rm -rf phase3_rag/__pycache__
	rm -rf phase3_rag/llm_cache
	rm -rf phase3_rag/transaction_cache
	rm -rf phase3_rag/chroma_db
	rm -f phase2_models/train_data.csv
	rm -f phase2_models/test_data.csv
	rm -f phase1_ingestion/transactions_raw.csv
	rm -f fraud-deploy.tar.gz
	@echo "$(GREEN)✅ Clean complete!$(NC)"

# ============================================
# QUICK START FOR NEW USERS
# ============================================

quickstart:
	@echo "$(GREEN)╔══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║                    QUICK START GUIDE                         ║$(NC)"
	@echo "$(GREEN)╚══════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "1. Clone the repository:"
	@echo "   $(YELLOW)git clone https://github.com/your-repo/fraud-detection.git$(NC)"
	@echo "   $(YELLOW)cd fraud-detection$(NC)"
	@echo ""
	@echo "2. Run one-click local deployment:"
	@echo "   $(YELLOW)make deploy-local$(NC)"
	@echo ""
	@echo "3. Start the application:"
	@echo "   $(YELLOW)make run-all$(NC)"
	@echo ""
	@echo "4. Open your browser:"
	@echo "   $(BLUE)http://localhost:8501$(NC)"
	@echo ""
	@echo "For Docker deployment:"
	@echo "   $(YELLOW)make deploy-docker$(NC)"
	@echo ""
	@echo "To rebuild everything:"
	@echo "   $(YELLOW)make docker-rebuild$(NC)"