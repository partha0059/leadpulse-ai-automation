"""
LeadPulse AI - Sales Copilot & Executive KPI Analytics
Calculates pipeline metrics, conversion velocity, prospect dossiers, and next best actions.
"""
from typing import Dict, List
import pandas as pd
from core.database import get_connection
from core.llm_engine import generate_prospect_dossier

def get_executive_kpis() -> Dict:
    """Calculate core executive pipeline, deliverability, and conversion metrics."""
    conn = get_connection()

    # 1. Leads overview
    leads_df = pd.read_sql_query("SELECT * FROM leads", conn)
    companies_df = pd.read_sql_query("SELECT * FROM companies", conn)
    enrichments_df = pd.read_sql_query("SELECT * FROM contact_enrichments", conn)
    sequences_df = pd.read_sql_query("SELECT * FROM outreach_sequences", conn)
    wa_df = pd.read_sql_query("SELECT * FROM whatsapp_conversations", conn)

    total_leads = len(leads_df)
    total_companies = len(companies_df)

    # Lead Temperature Breakdown
    hot_leads = len(leads_df[leads_df["temperature"] == "Hot"]) if total_leads else 0
    warm_leads = len(leads_df[leads_df["temperature"] == "Warm"]) if total_leads else 0
    cold_leads = len(leads_df[leads_df["temperature"] == "Cold"]) if total_leads else 0

    # Deliverability rate
    deliverable_count = len(enrichments_df[enrichments_df["verification_status"] == "Deliverable"]) if len(enrichments_df) else 0
    verification_rate = round((deliverable_count / len(enrichments_df) * 100), 1) if len(enrichments_df) else 0

    # Approval Queue Counts
    pending_approvals = len(sequences_df[sequences_df["status"] == "Pending Review"]) if len(sequences_df) else 0
    approved_sequences = len(sequences_df[sequences_df["status"] == "Approved"]) if len(sequences_df) else 0

    # Pipeline Value Estimation ($15k average deal size per Hot lead, $8k per Warm)
    pipeline_value = (hot_leads * 25000) + (warm_leads * 12000)

    # WhatsApp Handover escalations
    handover_count = len(wa_df[wa_df["handover_requested"] == 1]) if len(wa_df) else 0
    opt_out_count = len(leads_df[leads_df["opt_out"] == 1]) if total_leads else 0

    conn.close()

    return {
        "total_leads": total_leads,
        "total_companies": total_companies,
        "hot_leads": hot_leads,
        "warm_leads": warm_leads,
        "cold_leads": cold_leads,
        "pipeline_value": f"${pipeline_value:,.0f}",
        "raw_pipeline_value": pipeline_value,
        "verification_rate": f"{verification_rate}%",
        "pending_approvals": pending_approvals,
        "approved_sequences": approved_sequences,
        "handover_count": handover_count,
        "opt_out_count": opt_out_count
    }

def get_lead_dossier(lead_id: int) -> Dict:
    """Fetch complete 360-degree sales intelligence profile for a selected lead."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT l.*, c.name as company_name, c.domain, c.industry, c.size, c.location, c.revenue_range, c.tech_stack, c.hiring_signal
    FROM leads l
    LEFT JOIN companies c ON l.company_id = c.id
    WHERE l.id = ?
    """, (lead_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {}

    lead = dict(row)
    company = {
        "name": lead.get("company_name", "Unknown"),
        "domain": lead.get("domain", ""),
        "industry": lead.get("industry", "Technology"),
        "size": lead.get("size", "N/A"),
        "location": lead.get("location", "N/A"),
        "revenue_range": lead.get("revenue_range", "N/A"),
        "tech_stack": lead.get("tech_stack", "Cloud"),
        "hiring_signal": lead.get("hiring_signal", "Scaling operations")
    }

    # Fetch verification
    cursor.execute("SELECT * FROM contact_enrichments WHERE lead_id = ? ORDER BY id DESC LIMIT 1", (lead_id,))
    enrichment = cursor.fetchone()
    enrich_dict = dict(enrichment) if enrichment else {}

    # Fetch sequences
    cursor.execute("SELECT * FROM outreach_sequences WHERE lead_id = ? ORDER BY step_number ASC", (lead_id,))
    seqs = [dict(r) for r in cursor.fetchall()]

    # Fetch WhatsApp chat
    cursor.execute("SELECT * FROM whatsapp_conversations WHERE lead_id = ? ORDER BY id ASC", (lead_id,))
    chats = [dict(r) for r in cursor.fetchall()]

    conn.close()

    ai_dossier = generate_prospect_dossier(lead, company)

    return {
        "lead": lead,
        "company": company,
        "enrichment": enrich_dict,
        "sequences": seqs,
        "chats": chats,
        "ai_dossier": ai_dossier
    }
