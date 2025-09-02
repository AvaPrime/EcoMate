# EcoMate — Docs as Code

This repository holds EcoMate's product, ops, and GTM documentation in Markdown. Built with **MkDocs Material**, published to **GitHub Pages**, with optional PDF/Word exports for client packs.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve  # http://127.0.0.1:8000
```

## Deploy
Push to `main`; GitHub Actions builds and deploys to Pages.

## Exports
- PDF: `make pdf`
- DOCX (via pandoc): `make docx` (then upload to Google Drive)

## Data → Google Sheets
Keep tabular data in `data/*.csv`. Import into Google Sheets (File > Import) or use the Apps Script example in `scripts/google_sheets_sync_example.gs` to pull CSV from GitHub on a schedule.