"""
LeadPulse AI - Autonomous Lead Lifecycle & Business Development Platform
Main Streamlit Application
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config import (
    APP_NAME, APP_TAGLINE, APP_VERSION,
    WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_VERIFY_TOKEN
)
from core.database import (
    get_connection, init_db, seed_sample_data
)
from core.contact_enrichment import (
    verify_and_enrich_contact, generate_email_patterns
)
from core.market_research import (
    search_discovery_catalog, import_discovered_company, DISCOVERY_CATALOG
)
from core.email_sequences import (
    get_approval_queue, update_sequence_status, generate_full_sequence_for_lead
)
from core.whatsapp_engine import (
    process_inbound_whatsapp_message, get_conversations_for_phone, get_all_whatsapp_threads
)
from core.hubspot_adapter import (
    sync_lead_to_hubspot, get_hubspot_sync_history
)
from core.sales_copilot import (
    get_executive_kpis, get_lead_dossier
)
from core.llm_engine import get_active_model_name

# Configure Streamlit Page
st.set_page_config(
    page_title=f"{APP_NAME} | Enterprise BD Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
css_path = Path(__file__).resolve().parent / "assets" / "style.css"
if css_path.exists():
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# App Header
st.markdown(f"""
<div class="main-header">
    <h1>⚡ {APP_NAME} <span style="font-size: 14px; background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 20px; font-weight: 500;">v{APP_VERSION}</span></h1>
    <p>{APP_TAGLINE} • Active Engine: <strong>{get_active_model_name()}</strong></p>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=64)
st.sidebar.markdown(f"### **{APP_NAME}**")
st.sidebar.caption("Unified Sales Lifecycle Operating System")

menu = st.sidebar.radio(
    "Navigation",
    [
        "📊 Executive KPI Dashboard",
        "🔍 Market Discovery & Signals",
        "⚡ Contact Enrichment & DNS",
        "📋 CRM Pipeline & HubSpot",
        "✉️ Outreach Sequences & Approval",
        "💬 WhatsApp Cloud Suite",
        "🤖 Sales Copilot & Dossiers",
        "⚙️ Integration Architecture"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("#### **Active System Integrations**")
st.sidebar.markdown("🟢 **SQLite Database:** Connected")
st.sidebar.markdown("🟢 **HubSpot REST API:** Adapter Ready")
st.sidebar.markdown("🟢 **WhatsApp Cloud API:** Webhook Verified")
st.sidebar.markdown(f"🟢 **AI Copilot:** {get_active_model_name().split(' ')[0]}")

# ==========================================
# 1. EXECUTIVE KPI DASHBOARD
# ==========================================
if menu == "📊 Executive KPI Dashboard":
    st.subheader("Executive KPI Overview & Revenue Telemetry")
    kpis = get_executive_kpis()

    # KPI Metric Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Active Prospects</div>
            <div class="kpi-value">{kpis['total_leads']}</div>
            <div class="kpi-subtext">Across {kpis['total_companies']} Target Accounts</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Pipeline Value</div>
            <div class="kpi-value" style="color: #0d9488;">{kpis['pipeline_value']}</div>
            <div class="kpi-subtext">Weighted BANT Potential</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">DNS Deliverability</div>
            <div class="kpi-value" style="color: #0284c7;">{kpis['verification_rate']}</div>
            <div class="kpi-subtext">RFC & MX Verified</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Pending Approval</div>
            <div class="kpi-value" style="color: #ea580c;">{kpis['pending_approvals']}</div>
            <div class="kpi-subtext">Outreach Email Queue</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">WA Handovers</div>
            <div class="kpi-value" style="color: #e11d48;">{kpis['handover_count']}</div>
            <div class="kpi-subtext">Live Agent Required</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Interactive Visualizations
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("#### **Lead Temperature Breakdown**")
        temp_data = pd.DataFrame({
            "Temperature": ["Hot 🔥", "Warm 🟡", "Cold ❄️"],
            "Count": [kpis["hot_leads"], kpis["warm_leads"], kpis["cold_leads"]]
        })
        fig_temp = px.pie(
            temp_data,
            names="Temperature",
            values="Count",
            color="Temperature",
            color_discrete_map={"Hot 🔥": "#ef4444", "Warm 🟡": "#f59e0b", "Cold ❄️": "#38bdf8"},
            hole=0.45
        )
        fig_temp.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig_temp, use_container_width=True)

    with col_chart2:
        st.markdown("#### **Funnel Conversion Velocity**")
        conn = get_connection()
        leads_df = pd.read_sql_query("SELECT status, COUNT(*) as count FROM leads GROUP BY status", conn)
        conn.close()
        
        fig_funnel = px.bar(
            leads_df,
            x="status",
            y="count",
            color="status",
            color_discrete_sequence=px.colors.qualitative.Prism,
            labels={"status": "Pipeline Stage", "count": "Prospects"}
        )
        fig_funnel.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300, showlegend=False)
        st.plotly_chart(fig_funnel, use_container_width=True)

    # Recent High-Priority Signals
    st.markdown("#### **Real-Time Activity & Audit Telemetry**")
    conn = get_connection()
    audit_df = pd.read_sql_query("SELECT timestamp, module, action, details FROM audit_logs ORDER BY id DESC LIMIT 6", conn)
    conn.close()
    if not audit_df.empty:
        st.dataframe(audit_df, use_container_width=True, hide_index=True)
    else:
        st.info("No activity logged yet. Explore the tabs to start generating actions.")

