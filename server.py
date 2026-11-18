"""
LeadPulse AI - FastAPI Web Server & REST API Backend
Serves professional multi-page HTML/CSS/JS frontend and exposes full REST APIs
for Market Discovery, Contact Enrichment, Local CRM, HubSpot Adapter,
3-Step Email Approval Queue, WhatsApp Cloud Webhooks, and Sales Copilot.
"""
import io
import csv
import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.config import (
    APP_NAME, APP_TAGLINE, APP_VERSION,
    WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_WABA_ID, WHATSAPP_VERIFY_TOKEN, WHATSAPP_API_VERSION
)
from core.database import get_connection, init_db, seed_sample_data
from core.contact_enrichment import verify_and_enrich_contact, generate_email_patterns
from core.market_research import search_discovery_catalog, import_discovered_company
from core.email_sequences import get_approval_queue, update_sequence_status, generate_full_sequence_for_lead
from core.whatsapp_engine import (
    verify_meta_webhook, process_inbound_whatsapp_message,
    get_conversations_for_phone, get_all_whatsapp_threads
)
from core.hubspot_adapter import sync_lead_to_hubspot, get_hubspot_sync_history
from core.sales_copilot import get_executive_kpis, get_lead_dossier
from core.llm_engine import get_active_model_name

# Initialize database & sample enterprise dataset
init_db()
seed_sample_data()

app = FastAPI(
    title=f"{APP_NAME} API",
    description=APP_TAGLINE,
    version=APP_VERSION
)

WEB_DIR = BASE_DIR / "web"
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")


def serve_html(filename: str) -> HTMLResponse:
    html_path = WEB_DIR / filename
    if not html_path.exists():
        raise HTTPException(status_code=404, detail=f"Page {filename} not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ==========================================
# HTML PAGE ROUTES
# ==========================================
@app.get("/", response_class=HTMLResponse)
def page_dashboard():
    return serve_html("index.html")

@app.get("/discovery", response_class=HTMLResponse)
def page_discovery():
    return serve_html("discovery.html")

@app.get("/enrichment", response_class=HTMLResponse)
def page_enrichment():
    return serve_html("enrichment.html")

@app.get("/crm", response_class=HTMLResponse)
def page_crm():
    return serve_html("crm.html")

@app.get("/sequences", response_class=HTMLResponse)
def page_sequences():
    return serve_html("sequences.html")

@app.get("/whatsapp", response_class=HTMLResponse)
def page_whatsapp():
    return serve_html("whatsapp.html")

@app.get("/copilot", response_class=HTMLResponse)
def page_copilot():
    return serve_html("copilot.html")

@app.get("/architecture", response_class=HTMLResponse)
def page_architecture():
    return serve_html("architecture.html")


# ==========================================
# REQUEST MODELS
# ==========================================
class VerifyEmailRequest(BaseModel):
    email: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""

class PatternRequest(BaseModel):
    first_name: str
    last_name: str
    domain: str

class ImportCompanyRequest(BaseModel):
    name: str

class NewLeadRequest(BaseModel):
    first_name: str
    last_name: str
    title: str
    email: str
    phone: Optional[str] = ""
    company_name: str
    domain: Optional[str] = ""
    industry: Optional[str] = "Technology"

class SequenceReviewRequest(BaseModel):
    status: str
    subject: Optional[str] = None
    body: Optional[str] = None
    review_notes: Optional[str] = ""

class WhatsAppSimRequest(BaseModel):
    phone_number: str
    message: str
    lead_id: Optional[int] = None

class HubSpotSyncRequest(BaseModel):
    token: Optional[str] = None


# ==========================================
# 1. EXECUTIVE DASHBOARD & KPIs
# ==========================================
@app.get("/api/kpis")
def api_kpis():
    kpis = get_executive_kpis()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT status, COUNT(*) as count FROM leads GROUP BY status")
    funnel = [dict(r) for r in cur.fetchall()]

    cur.execute("""
    SELECT l.id, l.first_name, l.last_name, l.title, l.email, l.temperature, l.lead_score, l.bant_score, l.status, c.name as company_name
    FROM leads l
    LEFT JOIN companies c ON l.company_id = c.id
    ORDER BY l.lead_score DESC LIMIT 5
    """)
    top_leads = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT timestamp, module, action, details FROM audit_logs ORDER BY id DESC LIMIT 10")
    audit_logs = [dict(r) for r in cur.fetchall()]
    conn.close()

    return {
        "kpis": kpis,
        "funnel": funnel,
        "top_leads": top_leads,
        "audit_logs": audit_logs,
        "model": get_active_model_name(),
        "version": APP_VERSION
    }


# ==========================================
# 2. MARKET RESEARCH & COMPANY DISCOVERY
# ==========================================
@app.get("/api/discovery")
def api_discovery(
    industry: Optional[str] = Query(default="All Industries"),
    size: Optional[str] = Query(default="All Sizes"),
    q: Optional[str] = Query(default="")
):
    results = search_discovery_catalog(industry, size, q)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT LOWER(name) as name FROM companies")
    existing = {r["name"] for r in cur.fetchall()}
    conn.close()

    enriched = []
    for item in results:
        copy = dict(item)
        copy["already_imported"] = item["name"].lower() in existing
        enriched.append(copy)

    return {"count": len(enriched), "companies": enriched}


@app.post("/api/discovery/import")
def api_discovery_import(payload: ImportCompanyRequest):
    matches = search_discovery_catalog(query=payload.name)
    target = next((c for c in matches if c["name"].lower() == payload.name.lower()), None)
    if not target:
        raise HTTPException(status_code=404, detail="Company not found in discovery catalog")
    company_id = import_discovered_company(target)
    return {"success": True, "company_id": company_id, "message": f"Imported {target['name']} and decision makers into CRM."}


# ==========================================
# 3. CONTACT ENRICHMENT & DNS/MX VERIFIER
# ==========================================
@app.post("/api/enrichment/verify")
def api_enrichment_verify(payload: VerifyEmailRequest):
    result = verify_and_enrich_contact(payload.email, payload.first_name or "", payload.last_name or "")
    return result


@app.post("/api/enrichment/patterns")
def api_enrichment_patterns(payload: PatternRequest):
    patterns = generate_email_patterns(payload.first_name, payload.last_name, payload.domain)
    return {"patterns": patterns}


@app.get("/api/enrichment/history")
def api_enrichment_history():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT e.*, l.first_name, l.last_name, l.email, c.name as company_name
    FROM contact_enrichments e
    JOIN leads l ON e.lead_id = l.id
    LEFT JOIN companies c ON l.company_id = c.id
    ORDER BY e.id DESC LIMIT 30
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"history": rows}


