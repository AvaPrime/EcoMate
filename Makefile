PY=python
PIP=$(PY) -m pip
VENv=.venv

init:
	$(PY) -m venv .venv && . .venv/bin/activate && $(PIP) install -r requirements.txt

serve:
	mkdocs serve

build:
	mkdocs build --strict

pdf:
	mkdocs build
	@echo "PDF at site/pdf/ecomate-docs.pdf"

# Requires pandoc installed locally
DOCX_OUT=exports
DOCX_FILES= \
	docs/products/wastewater/overview.md \
	docs/products/wastewater/technical-spec.md \
	docs/products/wastewater/installation-guide.md \
	docs/products/wastewater/maintenance-schedule.md \
	docs/products/wastewater/compliance.md

docx:
	mkdir -p $(DOCX_OUT)
	for f in $(DOCX_FILES); do \
	  base=$$(basename $$f .md); \
	  pandoc $$f -o $(DOCX_OUT)/$$base.docx; \
	done