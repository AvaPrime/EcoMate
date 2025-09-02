up:
	docker compose up -d postgres minio temporal nats

worker:
	python services/orchestrator/worker.py

api:
	uvicorn services.api.main:app --reload --port 8080

price-monitor:
	curl -X POST "http://localhost:8080/run/price-monitor" -H "Content-Type: application/json" -d '{"create_pr": true}'

kill:
	docker compose down -v