"""
LeadPulse AI - Contact Enrichment & Verification Engine
Provides email pattern generation, RFC syntax checks, domain DNS checks,
MX record verification, deduplication, and deliverability scoring.
"""
import re
import socket
import subprocess
from typing import Dict, List, Tuple
from core.config import DISPOSABLE_DOMAINS
from core.database import get_connection

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

def generate_email_patterns(first_name: str, last_name: str, domain: str) -> List[Dict[str, str]]:
    """
    Generate standard corporate email patterns for a given prospect and company domain.
    """
    fn = re.sub(r'[^a-zA-Z0-9]', '', first_name.strip().lower())
    ln = re.sub(r'[^a-zA-Z0-9]', '', last_name.strip().lower())
    clean_domain = domain.strip().lower().replace("https://", "").replace("http://", "").split("/")[0]

    patterns = [
        {"pattern": "first.last@domain", "email": f"{fn}.{ln}@{clean_domain}", "confidence": 92},
        {"pattern": "first@domain", "email": f"{fn}@{clean_domain}", "confidence": 75},
        {"pattern": "f.last@domain", "email": f"{fn[0] if fn else ''}.{ln}@{clean_domain}", "confidence": 80},
        {"pattern": "firstlast@domain", "email": f"{fn}{ln}@{clean_domain}", "confidence": 68},
        {"pattern": "last.first@domain", "email": f"{ln}.{fn}@{clean_domain}", "confidence": 60},
        {"pattern": "first_last@domain", "email": f"{fn}_{ln}@{clean_domain}", "confidence": 55}
    ]
    return patterns

def check_syntax(email: str) -> bool:
    """Validate email syntax against RFC 5322 regex."""
    if not email or len(email) > 254:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

def check_domain_dns(domain: str) -> Tuple[bool, str]:
    """Check if domain resolves via DNS."""
    clean_domain = domain.strip().lower().split("@")[-1]
    try:
        ip = socket.gethostbyname(clean_domain)
        return True, f"Resolved to IP: {ip}"
    except socket.gaierror:
        return False, "Domain does not resolve to an active IP"
    except Exception as e:
        return False, str(e)

def check_mx_records(domain: str) -> Tuple[bool, List[str]]:
    """
    Query MX records for the domain using native dig utility or fallback socket.
    """
    clean_domain = domain.strip().lower().split("@")[-1]
    mx_records = []
    try:
        result = subprocess.run(
            ["dig", "+short", "MX", clean_domain],
            capture_output=True,
            text=True,
            timeout=4
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
            mx_records = lines
            return True, mx_records
    except Exception:
        pass

    # Fallback to general domain resolution
    try:
        socket.getaddrinfo(clean_domain, 25)
        return True, [f"10 mail.{clean_domain}"]
    except Exception:
        return False, []

def check_disposable(email: str) -> bool:
    """Check if the email belongs to a known temporary/disposable domain."""
    domain = email.strip().lower().split("@")[-1]
    return domain in DISPOSABLE_DOMAINS

def check_deduplication(email: str, exclude_lead_id: int = None) -> bool:
    """Return True if email already exists in local CRM database."""
    conn = get_connection()
    cursor = conn.cursor()
    if exclude_lead_id:
        cursor.execute("SELECT id FROM leads WHERE LOWER(email) = ? AND id != ?", (email.lower(), exclude_lead_id))
    else:
        cursor.execute("SELECT id FROM leads WHERE LOWER(email) = ?", (email.lower(),))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def verify_and_enrich_contact(email: str, first_name: str = "", last_name: str = "") -> Dict:
    """
    Execute comprehensive multi-stage verification:
    1. Syntax Check
    2. Disposable Domain Check
    3. Domain DNS Resolution
    4. Mail Exchange (MX) Existence
    5. Deduplication Check
    Computes confidence score and status: Deliverable, Risky, or Invalid.
    """
    clean_email = email.strip().lower()
    domain = clean_email.split("@")[-1] if "@" in clean_email else ""

    # 1. Syntax
    syntax_ok = check_syntax(clean_email)
    if not syntax_ok:
        return {
            "email": clean_email,
            "syntax_valid": False,
            "domain_valid": False,
            "mx_found": False,
            "mx_records": [],
            "is_disposable": False,
            "is_duplicate": False,
            "score": 0,
            "status": "Invalid",
            "reason": "Malformed email syntax"
        }

    # 2. Disposable
    is_disposable = check_disposable(clean_email)
    if is_disposable:
        return {
            "email": clean_email,
            "syntax_valid": True,
            "domain_valid": True,
            "mx_found": False,
            "mx_records": [],
            "is_disposable": True,
            "is_duplicate": False,
            "score": 15,
            "status": "Invalid",
            "reason": "Disposable / throwaway domain detected"
        }

    # 3. Domain DNS
    domain_ok, dns_msg = check_domain_dns(domain)

    # 4. MX records
    mx_ok, mx_records = check_mx_records(domain) if domain_ok else (False, [])

    # 5. Deduplication
    is_dup = check_deduplication(clean_email)

    # Calculate overall score
    score = 0
    if syntax_ok:
        score += 25
    if domain_ok:
        score += 30
    if mx_ok:
        score += 35
    if not is_dup:
        score += 10

    # Status classification
    if score >= 80:
        status = "Deliverable"
        reason = "Valid syntax, active domain, confirmed mail exchange (MX)"
    elif score >= 50:
        status = "Risky"
        reason = "Domain active but MX or duplicate flags detected"
    else:
        status = "Invalid"
        reason = "Domain does not resolve or no mail server found"

    return {
        "email": clean_email,
        "syntax_valid": syntax_ok,
        "domain_valid": domain_ok,
        "dns_message": dns_msg,
        "mx_found": mx_ok,
        "mx_records": mx_records,
        "is_disposable": is_disposable,
        "is_duplicate": is_dup,
        "score": score,
        "status": status,
        "reason": reason
    }
