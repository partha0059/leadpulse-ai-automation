/**
 * LeadPulse AI — Shared Navigation, UI Helpers & Toast Notifications
 */

const NAV_ITEMS = [
    { section: "OVERVIEW" },
    { path: "/", label: "Executive Dashboard", icon: `<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>` },
    { section: "LEAD LIFECYCLE" },
    { path: "/discovery", label: "Market Discovery", icon: `<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>` },
    { path: "/enrichment", label: "Contact Enrichment & DNS", icon: `<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>` },
    { path: "/crm", label: "CRM Pipeline & HubSpot", icon: `<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>` },
    { section: "OMNICHANNEL & AI" },
    { path: "/sequences", label: "Outreach & Approval Queue", icon: `<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>` },
    { path: "/whatsapp", label: "WhatsApp BANT Suite", icon: `<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>` },
    { path: "/copilot", label: "Sales Copilot & Dossiers", icon: `<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4z"/><circle cx="9" cy="14" r="1"/><circle cx="15" cy="14" r="1"/></svg>` },
    { section: "SYSTEM" },
    { path: "/architecture", label: "Architecture & Webhooks", icon: `<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>` }
];

function renderSidebar(activePath) {
    const sidebar = document.getElementById("sidebar");
    if (!sidebar) return;

    const navHtml = NAV_ITEMS.map(item => {
        if (item.section) {
            return `<div class="nav-section-label">${item.section}</div>`;
        }
        const isActive = item.path === activePath ? "active" : "";
        return `
            <a href="${item.path}" class="nav-link ${isActive}">
                ${item.icon}
                <span>${item.label}</span>
            </a>
        `;
    }).join("");

    sidebar.innerHTML = `
        <div class="sidebar-brand">
            <div class="brand-logo">⚡</div>
            <div class="brand-text">
                <h1>LeadPulse AI</h1>
                <span>Enterprise BD Platform</span>
            </div>
        </div>
        <nav class="sidebar-nav">${navHtml}</nav>
        <div class="sidebar-footer">
            <div class="status-row">
                <span class="status-dot"><span class="dot"></span>SQLite DB</span>
                <span style="color:#10b981;font-weight:600;">Online</span>
            </div>
            <div class="status-row">
                <span class="status-dot"><span class="dot"></span>HubSpot API</span>
                <span>Adapter Ready</span>
            </div>
            <div class="status-row">
                <span class="status-dot"><span class="dot"></span>WhatsApp Cloud</span>
                <span>v19.0 Active</span>
            </div>
        </div>
    `;
}

function showToast(message, isError = false) {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.className = "toast-container";
        document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    toast.className = `toast ${isError ? "error" : ""}`;
    toast.innerHTML = `<span>${isError ? "⚠️" : "✅"}</span><span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.25s ease";
        setTimeout(() => toast.remove(), 260);
    }, 3400);
}

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function tempBadge(temp) {
    const t = (temp || "Cold").toLowerCase();
    if (t === "hot") return `<span class="badge badge-hot">🔥 Hot</span>`;
    if (t === "warm") return `<span class="badge badge-warm">🟡 Warm</span>`;
    return `<span class="badge badge-cold">❄️ Cold</span>`;
}

function statusBadge(status) {
    const s = (status || "").toLowerCase();
    if (s === "approved" || s === "deliverable" || s === "qualified" || s === "closed-won" || s === "success") {
        return `<span class="badge badge-approved">${escapeHtml(status)}</span>`;
    }
    if (s === "pending review" || s === "risky" || s === "contacted" || s === "enriched") {
        return `<span class="badge badge-pending">${escapeHtml(status)}</span>`;
    }
    if (s === "rejected" || s === "invalid" || s === "closed-lost" || s === "failed") {
        return `<span class="badge badge-rejected">${escapeHtml(status)}</span>`;
    }
    return `<span class="badge badge-neutral">${escapeHtml(status)}</span>`;
}
