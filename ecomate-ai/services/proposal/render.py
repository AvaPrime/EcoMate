import os, subprocess, tempfile
from jinja2 import Template
from .models import ClientContext, SystemSpec, Quote

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates', 'proposal.md.j2')

def render_proposal_md(client: ClientContext, spec: SystemSpec, quote: Quote) -> str:
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        t = Template(f.read())
    return t.render(client=client.model_dump(), spec=spec.model_dump(), quote=quote.model_dump())

def render_pdf_from_md(md: str) -> bytes | None:
    # optional Pandoc export if available
    try:
        with tempfile.NamedTemporaryFile('w+', suffix='.md', delete=False) as tmp:
            tmp.write(md)
            tmp.flush()
            pdf_path = tmp.name.replace('.md', '.pdf')
        subprocess.check_call(['pandoc', tmp.name, '-o', pdf_path])
        with open(pdf_path, 'rb') as f:
            return f.read()
    except Exception:
        return None