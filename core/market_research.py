"""
LeadPulse AI - Market Research & Company Discovery Engine
Provides company discovery, firmographic filtering, tech stack profiling,
hiring signal analysis, and account prioritization.
"""
from typing import List, Dict, Optional
from core.database import get_connection

# Comprehensive B2B Industry Directory for Discovery
DISCOVERY_CATALOG = [
    {
        "name": "CloudMatrix Analytics",
        "domain": "cloudmatrix.ai",
        "industry": "Data Infrastructure",
        "size": "100-250",
        "location": "Seattle, WA",
        "revenue_range": "$15M-$30M",
        "tech_stack": "AWS, Kafka, Snowflake, Python, Kubernetes",
        "hiring_signal": "Hiring VP of Sales & 8 Solutions Engineers; recent Series B ($35M)",
        "priority_score": 92,
        "sample_contacts": [
            {"first_name": "Devin", "last_name": "Hayes", "title": "Chief Technology Officer"},
            {"first_name": "Melissa", "last_name": "Torres", "title": "VP of Revenue Operations"}
        ]
    },
    {
        "name": "BioHealth Precision",
        "domain": "biohealthprecision.org",
        "industry": "HealthTech & MedDevice",
        "size": "250-500",
        "location": "Cambridge, MA",
        "revenue_range": "$30M-$60M",
        "tech_stack": "Azure, FHIR APIs, Python, React",
        "hiring_signal": "FDA Approval secured for genomic monitoring platform; scaling enterprise hospital sales",
        "priority_score": 88,
        "sample_contacts": [
            {"first_name": "Jonathan", "last_name": "Kim", "title": "Chief Medical Information Officer"},
            {"first_name": "Claire", "last_name": "Duval", "title": "Director of Clinical Integrations"}
        ]
    },
    {
        "name": "OmniPay Global",
        "domain": "omnipayglobal.io",
        "industry": "FinTech & Payments",
        "size": "500-1000",
        "location": "San Francisco, CA",
        "revenue_range": "$80M-$150M",
        "tech_stack": "GCP, BigQuery, Golang, Stripe, Redis",
        "hiring_signal": "Expanding APAC operations; hiring 15 compliance and merchant onboarding managers",
        "priority_score": 95,
        "sample_contacts": [
            {"first_name": "Rohan", "last_name": "Patel", "title": "SVP of Merchant Operations"},
            {"first_name": "Jessica", "last_name": "Huang", "title": "Head of Payment Gateway Infrastructure"}
        ]
    },
    {
        "name": "Vanguard Cyber Defense",
        "domain": "vanguardcyber.com",
        "industry": "Cybersecurity",
        "size": "100-250",
        "location": "Tysons, VA",
        "revenue_range": "$20M-$45M",
        "tech_stack": "AWS, Splunk, CrowdStrike, Python",
        "hiring_signal": "Awarded $14M Federal defense cybersecurity contract; seeking zero-trust automation",
        "priority_score": 84,
        "sample_contacts": [
            {"first_name": "Marcus", "last_name": "Brantley", "title": "Chief Information Security Officer"},
            {"first_name": "Laura", "last_name": "Nixon", "title": "VP of Security Operations"}
        ]
    },
    {
        "name": "SwiftRoute Logistics",
        "domain": "swiftroute.co",
        "industry": "Supply Chain & SaaS",
        "size": "50-100",
        "location": "Atlanta, GA",
        "revenue_range": "$8M-$15M",
        "tech_stack": "PostgreSQL, React Native, Node.js, AWS",
        "hiring_signal": "Fleet automated tracking rollout across 1,200 vehicles in Midwest region",
        "priority_score": 79,
        "sample_contacts": [
            {"first_name": "Travis", "last_name": "Garrison", "title": "Chief Operating Officer"},
            {"first_name": "Amy", "last_name": "Chen", "title": "Fleet Technology Manager"}
        ]
    },
    {
        "name": "KiteScale AI",
        "domain": "kitescale.tech",
        "industry": "Algorithmic Trading & AI",
        "size": "25-50",
        "location": "New York, NY",
        "revenue_range": "$12M-$25M",
        "tech_stack": "CUDA, PyTorch, C++, Linux High-Performance",
        "hiring_signal": "Deploying low-latency trading infrastructure in Equinix NY4 data center",
        "priority_score": 86,
        "sample_contacts": [
            {"first_name": "Arthur", "last_name": "Pendleton", "title": "Head of Algorithmic Execution"}
        ]
    }
]

def search_discovery_catalog(
    industry: Optional[str] = None,
    size: Optional[str] = None,
    query: Optional[str] = None
) -> List[Dict]:
    """Filter discovery catalog by industry, size, and keyword search."""
    results = []
    q = query.strip().lower() if query else ""

    for comp in DISCOVERY_CATALOG:
        if industry and industry != "All Industries" and comp["industry"] != industry:
            continue
        if size and size != "All Sizes" and comp["size"] != size:
            continue
        if q:
            searchable = f"{comp['name']} {comp['domain']} {comp['tech_stack']} {comp['hiring_signal']} {comp['location']}".lower()
            if q not in searchable:
                continue
        results.append(comp)
    return results

def import_discovered_company(company_dict: Dict) -> int:
    """Import a discovered company and its primary contacts into the local CRM."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if company already exists
    cursor.execute("SELECT id FROM companies WHERE LOWER(name) = ? OR LOWER(domain) = ?", 
                   (company_dict["name"].lower(), company_dict["domain"].lower()))
    row = cursor.fetchone()

    if row:
        company_id = row["id"]
    else:
        cursor.execute("""
        INSERT INTO companies (name, domain, industry, size, location, revenue_range, tech_stack, hiring_signal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_dict["name"],
            company_dict["domain"],
            company_dict["industry"],
            company_dict["size"],
            company_dict["location"],
            company_dict["revenue_range"],
            company_dict["tech_stack"],
            company_dict["hiring_signal"]
        ))
        company_id = cursor.lastrowid

    # Import primary contacts
    imported_contacts = 0
    for contact in company_dict.get("sample_contacts", []):
        email = f"{contact['first_name'].lower()}.{contact['last_name'].lower()}@{company_dict['domain']}"
        cursor.execute("SELECT id FROM leads WHERE LOWER(email) = ?", (email.lower(),))
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO leads (company_id, first_name, last_name, title, email, status, lead_score, temperature)
            VALUES (?, ?, ?, ?, ?, 'New', ?, 'Warm')
            """, (
                company_id,
                contact["first_name"],
                contact["last_name"],
                contact["title"],
                email,
                company_dict.get("priority_score", 70)
            ))
            imported_contacts += 1

    # Log audit
    cursor.execute("""
    INSERT INTO audit_logs (module, action, details)
    VALUES ('Market Research', 'IMPORT_COMPANY', ?)
    """, (f"Imported company '{company_dict['name']}' with {imported_contacts} contact(s).",))

    conn.commit()
    conn.close()
    return company_id
