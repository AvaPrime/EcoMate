from datetime import datetime, timezone
from services.utils.github_pr import open_pr
from services.utils.minio_store import put_bytes
from .models import ClientContext, SystemSpec, Assumptions
from .bom_engine import base_bom_for
from .cost_model import compute_quote
from .render import render_proposal_md, render_pdf_from_md

async def activity_build_proposal(client: dict, spec: dict, assumptions: dict):
    ctx = ClientContext(**client); sp = SystemSpec(**spec); ass = Assumptions(**assumptions)
    bom = base_bom_for(sp)
    quote = compute_quote(bom, distance_km=ass.distance_km)
    md = render_proposal_md(ctx, sp, quote)
    pdf = render_pdf_from_md(md)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    changes = {f"proposals/{today}_{ctx.name.replace(' ','_')}.md": md}
    if pdf:
        url = put_bytes('proposals/pdf', pdf, content_type='application/pdf')
        changes[f"proposals/{today}_{ctx.name.replace(' ','_')}.pdf.s3url"] = url
    open_pr(f"bot/proposal-{today}", f"Proposal: {ctx.name} ({today})", changes)
    return {"materials": quote.materials_subtotal, "total": quote.total_quote}