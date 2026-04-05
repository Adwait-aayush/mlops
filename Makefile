# ============================================================
#  MLOps Platform — Makefile
#  Run any command from the mlops-platform/ folder
# ============================================================

# Build all Docker images
build:
	docker compose build

# Run the full pipeline: ingest → train → start services
run:
	@echo "Running data ingestion..."
	docker compose run --rm ingestion
	@echo "✓ Ingestion complete"
	@echo ""
	@echo "Running model training..."
	docker compose run --rm training
	@echo "✓ Training complete"
	@echo ""
	@echo "Starting serving, monitoring, and frontend..."
	docker compose up -d serving monitoring frontend
	@echo "✓ Services started"
	@echo ""
	@echo "Waiting for services to be ready..."
	sleep 3
	@echo "🌐 Frontend: http://localhost:3000"
	@echo "🔮 Serving:  http://localhost:8000"
	@echo "📊 Monitor:  http://localhost:8001"

# Stop all running services
stop:
	docker compose down

# Show logs of all running services
logs:
	docker compose logs -f

# Show logs of one service  e.g: make logs-serving
logs-serving:
	docker compose logs -f serving

logs-monitoring:
	docker compose logs -f monitoring

# Run only ingestion
ingest:
	docker compose run --rm ingestion

# Run only training
train:
	docker compose run --rm training

# Test the serving API with a spam and a normal message
test:
	curl -X POST http://localhost:8000/predict \
		-H "Content-Type: application/json" \
		-d "{\"text\": \"Win a free iPhone now click here!!!\"}"
	@echo ""
	curl -X POST http://localhost:8000/predict \
		-H "Content-Type: application/json" \
		-d "{\"text\": \"The hockey game was amazing last night\"}"
	@echo ""

# Check health of serving and monitoring
health:
	@echo "--- Serving ---"
	curl http://localhost:8000/health
	@echo ""
	@echo "--- Monitoring ---"
	curl http://localhost:8001/status
	@echo ""

# Check model info
model-info:
	curl http://localhost:8000/model-info
	@echo ""

# Remove all containers and volumes — full reset
clean:
	docker compose down --rmi all --volumes --remove-orphans
	@echo "✓ Clean complete"

# Rebuild everything from scratch and run
rebuild: clean build run