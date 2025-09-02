up:
	docker compose up -d postgres minio temporal nats

worker:
	python services/orchestrator/worker.py

api:
	uvicorn services.api.main:app --reload --port 8080

kill:
	docker compose down -v