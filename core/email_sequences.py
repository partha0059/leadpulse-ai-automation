"""
LeadPulse AI - 3-Step Outreach Sequence Engine & Human Approval Queue
Manages multi-touch personalized sequences, queue moderation, and dispatch scheduling.
"""
from typing import List, Dict, Optional
import datetime
from core.database import get_connection
from core.llm_engine import generate_personalized_sequence

def get_sequences_for_lead(lead_id: int) -> List[Dict]:
    """Retrieve all 3-step sequence messages for a specific lead."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT s.*, l.first_name, l.last_name, l.email, c.name as company_name
    FROM outreach_sequences s
    JOIN leads l ON s.lead_id = l.id
    LEFT JOIN companies c ON l.company_id = c.id
    WHERE s.lead_id = ?
    ORDER BY s.step_number ASC
    """, (lead_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_approval_queue(status_filter: Optional[str] = "Pending Review") -> List[Dict]:
    """Fetch outreach sequences waiting in the Human Approval Queue."""
    conn = get_connection()
    cursor = conn.cursor()
    if status_filter and status_filter != "All Statuses":
        cursor.execute("""
        SELECT s.*, l.first_name, l.last_name, l.email, l.title, c.name as company_name, c.industry
        FROM outreach_sequences s
        JOIN leads l ON s.lead_id = l.id
        LEFT JOIN companies c ON l.company_id = c.id
        WHERE s.status = ?
        ORDER BY s.id DESC
        """, (status_filter,))
    else:
        cursor.execute("""
        SELECT s.*, l.first_name, l.last_name, l.email, l.title, c.name as company_name, c.industry
        FROM outreach_sequences s
        JOIN leads l ON s.lead_id = l.id
        LEFT JOIN companies c ON l.company_id = c.id
        ORDER BY s.id DESC
        """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def update_sequence_status(sequence_id: int, new_status: str, notes: str = "", custom_subject: str = None, custom_body: str = None):
    """
    Approve, reject, or edit an outreach email in the queue.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    UPDATE outreach_sequences 
    SET status = ?, review_notes = ?, approved_at = CASE WHEN ? = 'Approved' THEN CURRENT_TIMESTAMP ELSE approved_at END
    """
    params = [new_status, notes, new_status]

    if custom_subject is not None:
        query += ", subject = ?"
        params.append(custom_subject)
    if custom_body is not None:
        query += ", body = ?"
        params.append(custom_body)

    query += " WHERE id = ?"
    params.append(sequence_id)

    cursor.execute(query, tuple(params))

    # Log audit event
    cursor.execute("""
    INSERT INTO audit_logs (module, action, details)
    VALUES ('Outreach Queue', 'STATUS_UPDATE', ?)
    """, (f"Sequence #{sequence_id} marked as '{new_status}'. Notes: {notes}",))

    conn.commit()
    conn.close()

def generate_full_sequence_for_lead(lead_id: int) -> int:
    """
    Generate all 3 steps for a lead if they don't already exist.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get lead & company details
    cursor.execute("""
    SELECT l.*, c.name as company_name, c.domain, c.industry, c.tech_stack, c.hiring_signal
    FROM leads l
    LEFT JOIN companies c ON l.company_id = c.id
    WHERE l.id = ?
    """, (lead_id,))
    lead_row = cursor.fetchone()
    if not lead_row:
        conn.close()
        return 0

    lead = dict(lead_row)
    company = {
        "name": lead.get("company_name", "Target Company"),
        "domain": lead.get("domain", ""),
        "industry": lead.get("industry", "Technology"),
        "tech_stack": lead.get("tech_stack", "Cloud"),
        "hiring_signal": lead.get("hiring_signal", "expanding headcount")
    }

    # Check existing steps
    cursor.execute("SELECT step_number FROM outreach_sequences WHERE lead_id = ?", (lead_id,))
    existing_steps = {r[0] for r in cursor.fetchall()}

    created_count = 0
    now = datetime.datetime.now()

    for step in [1, 2, 3]:
        if step in existing_steps:
            continue
        data = generate_personalized_sequence(lead, company, step)
        
        # Stagger scheduled dates
        sched_time = now + datetime.timedelta(days=(step - 1) * 3)
        sched_str = sched_time.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO outreach_sequences (lead_id, step_number, subject, body, status, scheduled_at)
        VALUES (?, ?, ?, ?, 'Pending Review', ?)
        """, (lead_id, step, data["subject"], data["body"], sched_str))
        created_count += 1

    conn.commit()
    conn.close()
    return created_count