# ==========================================
# 4. CRM PIPELINE & HUBSPOT SYNC
# ==========================================
@app.get("/api/crm/leads")
def api_crm_leads(
    q: Optional[str] = Query(default=""),
    temperature: Optional[str] = Query(default="All"),
    status: Optional[str] = Query(default="All")
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT l.*, c.name as company_name, c.domain, c.industry, c.location
    FROM leads l
    LEFT JOIN companies c ON l.company_id = c.id
    ORDER BY l.id DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    filtered = []
    q_low = (q or "").strip().lower()
    for r in rows:
        if temperature and temperature != "All" and r["temperature"] != temperature:
            continue
        if status and status != "All" and r["status"] != status:
            continue
        if q_low:
            hay = f"{r['first_name']} {r['last_name']} {r['title']} {r['email']} {r.get('company_name', '')}".lower()
            if q_low not in hay:
                continue
        filtered.append(r)

    return {"count": len(filtered), "leads": filtered}


@app.post("/api/crm/leads")
def api_crm_add_lead(payload: NewLeadRequest):
    conn = get_connection()
    cur = conn.cursor()

    # Create or find company
    domain = payload.domain or (payload.email.split("@")[-1] if "@" in payload.email else "company.com")
    cur.execute("SELECT id FROM companies WHERE LOWER(name) = ?", (payload.company_name.lower(),))
    comp = cur.fetchone()
    if comp:
        comp_id = comp["id"]
    else:
        cur.execute("""
        INSERT INTO companies (name, domain, industry, size, location, revenue_range, tech_stack, hiring_signal)
        VALUES (?, ?, ?, '50-250', 'United States', '$10M-$25M', 'Cloud, Python', 'Active expansion')
        """, (payload.company_name, domain, payload.industry or "Technology"))
        comp_id = cur.lastrowid

    try:
        cur.execute("""
        INSERT INTO leads (company_id, first_name, last_name, title, email, phone, status, lead_score, temperature)
        VALUES (?, ?, ?, ?, ?, ?, 'New', 65, 'Warm')
        """, (comp_id, payload.first_name, payload.last_name, payload.title, payload.email, payload.phone))
        lead_id = cur.lastrowid
        cur.execute("""
        INSERT INTO audit_logs (module, action, details)
        VALUES ('CRM Pipeline', 'CREATE_LEAD', ?)
        """, (f"Added prospect {payload.first_name} {payload.last_name} ({payload.email}) at {payload.company_name}",))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Could not create lead (email may already exist): {e}")

    conn.close()
    return {"success": True, "lead_id": lead_id}


@app.get("/api/crm/export")
def api_crm_export():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT l.id, l.first_name, l.last_name, l.title, c.name as company, l.email, l.phone,
           l.status, l.temperature, l.lead_score, l.bant_score, l.hubspot_id, l.opt_out
    FROM leads l
    LEFT JOIN companies c ON l.company_id = c.id
    ORDER BY l.id DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leadpulse_crm_export.csv"}
    )


