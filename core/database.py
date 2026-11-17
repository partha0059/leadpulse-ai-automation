"""
LeadPulse AI - SQLite Database Layer & ORM Helpers
Provides schema initialization, seed data generation, and CRUD queries.
"""
import sqlite3
import datetime
import json
from pathlib import Path
from core.config import DB_PATH

def get_connection():
    """Return a connection to the SQLite database with row_factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create all required tables if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Companies Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        domain TEXT NOT NULL,
        industry TEXT NOT NULL,
        size TEXT,
        location TEXT,
        revenue_range TEXT,
        tech_stack TEXT,
        hiring_signal TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Leads Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        title TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        linkedin_url TEXT,
        status TEXT DEFAULT 'New', -- New, Enriched, Contacted, Qualified, Nurturing, Closed-Won, Closed-Lost
        lead_score INTEGER DEFAULT 50,
        temperature TEXT DEFAULT 'Warm', -- Hot, Warm, Cold
        bant_score INTEGER DEFAULT 0,
        opt_out INTEGER DEFAULT 0,
        hubspot_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies (id)
    );
    """)

    # 3. Contact Enrichments & Verification Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_enrichments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        email_pattern TEXT,
        syntax_valid INTEGER DEFAULT 1,
        domain_valid INTEGER DEFAULT 1,
        mx_records TEXT,
        score INTEGER DEFAULT 85,
        verification_status TEXT DEFAULT 'Deliverable', -- Deliverable, Risky, Invalid
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lead_id) REFERENCES leads (id)
    );
    """)

    # 4. Outreach Sequences & Human Approval Queue
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS outreach_sequences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        step_number INTEGER NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        status TEXT DEFAULT 'Pending Review', -- Pending Review, Approved, Rejected, Sent
        scheduled_at TIMESTAMP,
        approved_at TIMESTAMP,
        review_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lead_id) REFERENCES leads (id)
    );
    """)

    # 5. WhatsApp Conversations & Qualification Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS whatsapp_conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        phone_number TEXT NOT NULL,
        role TEXT NOT NULL, -- user, assistant, system
        message TEXT NOT NULL,
        intent TEXT,
        bant_budget TEXT,
        bant_authority TEXT,
        bant_need TEXT,
        bant_timeline TEXT,
        handover_requested INTEGER DEFAULT 0,
        is_opt_out INTEGER DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lead_id) REFERENCES leads (id)
    );
    """)

    # 6. HubSpot Sync Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hubspot_sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL, -- Contact, Company, Deal
        entity_id INTEGER NOT NULL,
        hubspot_id TEXT,
        sync_direction TEXT DEFAULT 'PUSH',
        sync_status TEXT DEFAULT 'SUCCESS', -- SUCCESS, FAILED, PENDING
        details TEXT,
        synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 7. Audit & Event Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

def seed_sample_data():
    """Populate database with rich, realistic enterprise B2B data if empty."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM companies")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return  # Already seeded

    # Seed Companies
    companies = [
        ("Apex Cloud Logistics", "apexlogistics.io", "Supply Chain & SaaS", "500-1000", "Chicago, IL", "$50M-$100M", "AWS, Snowflake, React, Python", "Hiring 12 Senior Cloud & DevOps Engineers"),
        ("NexaHealth Systems", "nexahealth.com", "HealthTech & MedDevice", "250-500", "Boston, MA", "$20M-$50M", "Azure, Kubernetes, C#, PostgreSQL", "Raised $28M Series B; expanding sales ops"),
        ("FinFlow Technologies", "finflow.ai", "FinTech & Payments", "100-250", "New York, NY", "$10M-$25M", "GCP, BigQuery, Node.js, Go", "Launching Cross-border Settlement Engine"),
        ("CyberShield Security", "cybershield.net", "Cybersecurity", "1000+", "San Jose, CA", "$150M+", "AWS, Terraform, Go, Elastic", "Acquired SentinelRisk; consolidating SOC stack"),
        ("DataSphere Analytics", "datasphere.co", "Data Infrastructure", "50-100", "Austin, TX", "$5M-$10M", "AWS, Databricks, Python, FastAPI", "New VP of Sales onboarded; scaling outbound"),
        ("HyperGrowth Media", "hypergrowth.agency", "AdTech & Performance Marketing", "50-100", "London, UK", "$10M-$20M", "HubSpot, Meta Graph, React", "Expanding AI content pipeline"),
        ("QuantIQ Systems", "quantiq.tech", "Algorithmic Trading & AI", "25-50", "Singapore", "$15M-$30M", "Rust, PyTorch, C++, Redis", "Hiring Machine Learning Infrastructure leads")
    ]

    cursor.executemany("""
    INSERT INTO companies (name, domain, industry, size, location, revenue_range, tech_stack, hiring_signal)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, companies)

    # Fetch company IDs
    cursor.execute("SELECT id, name, domain FROM companies")
    comp_map = {row["name"]: (row["id"], row["domain"]) for row in cursor.fetchall()}

    # Seed Leads
    leads = [
        (comp_map["Apex Cloud Logistics"][0], "Marcus", "Vance", "VP of Supply Chain Technology", "marcus.vance@apexlogistics.io", "+1 (312) 555-0192", "https://linkedin.com/in/marcus-vance-apex", "Qualified", 88, "Hot", 85, 0, "HS-CONT-10291"),
        (comp_map["Apex Cloud Logistics"][0], "Sarah", "Jenkins", "Director of IT Infrastructure", "s.jenkins@apexlogistics.io", "+1 (312) 555-0195", "https://linkedin.com/in/s-jenkins-cloud", "Contacted", 62, "Warm", 50, 0, None),
        (comp_map["NexaHealth Systems"][0], "Elena", "Rostova", "Chief Information Officer", "elena.rostova@nexahealth.com", "+1 (617) 555-0821", "https://linkedin.com/in/elena-rostova-cio", "Qualified", 94, "Hot", 90, 0, "HS-CONT-10304"),
        (comp_map["NexaHealth Systems"][0], "David", "Miller", "Head of Clinical Data Ops", "david@nexahealth.com", "+1 (617) 555-0824", "https://linkedin.com/in/david-miller-med", "Enriched", 58, "Warm", 40, 0, None),
        (comp_map["FinFlow Technologies"][0], "Arjun", "Mehta", "VP of Engineering & Architecture", "arjun.mehta@finflow.ai", "+1 (212) 555-0432", "https://linkedin.com/in/arjun-mehta-finflow", "Qualified", 82, "Hot", 80, 0, "HS-CONT-10319"),
        (comp_map["CyberShield Security"][0], "Rachel", "Stern", "Chief Technology Officer", "rachel.stern@cybershield.net", "+1 (408) 555-0911", "https://linkedin.com/in/rachel-stern-cto", "Contacted", 65, "Warm", 55, 0, None),
        (comp_map["DataSphere Analytics"][0], "Kavita", "Deshmukh", "Director of Business Intelligence", "kavita@datasphere.co", "+1 (512) 555-0677", "https://linkedin.com/in/kavita-bi-analytics", "New", 45, "Cold", 30, 0, None),
        (comp_map["HyperGrowth Media"][0], "Liam", "O'Connor", "Managing Director", "liam@hypergrowth.agency", "+44 20 7946 0192", "https://linkedin.com/in/liam-oconnor-agency", "Enriched", 71, "Warm", 60, 0, None),
        (comp_map["QuantIQ Systems"][0], "Chen", "Wei", "Head of Quantitative Strategy", "chen.wei@quantiq.tech", "+65 6789 0123", "https://linkedin.com/in/chen-wei-quantiq", "New", 78, "Hot", 75, 0, None)
    ]

    cursor.executemany("""
    INSERT INTO leads (company_id, first_name, last_name, title, email, phone, linkedin_url, status, lead_score, temperature, bant_score, opt_out, hubspot_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, leads)

    # Fetch created leads
    cursor.execute("SELECT id, first_name, email FROM leads")
    lead_rows = cursor.fetchall()
    lead_dict = {row["email"]: row["id"] for row in lead_rows}

    # Seed Contact Enrichments
    for row in lead_rows:
        lead_id = row["id"]
        cursor.execute("""
        INSERT INTO contact_enrichments (lead_id, email_pattern, syntax_valid, domain_valid, mx_records, score, verification_status)
        VALUES (?, 'first.last@domain', 1, 1, '10 mail.protection.outlook.com.', 95, 'Deliverable')
        """, (lead_id,))

    # Seed Outreach Sequences (3-step personalized sequences)
    sample_sequences = [
        # Lead 1: Marcus Vance
        (lead_dict["marcus.vance@apexlogistics.io"], 1, "Quick inquiry regarding Apex Cloud's logistics scaling",
         "Hi Marcus,\n\nNoticed Apex Cloud Logistics is aggressively scaling cloud engineering across Chicago. Fast growth typically strains multi-cloud data sync and warehouse SLA compliance.\n\nWe recently automated real-time dispatch verification for a Tier-1 3PL, eliminating 40 hours of manual reconciliation per week.\n\nOpen to a brief 10-minute preview on Thursday?\n\nBest,\nAlex Rivera\nLeadPulse BD Team",
         "Approved", "2026-11-18 10:00:00"),
        (lead_dict["marcus.vance@apexlogistics.io"], 2, "Re: Logistics pipeline automation case study for Marcus",
         "Hi Marcus,\n\nFollowing up on my previous note. Thought you'd appreciate this benchmark report showing how freight SaaS platforms reduced dispatch exception rates by 34% through automated pipeline monitoring.\n\nWould next Tuesday at 2 PM CT work for a quick walk-through?\n\nBest,\nAlex Rivera",
         "Pending Review", "2026-11-21 14:00:00"),
        (lead_dict["marcus.vance@apexlogistics.io"], 3, "Permission to close file? - Apex Cloud Logistics",
         "Hi Marcus,\n\nI realize you are likely deep in engineering hiring and platform initiatives right now. If automated dispatch verification isn't a top priority for Q4, no problem at all.\n\nShould I check back in Q1 2027, or is there a colleague better suited to connect with?\n\nWarm regards,\nAlex Rivera",
         "Pending Review", "2026-11-25 09:30:00"),

        # Lead 3: Elena Rostova
        (lead_dict["elena.rostova@nexahealth.com"], 1, "Accelerating NexaHealth's clinical data integration post-Series B",
         "Hi Elena,\n\nCongratulations on the $28M Series B announced recently for NexaHealth! As you scale patient-record integrations across hospital partners, data ingestion bottlenecks can become a major risk.\n\nLeadPulse helped MedTech leaders automate compliant FHIR API pipeline checks with zero downtime.\n\nCould we explore a 15-minute introductory alignment next week?\n\nSincerely,\nAlex Rivera",
         "Approved", "2026-11-17 11:30:00"),
        (lead_dict["elena.rostova@nexahealth.com"], 2, "NexaHealth clinical integration: Zero-breach compliance playbook",
         "Hi Elena,\n\nFollowing up on our FHIR workflow automation notes. Here is our technical brief outlining automated SOC2 and HIPAA verification in distributed pipelines.\n\nHappy to share the live sandbox whenever convenient.\n\nBest,\nAlex",
         "Pending Review", "2026-11-20 11:30:00"),

        # Lead 5: Arjun Mehta
        (lead_dict["arjun.mehta@finflow.ai"], 1, "Cross-border payment latency reduction for FinFlow",
         "Hi Arjun,\n\nSaw FinFlow's expansion into multi-currency settlement. Microsecond reconciliation latency in GCP/Go architectures is notoriously difficult to maintain under peak transaction loads.\n\nWe built an automated ingestion telemetry engine that keeps settlement discrepancies under 0.01%.\n\nWould you be open to an executive tech brief this Friday?\n\nCheers,\nAlex Rivera",
         "Pending Review", "2026-11-19 15:00:00")
    ]

    for seq in sample_sequences:
        cursor.execute("""
        INSERT INTO outreach_sequences (lead_id, step_number, subject, body, status, scheduled_at, approved_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, seq)

    # Seed WhatsApp Inbound Conversations
    marcus_id = lead_dict["marcus.vance@apexlogistics.io"]
    wa_msgs = [
        (marcus_id, "+1 (312) 555-0192", "user", "Hi there, saw your email on automated dispatch verification. Does this integrate with our Snowflake warehouse?", "Tech Inquiry", "Yes, allocated Q4 budget", "VP Supply Chain (Decision Maker)", "High - dispatch delays", "Need within 30 days", 0, 0),
        (marcus_id, "+1 (312) 555-0192", "assistant", "Hello Marcus! Yes, LeadPulse provides a native Snowflake read/write connector with zero ETL lag. We can handle up to 500k events/sec. Would you like a live demo or technical specs?", "Demo Offer", "Q4 Approved", "VP Decision Maker", "High", "< 30 days", 0, 0),
        (marcus_id, "+1 (312) 555-0192", "user", "That sounds promising. We have $45k allocated for this sprint. Can your enterprise team get on a call tomorrow at 11 AM CT?", "Demo Request", "$45k Allocated", "Authorized VP", "Critical SLA compliance", "Immediate", 1, 0),
        (marcus_id, "+1 (312) 555-0192", "assistant", "[HUMAN HANDOVER ESCALATED]: Connecting you with Senior Enterprise Solution Engineer Alex Rivera. Call invite sent for tomorrow at 11:00 AM CT.", "Handover", "$45k", "VP", "Critical", "Immediate", 1, 0)
    ]

    for msg in wa_msgs:
        cursor.execute("""
        INSERT INTO whatsapp_conversations (lead_id, phone_number, role, message, intent, bant_budget, bant_authority, bant_need, bant_timeline, handover_requested, is_opt_out)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, msg)

    # Seed HubSpot Sync Logs
    cursor.execute("""
    INSERT INTO hubspot_sync_log (entity_type, entity_id, hubspot_id, sync_direction, sync_status, details)
    VALUES 
    ('Contact', 1, 'HS-CONT-10291', 'PUSH', 'SUCCESS', 'Synced Marcus Vance to HubSpot Deals Pipeline: Enterprise Logistics ($65,000)'),
    ('Contact', 3, 'HS-CONT-10304', 'PUSH', 'SUCCESS', 'Synced Elena Rostova to HubSpot Deals Pipeline: MedTech Tier-1 ($120,000)'),
    ('Company', 1, 'HS-COMP-9812', 'PUSH', 'SUCCESS', 'Apex Cloud Logistics profile synced with 8 custom properties')
    """)

    conn.commit()
    conn.close()

# Initialize DB upon import
init_db()
seed_sample_data()
