# AI Financial Fraud Investigator - Makefile

.PHONY: help build up down restart logs clean

# Colors
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

help:
	@echo "$(GREEN)AI Financial Fraud Investigator$(NC)"
	@echo ""
	@echo "  $(YELLOW)make build$(NC)     - Build Docker images"
	@echo "  $(YELLOW)make up$(NC)        - Start all containers"
	@echo "  $(YELLOW)make down$(NC)      - Stop all containers"
	@echo "  $(YELLOW)make restart$(NC)   - Restart all containers"
	@echo "  $(YELLOW)make logs$(NC)      - View container logs"
	@echo "  $(YELLOW)make clean$(NC)     - Remove containers and volumes"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "$(GREEN)✅ Containers started!$(NC)"
	@echo "   UI: http://localhost:8501"
	@echo "   API: http://localhost:8002/docs"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f