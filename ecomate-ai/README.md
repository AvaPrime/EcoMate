# ecomate-ai

Agent services for EcoMate: research, supplier sync, price monitor, spec drafting, and compliance checks.

## Quickstart
```bash
# 1) clone & env
cp .env.example .env
# fill values in .env (OLLAMA_URL, GH_TOKEN, MINIO creds, etc.)

# 2) bring up infra
docker compose up -d postgres minio temporal nats

# 3) install local deps for worker & api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 4) start a Temporal worker
python services/orchestrator/worker.py

# 5) start the API (triggers workflows)
uvicorn services.api.main:app --reload --port 8080
```

## Temporal Web & MinIO
- Temporal Web UI: http://localhost:8088
- MinIO Console: http://localhost:9001 (user/pass from `.env`)

## Trigger a sample research run
```bash
curl -X POST 'http://localhost:8080/run/research' \
  -H 'Content-Type: application/json' \
  -d '{"query":"domestic MBBR package South Africa","limit":5}'
```

## PR to docs repo
Set `GH_TOKEN` (PAT with repo scope) and `DOCS_REPO=YOUR_GH_ORG/ecomate-docs`. The demo activity writes `data/suppliers.csv` and opens a PR.