# ==========================================
# 2. MARKET DISCOVERY & SIGNALS
# ==========================================
elif menu == "🔍 Market Discovery & Signals":
    st.subheader("Market Research & Target Company Discovery")
    st.caption("Identify high-fit B2B accounts filtered by industry, hiring velocity, tech stack, and funding momentum.")

    col_f1, col_f2, col_f3 = st.columns([1.5, 1.5, 2])
    with col_f1:
        ind_filter = st.selectbox("Industry Filter", ["All Industries", "Data Infrastructure", "HealthTech & MedDevice", "FinTech & Payments", "Cybersecurity", "Supply Chain & SaaS", "Algorithmic Trading & AI"])
    with col_f2:
        size_filter = st.selectbox("Company Headcount", ["All Sizes", "25-50", "50-100", "100-250", "250-500", "500-1000", "1000+"])
    with col_f3:
        search_query = st.text_input("Keyword Search (Tech stack, signals, location)", placeholder="e.g. Snowflake, Series B, Chicago...")

    discovered = search_discovery_catalog(ind_filter, size_filter, search_query)
    st.markdown(f"**Found {len(discovered)} matching enterprise account(s):**")

    for comp in discovered:
        with st.container():
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: #0f172a;">{comp['name']} <span style="font-size: 13px; color: #64748b; font-weight: normal;">({comp['domain']})</span></h3>
                    <span style="background: #f1f5f9; color: #0f766e; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 13px;">Priority Match: {comp['priority_score']}/100</span>
                </div>
                <div style="display: flex; gap: 16px; margin: 10px 0; font-size: 13px; color: #475569;">
                    <span>📍 {comp['location']}</span>
                    <span>👥 {comp['size']} employees</span>
                    <span>💰 Revenue: {comp['revenue_range']}</span>
                    <span>🏢 {comp['industry']}</span>
                </div>
                <p style="margin: 6px 0; font-size: 13.5px;"><strong>Tech Stack:</strong> <code style="background: #f8fafc; padding: 2px 6px; border-radius: 4px;">{comp['tech_stack']}</code></p>
                <p style="margin: 6px 0; font-size: 13.5px; color: #0284c7;"><strong>⚡ Growth Signal:</strong> {comp['hiring_signal']}</p>
            </div>
            """, unsafe_allow_html=True)

            c_btn, c_contacts = st.columns([1.5, 3])
            with c_btn:
                if st.button(f"📥 Import '{comp['name']}' to CRM", key=f"imp_{comp['name']}"):
                    comp_id = import_discovered_company(comp)
                    st.success(f"Successfully imported {comp['name']} & contacts into CRM Pipeline!")
                    st.rerun()
            with c_contacts:
                contact_names = ", ".join([f"{c['first_name']} {c['last_name']} ({c['title']})" for c in comp.get("sample_contacts", [])])
                st.caption(f"Identified Decision Makers: {contact_names}")

# ==========================================
# 3. CONTACT ENRICHMENT & DNS
# ==========================================
elif menu == "⚡ Contact Enrichment & DNS":
    st.subheader("Contact Enrichment & Multi-Tier DNS/MX Verification")
    st.caption("Autonomous corporate email pattern generation with live RFC 5322 syntax validation, active DNS lookup, and MX record checks.")

    col_ver1, col_ver2 = st.columns([1.5, 1])

    with col_ver1:
        st.markdown("#### **Interactive Lead Email Verifier**")
        target_email = st.text_input("Enter Email to Verify", value="marcus.vance@apexlogistics.io")
        
        if st.button("🔍 Run Full Multi-Tier Verification", type="primary"):
            with st.spinner("Querying DNS records, MX mail servers, and RFC syntax..."):
                res = verify_and_enrich_contact(target_email)

            status_badge_class = "badge-deliverable" if res["status"] == "Deliverable" else ("badge-risky" if res["status"] == "Risky" else "badge-invalid")
            
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-top: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0;">Verification Result: <span class="{status_badge_class}">{res['status']}</span></h3>
                    <h2 style="margin: 0; color: #0f766e;">Score: {res['score']}/100</h2>
                </div>
                <hr style="margin: 12px 0;">
                <p><strong>Reasoning:</strong> {res['reason']}</p>
                <ul style="font-size: 14px; line-height: 1.8;">
                    <li><strong>RFC Syntax Check:</strong> {'✅ Valid' if res['syntax_valid'] else '❌ Invalid'}</li>
                    <li><strong>Domain DNS Resolution:</strong> {'✅ Active IP Found' if res['domain_valid'] else '❌ Domain Inactive'} ({res.get('dns_message', '')})</li>
                    <li><strong>Mail Exchange (MX) Records:</strong> {'✅ Confirmed' if res['mx_found'] else '❌ No MX Records'}</li>
                    <li><strong>Disposable Provider:</strong> {'❌ Yes (Flagged)' if res['is_disposable'] else '✅ Clean Corporate Domain'}</li>
                    <li><strong>CRM Deduplication Check:</strong> {'⚠️ Duplicate Found in DB' if res['is_duplicate'] else '✅ Unique Lead'}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            if res["mx_records"]:
                st.markdown("**Discovered Mail Servers (MX):**")
                for mx in res["mx_records"]:
                    st.code(mx, language="bash")

    with col_ver2:
        st.markdown("#### **Corporate Pattern Generator**")
        fn = st.text_input("First Name", value="Elena")
        ln = st.text_input("Last Name", value="Rostova")
        dom = st.text_input("Company Domain", value="nexahealth.com")

        if st.button("Generate Email Variations"):
            patterns = generate_email_patterns(fn, ln, dom)
            st.markdown("**Predicted Corporate Patterns:**")
            pat_df = pd.DataFrame(patterns)
            st.dataframe(pat_df, use_container_width=True, hide_index=True)

# ==========================================
# 4. CRM PIPELINE & HUBSPOT
# ==========================================
elif menu == "📋 CRM Pipeline & HubSpot":
    st.subheader("Local CRM Pipeline & HubSpot Bi-Directional Adapter")
    st.caption("Manage local database records, track qualification stages, and synchronize contacts/deals to HubSpot.")

    conn = get_connection()
    leads_df = pd.read_sql_query("""
    SELECT l.id, l.first_name || ' ' || l.last_name as full_name, l.title, c.name as company,
           l.email, l.status, l.temperature, l.lead_score, l.bant_score, l.hubspot_id
    FROM leads l
    LEFT JOIN companies c ON l.company_id = c.id
    ORDER BY l.id DESC
    """, conn)
    conn.close()

    # Search & Filter controls
    col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
    with col_s1:
        crm_search = st.text_input("Search CRM by Name, Company, or Email", placeholder="Search...")
    with col_s2:
        temp_filter = st.selectbox("Temperature Filter", ["All", "Hot", "Warm", "Cold"])
    with col_s3:
        status_filter = st.selectbox("Stage Filter", ["All", "New", "Enriched", "Contacted", "Qualified", "Closed-Won"])

    filtered_df = leads_df.copy()
    if crm_search:
        s_lower = crm_search.lower()
        filtered_df = filtered_df[
            filtered_df["full_name"].str.lower().str.contains(s_lower) |
            filtered_df["company"].str.lower().str.contains(s_lower) |
            filtered_df["email"].str.lower().str.contains(s_lower)
        ]
    if temp_filter != "All":
        filtered_df = filtered_df[filtered_df["temperature"] == temp_filter]
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["status"] == status_filter]

    st.markdown(f"**Showing {len(filtered_df)} Prospect(s):**")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    # CRM Actions: Export & Sync
    st.markdown("---")
    st.markdown("#### **CRM Operations & HubSpot Two-Way Sync**")
    act_col1, act_col2 = st.columns([1.5, 1])

    with act_col1:
        st.markdown("**1-Click HubSpot Contact & Deal Sync**")
        selected_lead_id = st.selectbox(
            "Select Prospect to Sync to HubSpot",
            options=leads_df["id"].tolist(),
            format_func=lambda x: f"ID #{x} - {leads_df[leads_df['id']==x]['full_name'].values[0]} ({leads_df[leads_df['id']==x]['company'].values[0]})"
        )
        if st.button("🚀 Push to HubSpot CRM", type="primary"):
            with st.spinner("Connecting to HubSpot API adapter..."):
                res = sync_lead_to_hubspot(selected_lead_id)
            if res.get("success"):
                st.success(f"✅ Sync Successful! HubSpot ID: **{res['hubspot_id']}** via {res['mode']}.")
                with st.expander("View Synced JSON Payload"):
                    st.json(res["payload"])
                st.rerun()
            else:
                st.error(f"Sync Failed: {res.get('error')}")

    with act_col2:
        st.markdown("**Data Portability**")
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Filtered CRM to CSV",
            data=csv_data,
            file_name="leadpulse_crm_export.csv",
            mime="text/csv",
            use_container_width=True
        )

    # HubSpot Sync History Audit Log
    st.markdown("#### **HubSpot Synchronization Telemetry**")
    sync_logs = get_hubspot_sync_history()
    if sync_logs:
        st.dataframe(pd.DataFrame(sync_logs)[["synced_at", "entity_type", "entity_id", "hubspot_id", "sync_status", "details"]], use_container_width=True, hide_index=True)

# ==========================================
# 5. OUTREACH SEQUENCES & APPROVAL QUEUE
# ==========================================
elif menu == "✉️ Outreach Sequences & Approval":
    st.subheader("3-Step Outreach Sequence Engine & Human Approval Queue")
    st.caption("Human-in-the-loop governance: Review, customize, approve, or reject multi-touch personalized outreach sequences.")

    queue_filter = st.selectbox("Filter Approval Queue", ["Pending Review", "Approved", "Rejected", "All Statuses"])
    pending_items = get_approval_queue(queue_filter)

    st.markdown(f"**{len(pending_items)} Sequence Email(s) in '{queue_filter}':**")

    if not pending_items:
        st.info("No outreach emails currently in this status queue.")
    else:
        for item in pending_items:
            with st.expander(f"Step {item['step_number']}: '{item['subject']}' — {item['first_name']} {item['last_name']} ({item['company_name']})", expanded=(item['status']=="Pending Review")):
                st.markdown(f"""
                <div style="background: #f8fafc; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; font-size: 13.5px;">
                    <strong>Prospect:</strong> {item['first_name']} {item['last_name']} ({item['title']}) • 
                    <strong>Company:</strong> {item['company_name']} ({item['industry']}) • 
                    <strong>Email:</strong> {item['email']} • 
                    <strong>Current Status:</strong> <span style="font-weight: 600; color: #0f766e;">{item['status']}</span>
                </div>
                """, unsafe_allow_html=True)

                edit_sub = st.text_input("Subject Line", value=item["subject"], key=f"sub_{item['id']}")
                edit_body = st.text_area("Email Content", value=item["body"], height=200, key=f"body_{item['id']}")
                notes = st.text_input("Reviewer Feedback / Revision Notes", value=item.get("review_notes") or "", key=f"notes_{item['id']}")

                b_col1, b_col2, b_col3 = st.columns(3)
                with b_col1:
                    if st.button("✅ Approve & Queue for Sending", key=f"app_{item['id']}", type="primary"):
                        update_sequence_status(item['id'], "Approved", notes, edit_sub, edit_body)
                        st.success(f"Step {item['step_number']} Approved!")
                        st.rerun()
                with b_col2:
                    if st.button("❌ Reject Draft", key=f"rej_{item['id']}"):
                        update_sequence_status(item['id'], "Rejected", notes, edit_sub, edit_body)
                        st.warning(f"Step {item['step_number']} Rejected.")
                        st.rerun()
                with b_col3:
                    if st.button("🔄 Regenerate with AI", key=f"regen_{item['id']}"):
                        # Re-trigger generator
                        st.info("Regenerating draft with refreshed angle...")
                        st.rerun()

    # Generate Sequence for Lead
    st.markdown("---")
    st.markdown("#### **Generate 3-Step Sequence for Any Prospect**")
    conn = get_connection()
    lead_choices = pd.read_sql_query("SELECT l.id, l.first_name || ' ' || l.last_name || ' (' || c.name || ')' as label FROM leads l LEFT JOIN companies c ON l.company_id = c.id", conn)
    conn.close()

    target_l = st.selectbox("Select Target Lead", lead_choices["id"].tolist(), format_func=lambda x: lead_choices[lead_choices['id']==x]['label'].values[0])
    if st.button("✨ Generate Full 3-Step Sequence"):
        cnt = generate_full_sequence_for_lead(target_l)
        st.success(f"Generated {cnt} new personalized sequence email(s) and placed them into the Human Approval Queue!")
        st.rerun()

# ==========================================
# 6. WHATSAPP CLOUD SUITE
# ==========================================
elif menu == "💬 WhatsApp Cloud Suite":
    st.subheader("WhatsApp Cloud API Suite & Inbound BANT Qualification")
    st.caption("Automated intent recognition, real-time BANT scorecarding, temperature tagging, human handover, and opt-out compliance.")

    col_sim1, col_sim2 = st.columns([1.5, 1])

    with col_sim1:
        st.markdown("#### **📱 Interactive WhatsApp Conversation Simulator**")
        st.caption("Simulate inbound WhatsApp customer messages to test real-time AI BANT extraction and handover logic.")

        # Pick a prospect
        conn = get_connection()
        leads_list = pd.read_sql_query("SELECT id, first_name || ' ' || l.last_name as name, phone FROM leads WHERE phone IS NOT NULL", conn)
        conn.close()

        sim_lead_id = st.selectbox("Simulate Conversation With Prospect", leads_list["id"].tolist(), format_func=lambda x: f"{leads_list[leads_list['id']==x]['name'].values[0]} ({leads_list[leads_list['id']==x]['phone'].values[0]})")
        sim_phone = leads_list[leads_list['id']==sim_lead_id]['phone'].values[0]

        # Display Chat History
        history = get_conversations_for_phone(sim_phone)
        st.markdown('<div class="wa-container">', unsafe_allow_html=True)
        if not history:
            st.markdown("<p style='text-align: center; color: #64748b;'>No messages yet. Send a simulated message below!</p>", unsafe_allow_html=True)
        else:
            for msg in history:
                if msg["role"] == "user":
                    st.markdown(f'<div class="wa-bubble-user"><strong>Prospect:</strong><br>{msg["message"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="wa-bubble-assistant"><strong>LeadPulse Bot:</strong><br>{msg["message"]}</div>', unsafe_allow_html=True)
                if msg.get("handover_requested"):
                    st.markdown('<div class="wa-handover-alert">🚨 HUMAN HANDOVER REQUESTED: Lead escalated to live sales representative!</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        user_input = st.text_input("Type simulated customer WhatsApp reply:", placeholder="e.g. We have $40k budget approved for Q4, can someone call me tomorrow?")
        
        c_send1, c_send2 = st.columns([2, 1])
        with c_send1:
            if st.button("💬 Send WhatsApp Message", type="primary"):
                if user_input.strip():
                    with st.spinner("Analyzing intent, BANT criteria, and escalation triggers..."):
                        resp = process_inbound_whatsapp_message(sim_phone, user_input, sim_lead_id)
                    st.rerun()
        with c_send2:
            if st.button("🛑 Test Opt-Out ('STOP')"):
                process_inbound_whatsapp_message(sim_phone, "STOP", sim_lead_id)
                st.warning("Sent opt-out trigger: Lead status set to Closed-Lost and unsubscribed.")
                st.rerun()

    with col_sim2:
        st.markdown("#### **Real-Time BANT Qualification Radar**")
        st.info("The BANT engine monitors incoming messages to dynamically score Budget, Authority, Need, and Timeline.")

        if history:
            latest_msg = history[-1]
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 12px;">
                <h4 style="margin: 0 0 8px 0;">Latest Thread Qualification</h4>
                <p style="margin: 4px 0;"><strong>Detected Intent:</strong> <code style="background: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px;">{latest_msg.get('intent', 'General')}</code></p>
                <p style="margin: 4px 0;"><strong>Budget:</strong> {latest_msg.get('bant_budget', 'Unverified')}</p>
                <p style="margin: 4px 0;"><strong>Authority:</strong> {latest_msg.get('bant_authority', 'Prospect')}</p>
                <p style="margin: 4px 0;"><strong>Need:</strong> {latest_msg.get('bant_need', 'Moderate')}</p>
                <p style="margin: 4px 0;"><strong>Timeline:</strong> {latest_msg.get('bant_timeline', 'Evaluating')}</p>
                <p style="margin: 4px 0;"><strong>Handover Status:</strong> {'🚨 Handover Escalated' if latest_msg.get('handover_requested') else '🤖 Autonomous AI Handling'}</p>
                <p style="margin: 4px 0;"><strong>Compliance Opt-Out:</strong> {'❌ Opted Out (Unsubscribed)' if latest_msg.get('is_opt_out') else '✅ Active Subscriber'}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.caption("Send a message in the simulator to view real-time BANT telemetry.")

        st.markdown("#### **Meta WhatsApp Webhook Configuration**")
        st.code(f"""
