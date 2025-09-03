up:
	docker compose up -d postgres minio temporal nats

worker:
	python services/orchestrator/worker.py

api:
	uvicorn services.api.main:app --reload --port 8080

price-monitor:
	curl -X POST "http://localhost:8080/run/price-monitor" -H "Content-Type: application/json" -d '{"create_pr": true}'

research:
	curl -X POST "http://localhost:8080/run/new-research" -H "Content-Type: application/json" -d '{"urls": ["https://example.com/suppliers", "https://example.com/parts"]}'

# New service endpoints
proposal:
	curl -X POST "http://localhost:8080/proposal/build" -H "Content-Type: application/json" -d '{"system_id": "test-system", "components": ["pump", "filter", "uv-sterilizer"]}'

catalog-sync:
	curl -X POST "http://localhost:8080/catalog/sync" -H "Content-Type: application/json" -d '{"source": "shopify"}'

maintenance-plan:
	curl -X POST "http://localhost:8080/maintenance/plan" -H "Content-Type: application/json" -d '{"system_id": "test-system"}'

compliance-check:
	curl -X POST "http://localhost:8080/compliance/check" -H "Content-Type: application/json" -d '{"system_id": "test-system", "rules": ["sans_water"]}'

telemetry-ingest:
	curl -X POST "http://localhost:8080/telemetry/ingest" -H "Content-Type: application/json" -d '{"system_id": "test-system", "metrics": {"flow_m3h": 12.5, "uv_dose_mj_cm2": 35.0}}'

kill:
	docker compose down -v