# ⚡ LeadPulse AI – Lead Generation & Business Development Automation Platform

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57.svg)](https://www.sqlite.org/)
[![HubSpot API](https://img.shields.io/badge/CRM%20Adapter-HubSpot%20REST%20v3-FF7A59.svg)](https://developers.hubspot.com/)
[![WhatsApp Cloud API](https://img.shields.io/badge/Meta%20Graph%20API-v19.0-25D366.svg)](https://developers.facebook.com/docs/whatsapp/cloud-api)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **LeadPulse AI** is an autonomous, unified lead-lifecycle and business development platform designed to bring repetitive sales-development tasks into one trackable, auditable workflow.

---

## 🎯 Executive Overview & Business Value

In fast-paced B2B environments, sales development reps (SDRs) and revenue leaders waste **over 65% of their working hours** toggling across disconnected tools for account research, email hunting, syntax verification, CRM updates, personalized copywriting, and WhatsApp inquiry qualification. 

**LeadPulse AI** consolidates this entire pipeline into a cohesive, high-performance operating system:
* **Market Research & Discovery:** Uncovers high-fit enterprise accounts with real-time growth signals (Series B/C funding, cloud migrations, hiring spikes).
* **Contact Enrichment & Multi-Tier Verification:** Predicts corporate email patterns (`first.last@`, `first@`, etc.) and performs **RFC 5322 syntax validation, active DNS checks, and mail exchange (MX) record queries** to eliminate bounces and protect sender reputation.
* **Local CRM & HubSpot Two-Way Sync:** Maintains persistent SQLite data models with automated two-way synchronization to **HubSpot CRM v3 API** and one-click CSV portability.
* **Personalized 3-Step Sequences with Human Approval Queue:** Generates contextual, multi-touch email campaigns (Hook & Cold Pitch ➔ Social Proof Case Study ➔ Polite Breakup) with human-in-the-loop review and editing.
* **WhatsApp Cloud API Suite:** Processes inbound Meta webhooks, performs real-time **BANT (Budget, Authority, Need, Timeline)** qualification, assigns dynamic lead temperature labels (🔥 Hot, 🟡 Warm, ❄️ Cold), triggers automated **Human Agent Handover**, and manages opt-out/STOP compliance.
* **Sales Copilot:** Delivers instant prospect dossiers, call talking points, objection handling playbooks, and executive revenue telemetry.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Discovery["1. Market Research & Account Discovery"]
        A[Firmographic Directory] --> B[Hiring & Funding Signal Analyzer]
        B --> C[Ideal Customer Profile (ICP) Scorer]
    end

    subgraph Enrichment["2. Contact Enrichment & DNS Verifier"]
        C --> D[Corporate Email Pattern Generator]
        D --> E[RFC 5322 Syntax Engine]
        E --> F[Domain Active DNS Resolver]
        F --> G[Mail Exchange (MX) Host Query]
        G --> H[CRM Deduplication & Deliverability Classifier]
    end

    subgraph CRM["3. Local CRM & Ecosystem Adapters"]
        H --> I[(SQLite Relational Database)]
        I <--> J[HubSpot REST API Adapter (Contacts & Deals)]
        I --> K[CSV Data Exporter]
    end

    subgraph Outreach["4. Multi-Touch Sequences & Human Governance"]
        I --> L[AI 3-Step Sequence Synthesizer]
        L --> M{Human Approval Queue}
        M -- "Approve & Edit" --> N[Scheduled Dispatcher]
        M -- "Reject" --> O[Feedback Archive]
    end

    subgraph Inbound["5. WhatsApp Cloud API & Qualification"]
        P[Inbound Meta Webhook] --> Q[Intent Classifier]
        Q --> R[BANT Extraction Engine]
        R --> S{Lead Temperature & Handover}
        S -- "High Urgency / Hot" --> T[Human Agent Handover Trigger]
        S -- "Standard Inquiry" --> U[Autonomous AI Reply]
        Q --> V[Compliance Opt-Out Handler (STOP)]
    end

    subgraph Copilot["6. Sales Copilot & Executive KPI Telemetry"]
        I --> W[Interactive Revenue Dashboard]
        I --> X[360° AI Prospect Briefing Dossier]
    end
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend & UI/UX** | **Streamlit (v1.30+)**, Custom CSS Modern Design System, Plotly interactive charts |
| **Core Language** | **Python (3.10+)** with modular decoupled architecture |
| **Database & Persistence** | **SQLite3** with relational schema (`companies`, `leads`, `enrichments`, `sequences`, `whatsapp`, `audit_logs`) |
| **REST APIs & Integrations** | **HubSpot CRM API v3**, **WhatsApp Cloud API (Graph v19.0)**, Requests, Pydantic |
| **DNS & Mail Verification** | Native Unix `dig` socket resolution, RFC 5322 Regex, RFC compliant MX query parser |
| **AI & Neural Generation** | Contextual heuristic neural generator with zero-dependency instant startup + **OpenAI GPT-4o / Google Gemini / Claude** adapters |

---

## 🚀 Key Modules & Capabilities

### 1. 🔍 Market Research & Target Company Discovery
- Filter companies across high-growth verticals (Data Infrastructure, HealthTech, FinTech, Cybersecurity, SaaS).
- Track hiring surges, tech stack footprints (AWS, Snowflake, Kubernetes, BigQuery), and funding rounds.
- 1-click **"Import to CRM Pipeline"** automatically inserts accounts and key decision-makers.

### 2. ⚡ Multi-Tier Contact Enrichment & DNS/MX Verifier
- **Pattern Prediction:** Generates corporate email syntax options with confidence weighting.
- **Verification Engine:**
  - `Tier 1`: RFC 5322 Regex syntax validation.
  - `Tier 2`: Active domain DNS resolution.
  - `Tier 3`: Native Mail Exchange (MX) record queries (identifies Microsoft 365, Google Workspace, Proofpoint, etc.).
  - `Tier 4`: Disposable/throwaway domain detection and CRM deduplication.
- Outputs **Deliverability Status** (`Deliverable`, `Risky`, `Invalid`) and an overall quality score (0-100).

### 3. 📋 Local CRM & HubSpot Two-Way Sync Adapter
- Full relational CRM view with search, status filters, and pipeline velocity tracking.
- **HubSpot REST API Integration:** Bi-directionally syncs contacts, companies, custom properties (`hs_lead_temperature`, `hs_lead_score`), and deal associations with live API or enterprise sandbox simulation.
- Audit trail logging all sync transactions with HTTP status codes and timestamps.

### 4. ✉️ 3-Step Outreach Sequence & Human Approval Queue
- Generates tailored multi-touch email sequences:
  - **Step 1:** Personalized hook linking recent company hiring/funding signals to core value proposition.
  - **Step 2:** Social proof follow-up highlighting peer benchmarks and case studies (+3 days).
  - **Step 3:** Polite breakup closing the file gracefully (+7 days).
- **Human Approval Queue:** Strict human-in-the-loop review interface allowing sales managers to inspect, edit subject/body, approve, reject, or request AI revisions before dispatch.

### 5. 💬 WhatsApp Cloud API Suite & Live BANT Simulator
- Interactive phone chat widget simulating inbound WhatsApp inquiries.
- **Autonomous BANT Scoring:** Dynamically extracts:
  - **B**udget: Detects funding or allocated project spend.
  - **A**uthority: Identifies decision makers (VP, C-Suite, Director).
  - **N**eed: Evaluates operational urgency and SLA bottlenecks.
  - **T**imeline: Distinguishes immediate (< 30 days) vs future quarters.
- **Lead Temperature Tagging:** Automatically labels prospects as 🔥 **Hot** (score > 75), 🟡 **Warm** (45-75), or ❄️ **Cold** (< 45).
- **Human Handover & Compliance:** Escalates high-value enterprise leads to live representatives and enforces instant opt-out compliance upon receiving "STOP" or "UNSUBSCRIBE".

### 6. 🤖 Sales Copilot & Strategic Dossiers
- Generates 360° prospect briefings in seconds.
- Recommends tailored discovery call talking points and objection-handling scripts (e.g., competing against incumbent SDRs, budget pushback, CRM integration questions).
- Suggests **Next Best Actions (NBA)** for closing deals faster.

---

## 💻 Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/partha0059/LeadPulse-AI.git
cd LeadPulse-AI
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📁 Repository Structure

```
LeadPulse-AI/
├── README.md                      # Comprehensive enterprise documentation
├── requirements.txt               # Python package dependencies
├── .gitignore                     # Git ignore rules
├── app.py                         # Unified Streamlit dashboard application
├── core/
│   ├── __init__.py
│   ├── config.py                  # Environment config, API credentials, paths
│   ├── database.py                # SQLite schema, migrations, seed data, CRUD
│   ├── contact_enrichment.py      # Pattern generator & DNS/MX verifier
│   ├── market_research.py         # Company discovery catalog & signal tracker
│   ├── email_sequences.py         # 3-step outreach sequence & approval queue
│   ├── whatsapp_engine.py         # WhatsApp Cloud API, BANT qualification, handover
│   ├── hubspot_adapter.py         # HubSpot REST API sync adapter
│   ├── sales_copilot.py           # Prospect dossiers & KPI metrics
│   └── llm_engine.py              # LLM integration & contextual neural generator
├── assets/
│   └── style.css                  # Modern corporate design system styling
└── data/
    └── leadpulse.db               # Pre-seeded SQLite database with realistic B2B data
```

---

## 🛡️ Enterprise Security & Data Governance
* **Zero Hardcoded Secrets:** Environment variable injection for all API tokens.
* **Data Hygiene:** Pre-outreach DNS and syntax verification prevents high bounce rates and domain blacklisting.
* **Human-in-the-Loop:** Outreach approval queue guarantees no automated message is sent without managerial sign-off.
* **Opt-Out Compliance:** Automated WhatsApp STOP processing honors user preferences immediately.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