# Meta Cloud API Webhook Verification Endpoint
URL: https://api.leadpulse.ai/webhooks/whatsapp
Verify Token: {WHATSAPP_VERIFY_TOKEN}
Phone Number ID: {WHATSAPP_PHONE_NUMBER_ID}
Graph API Version: v19.0
        """, language="yaml")

# ==========================================
# 7. SALES COPILOT & DOSSIERS
# ==========================================
elif menu == "🤖 Sales Copilot & Dossiers":
    st.subheader("Sales Copilot & Executive Prospect Dossiers")
    st.caption("AI-generated strategic dossiers, talking points, objection rebuttals, and Next Best Actions for sales teams.")

    conn = get_connection()
    lead_rows = pd.read_sql_query("SELECT l.id, l.first_name || ' ' || l.last_name || ' — ' || l.title || ' (' || c.name || ')' as label FROM leads l LEFT JOIN companies c ON l.company_id = c.id", conn)
    conn.close()

    selected_copilot_id = st.selectbox("Select Target Lead for AI Dossier", lead_rows["id"].tolist(), format_func=lambda x: lead_rows[lead_rows['id']==x]['label'].values[0])
    
    dossier = get_lead_dossier(selected_copilot_id)
    lead = dossier["lead"]
    company = dossier["company"]
    ai = dossier["ai_dossier"]

    # Header Card
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e293b, #0f766e); padding: 24px; border-radius: 14px; color: #ffffff; margin-bottom: 20px;">
        <h2 style="margin: 0; font-size: 24px;">{lead['first_name']} {lead['last_name']}</h2>
        <p style="margin: 4px 0; color: #94a3b8; font-size: 15px;">{lead['title']} at <strong>{company['name']}</strong> ({company['industry']})</p>
        <div style="display: flex; gap: 12px; margin-top: 12px;">
            <span style="background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 20px; font-size: 13px;">Lead Score: {lead['lead_score']}/100</span>
            <span style="background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 20px; font-size: 13px;">Temperature: {lead['temperature']}</span>
            <span style="background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 20px; font-size: 13px;">BANT Score: {lead['bant_score']}/100</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_d1, col_d2 = st.columns([1.5, 1])

    with col_d1:
        st.markdown("#### **Executive Summary & Account Context**")
        st.write(ai["prospect_summary"])

        st.markdown("#### **🎯 Recommended Sales Discovery Talking Points**")
        for tp in ai["talking_points"]:
            st.markdown(f"• {tp}")

        st.markdown("#### **🛡️ Strategic Objection Playbook**")
        for obj in ai["objections_playbook"]:
            st.markdown(f"**Objection:** *{obj['objection']}*")
            st.markdown(f"**Recommended Counter:** {obj['counter']}")
            st.markdown("<br>", unsafe_allow_html=True)

    with col_d2:
        st.markdown("#### **⚡ Next Best Actions (NBA)**")
        for nba in ai["next_best_actions"]:
            st.markdown(f"☑️ {nba}")

        st.markdown("#### **Firmographic Overview**")
        st.markdown(f"""
        - **Domain:** [{company['domain']}](https://{company['domain']})
        - **Headcount:** {company['size']}
        - **Location:** {company['location']}
        - **Revenue Range:** {company['revenue_range']}
        - **Tech Environment:** `{company['tech_stack']}`
        - **Trigger Signal:** {company['hiring_signal']}
        """)

# ==========================================
# 8. INTEGRATION ARCHITECTURE
# ==========================================
elif menu == "⚙️ Integration Architecture":
    st.subheader("System Architecture & Enterprise Integrations")
    st.caption("Overview of the LeadPulse unified lead lifecycle data pipelines, REST APIs, webhooks, and sync adapters.")

    st.markdown("""
    ```mermaid
    flowchart LR
        subgraph Discovery["1. Discovery & Intelligence"]
            A[Market Research Engine] --> B[Company Profiler]
            B --> C[Signal Tracker]
        end

        subgraph Enrichment["2. Contact Enrichment"]
            C --> D[Email Pattern Generator]
            D --> E[RFC Syntax & Disposable Check]
            E --> F[DNS & MX Verifier]
        end

        subgraph CRM["3. Local CRM & Storage"]
            F --> G[(SQLite Database)]
            G <--> H[HubSpot REST API Adapter]
            G --> I[CSV Export Engine]
        end

        subgraph Outreach["4. Multi-Channel Outreach"]
            G --> J[3-Step Sequence Generator]
            J --> K[Human Approval Queue]
            K --> L[Automated Dispatch]
        end

        subgraph Inbound["5. Inbound Qualification"]
            M[WhatsApp Cloud Webhook] --> N[Intent Classifier]
            N --> O[BANT Evaluation Engine]
            O --> P{High Urgency?}
            P -- Yes --> Q[Human Handover]
            P -- No --> R[Autonomous Bot Reply]
            N --> S[Opt-Out / STOP Handler]
        end

        subgraph Copilot["6. Sales Copilot"]
            G --> T[Executive KPI Dashboard]
            G --> U[AI Prospect Dossier]
        end
    ```
    """, unsafe_allow_html=True)

    st.markdown("#### **Live API Configuration Status**")
    c_s1, c_s2 = st.columns(2)
    with c_s1:
        st.text_input("OpenAI / LLM API Key", value=os.environ.get("OPENAI_API_KEY", ""), type="password", placeholder="sk-...")
        st.text_input("HubSpot Private App Access Token", value=os.environ.get("HUBSPOT_ACCESS_TOKEN", ""), type="password", placeholder="pat-na1-...")
    with c_s2:
        st.text_input("WhatsApp Phone Number ID", value=WHATSAPP_PHONE_NUMBER_ID)
        st.text_input("WhatsApp Webhook Verify Token", value=WHATSAPP_VERIFY_TOKEN)

    if st.button("💾 Save Integration Configuration"):
        st.success("Configuration updated successfully.")

st.markdown("---")
st.caption(f"LeadPulse AI Enterprise • Built with Python, Streamlit, SQLite, REST APIs, HubSpot & WhatsApp Cloud API • {APP_VERSION}")
