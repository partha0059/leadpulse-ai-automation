"""
LeadPulse AI - WhatsApp Cloud API Suite & Inbound BANT Qualification
Handles Meta webhook architecture, automated intent classification,
BANT evaluation, lead-temperature labels, human handover, and opt-out compliance.
"""
from typing import Dict, List, Optional
import datetime
import json
from core.database import get_connection
from core.llm_engine import analyze_whatsapp_intent_and_bant
from core.config import (
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_WABA_ID,
    WHATSAPP_VERIFY_TOKEN,
    WHATSAPP_API_VERSION
)

def verify_meta_webhook(mode: str, token: str, challenge: str) -> Optional[str]:
    """Verify incoming Meta WhatsApp webhook subscription challenge."""
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        return challenge
    return None

def process_inbound_whatsapp_message(
    phone_number: str,
    message_text: str,
    lead_id: Optional[int] = None
) -> Dict:
    """
    Process an inbound WhatsApp message:
    1. Check opt-out status
    2. Extract BANT qualification signals & intent
    3. Determine lead temperature & human handover
    4. Store message and response in SQLite conversation log
    5. Update Lead record (temperature, BANT score, opt-out flag)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Find or link lead by phone if lead_id not supplied
    if not lead_id:
        cursor.execute("SELECT id, opt_out FROM leads WHERE phone = ?", (phone_number,))
        lead_row = cursor.fetchone()
        if lead_row:
            lead_id = lead_row["id"]
            if lead_row["opt_out"]:
                # Already opted out
                conn.close()
                return {
                    "reply": "This number is currently unsubscribed from automated messages. Reply START to resubscribe.",
                    "status": "OPTED_OUT",
                    "handover": False
                }

    # Retrieve conversation history
    cursor.execute("""
    SELECT role, message, intent, timestamp 
    FROM whatsapp_conversations 
    WHERE phone_number = ? 
    ORDER BY id ASC
    """, (phone_number,))
    history = [dict(r) for r in cursor.fetchall()]

    # Analyze message with LLM engine
    analysis = analyze_whatsapp_intent_and_bant(message_text, history)

    # 1. Store incoming User message
    cursor.execute("""
    INSERT INTO whatsapp_conversations 
    (lead_id, phone_number, role, message, intent, bant_budget, bant_authority, bant_need, bant_timeline, handover_requested, is_opt_out)
    VALUES (?, ?, 'user', ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lead_id,
        phone_number,
        message_text,
        analysis["intent"],
        analysis["bant_budget"],
        analysis["bant_authority"],
        analysis["bant_need"],
        analysis["bant_timeline"],
        1 if analysis["handover_requested"] else 0,
        1 if analysis["is_opt_out"] else 0
    ))

    # 2. Store Assistant Response
    cursor.execute("""
    INSERT INTO whatsapp_conversations 
    (lead_id, phone_number, role, message, intent, bant_budget, bant_authority, bant_need, bant_timeline, handover_requested, is_opt_out)
    VALUES (?, ?, 'assistant', ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lead_id,
        phone_number,
        analysis["response"],
        analysis["intent"],
        analysis["bant_budget"],
        analysis["bant_authority"],
        analysis["bant_need"],
        analysis["bant_timeline"],
        1 if analysis["handover_requested"] else 0,
        1 if analysis["is_opt_out"] else 0
    ))

    # 3. Update Lead in CRM if lead_id is linked
    if lead_id:
        if analysis["is_opt_out"]:
            cursor.execute("UPDATE leads SET opt_out = 1, status = 'Closed-Lost', temperature = 'Cold' WHERE id = ?", (lead_id,))
        else:
            cursor.execute("""
            UPDATE leads 
            SET temperature = ?, bant_score = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (analysis["temperature"], analysis["bant_score"], lead_id))

    # Audit log
    cursor.execute("""
    INSERT INTO audit_logs (module, action, details)
    VALUES ('WhatsApp Suite', 'INBOUND_MESSAGE', ?)
    """, (f"Processed WhatsApp from {phone_number}. Intent: {analysis['intent']}. Handover: {analysis['handover_requested']}",))

    conn.commit()
    conn.close()

    return {
        "reply": analysis["response"],
        "intent": analysis["intent"],
        "temperature": analysis["temperature"],
        "bant_score": analysis["bant_score"],
        "handover_requested": analysis["handover_requested"],
        "is_opt_out": analysis["is_opt_out"],
        "bant_breakdown": {
            "Budget": analysis["bant_budget"],
            "Authority": analysis["bant_authority"],
            "Need": analysis["bant_need"],
            "Timeline": analysis["bant_timeline"]
        }
    }

def get_conversations_for_phone(phone_number: str) -> List[Dict]:
    """Retrieve full conversation transcript for a given telephone number."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM whatsapp_conversations 
    WHERE phone_number = ? 
    ORDER BY id ASC
    """, (phone_number,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_whatsapp_threads() -> List[Dict]:
    """Retrieve unique active WhatsApp lead conversation threads with latest status."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT w.phone_number, w.lead_id, l.first_name, l.last_name, c.name as company_name,
           w.intent, w.handover_requested, w.is_opt_out, MAX(w.timestamp) as last_activity,
           COUNT(w.id) as message_count, l.temperature, l.bant_score
    FROM whatsapp_conversations w
    LEFT JOIN leads l ON w.lead_id = l.id
    LEFT JOIN companies c ON l.company_id = c.id
    GROUP BY w.phone_number
    ORDER BY last_activity DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