@app.post("/api/hubspot/sync/{lead_id}")
def api_hubspot_sync(lead_id: int, payload: Optional[HubSpotSyncRequest] = None):
    custom_token = payload.token if payload else None
    result = sync_lead_to_hubspot(lead_id, custom_token=custom_token)
    return result


@app.get("/api/hubspot/logs")
def api_hubspot_logs():
    return {"logs": get_hubspot_sync_history()}


# ==========================================
# 5. 3-STEP OUTREACH SEQUENCES & APPROVAL QUEUE
# ==========================================
@app.get("/api/sequences")
def api_sequences(status: Optional[str] = Query(default="All Statuses")):
    items = get_approval_queue(status)
    return {"count": len(items), "sequences": items}


@app.post("/api/sequences/generate/{lead_id}")
def api_sequences_generate(lead_id: int):
    created = generate_full_sequence_for_lead(lead_id)
    return {"success": True, "created_count": created}


@app.post("/api/sequences/{seq_id}/review")
def api_sequences_review(seq_id: int, payload: SequenceReviewRequest):
    if payload.status not in ["Approved", "Rejected", "Pending Review", "Sent"]:
        raise HTTPException(status_code=400, detail="Invalid review status")
    update_sequence_status(
        sequence_id=seq_id,
        new_status=payload.status,
        notes=payload.review_notes or "",
        custom_subject=payload.subject,
        custom_body=payload.body
    )
    return {"success": True, "sequence_id": seq_id, "status": payload.status}


# ==========================================
# 6. WHATSAPP CLOUD API & BANT SIMULATOR
# ==========================================
@app.get("/api/whatsapp/threads")
def api_whatsapp_threads():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT l.id, l.first_name, l.last_name, l.title, l.phone, l.temperature, l.bant_score, l.opt_out, c.name as company_name
    FROM leads l
    LEFT JOIN companies c ON l.company_id = c.id
    WHERE l.phone IS NOT NULL AND l.phone != ''
    ORDER BY l.lead_score DESC
    """)
    contacts = [dict(r) for r in cur.fetchall()]
    conn.close()
    threads = get_all_whatsapp_threads()
    return {"contacts": contacts, "threads": threads}


@app.get("/api/whatsapp/messages")
def api_whatsapp_messages(phone: str = Query(...)):
    messages = get_conversations_for_phone(phone)
    return {"phone": phone, "messages": messages}


@app.post("/api/whatsapp/simulate")
def api_whatsapp_simulate(payload: WhatsAppSimRequest):
    result = process_inbound_whatsapp_message(
        phone_number=payload.phone_number,
        message_text=payload.message,
        lead_id=payload.lead_id
    )
    return result


@app.get("/webhooks/whatsapp")
def meta_webhook_verify(
    hub_mode: Optional[str] = Query(default=None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(default=None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(default=None, alias="hub.challenge")
):
    challenge = verify_meta_webhook(hub_mode or "", hub_verify_token or "", hub_challenge or "")
    if challenge:
        return PlainTextResponse(content=challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Webhook verification failed: invalid token")


@app.post("/webhooks/whatsapp")
async def meta_webhook_receive(request: Request):
    body = await request.json()
    try:
        entries = body.get("entry", [])
        processed = []
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    phone = msg.get("from", "unknown")
                    text = msg.get("text", {}).get("body", "")
                    if text:
                        res = process_inbound_whatsapp_message(phone, text)
                        processed.append({"phone": phone, "intent": res.get("intent")})
        return {"status": "received", "processed": processed}
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "ignored", "detail": str(e)})


# ==========================================
# 7. SALES COPILOT & DOSSIERS
# ==========================================
@app.get("/api/copilot/dossier/{lead_id}")
def api_copilot_dossier(lead_id: int):
    dossier = get_lead_dossier(lead_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Lead not found")
    return dossier


# ==========================================
# 8. SYSTEM CONFIGURATION & ARCHITECTURE
# ==========================================
@app.get("/api/config")
def api_config():
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "active_model": get_active_model_name(),
        "whatsapp": {
            "phone_number_id": WHATSAPP_PHONE_NUMBER_ID,
            "waba_id": WHATSAPP_WABA_ID,
            "verify_token": WHATSAPP_VERIFY_TOKEN,
            "api_version": WHATSAPP_API_VERSION,
            "webhook_url": "/webhooks/whatsapp"
        },
        "integrations": {
            "sqlite": "Connected (7 relational tables)",
            "hubspot": "Live Token" if os.environ.get("HUBSPOT_ACCESS_TOKEN") else "Enterprise Sandbox Mode",
            "llm": get_active_model_name(),
            "whatsapp_webhook": "Active & Verified"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
