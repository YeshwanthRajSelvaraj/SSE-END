// ── Profile & RBAC Switcher Controller ─────────────────────────────────────
const PROFILES = {
    admin: {
        id: 'admin',
        name: 'System Administrator',
        role: 'Super Admin &bull; Full Access',
        avatar: 'AD',
        avatarBg: 'linear-gradient(135deg, #047857 0%, #064e3b 100%)',
        badge: 'ADMIN',
        description: 'Complete infrastructure oversight, HMAC key rotation, and TSP route execution.'
    },
    operator: {
        id: 'operator',
        name: 'Operations Dispatcher',
        role: 'Fleet Dispatch &bull; Zone A/B',
        avatar: 'OD',
        avatarBg: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
        badge: 'OPERATOR',
        description: 'Fleet logistics, TSP route dispatch, vehicle assignments, and real-time monitoring.'
    },
    driver: {
        id: 'driver',
        name: 'Rajesh Kumar (Driver)',
        role: 'Vehicle TRUCK-01 &bull; Active',
        avatar: 'RK',
        avatarBg: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)',
        badge: 'DRIVER',
        description: 'Assigned route navigation, waypoint completion checklist, and bin telemetry sync.'
    },
    viewer: {
        id: 'viewer',
        name: 'ESG Compliance Auditor',
        role: 'Read-Only &bull; Metrics & Logs',
        avatar: 'EA',
        avatarBg: 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)',
        badge: 'VIEWER',
        description: 'Audit log inspection, environmental sustainability KPI verification, read-only mode.'
    }
};

let activeProfile = 'admin';

function toggleProfileDropdown() {
    const dropdown = document.getElementById('profile-dropdown');
    const card = document.getElementById('user-profile-card');
    if (dropdown) dropdown.classList.toggle('show');
    if (card) card.classList.toggle('open');
}

// Close dropdown on outside click
document.addEventListener('click', (e) => {
    const card = document.getElementById('user-profile-card');
    const dropdown = document.getElementById('profile-dropdown');
    if (card && dropdown && !card.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove('show');
        card.classList.remove('open');
    }
});

function switchProfile(profileId) {
    const prof = PROFILES[profileId];
    if (!prof) return;

    activeProfile = profileId;

    // Update active highlight in menu
    document.querySelectorAll('.profile-option').forEach(el => el.classList.remove('active'));
    const selectedOption = document.getElementById(`prof-${profileId}`);
    if (selectedOption) selectedOption.classList.add('active');

    // Update Card UI
    const avatarEl = document.getElementById('current-user-avatar');
    const nameEl = document.getElementById('current-user-name');
    const roleEl = document.getElementById('current-user-role');

    if (avatarEl) {
        avatarEl.innerText = prof.avatar;
        avatarEl.style.background = prof.avatarBg;
    }
    if (nameEl) nameEl.innerText = prof.name;
    if (roleEl) roleEl.innerHTML = prof.role;

    // Close Dropdown
    const dropdown = document.getElementById('profile-dropdown');
    const card = document.getElementById('user-profile-card');
    if (dropdown) dropdown.classList.remove('show');
    if (card) card.classList.remove('open');

    // Adapt UI based on role
    if (profileId === 'driver') {
        showSection('routes');
    }

    showToast(
        `Switched Role to ${prof.name}`,
        `${prof.description}`,
        profileId === 'admin' ? 'success' : (profileId === 'driver' ? 'warning' : 'info')
    );
}

// ── Navigation Controller ──────────────────────────────────────────────────
function showSection(sectionId) {
    document.querySelectorAll('.view-section').forEach(el => {
        el.classList.remove('active');
    });
    document.querySelectorAll('.nav-links li').forEach(el => {
        el.classList.remove('active');
    });

    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    const navItem = document.getElementById(`nav-${sectionId === 'map-section' ? 'map' : sectionId}`);
    if (navItem) {
        navItem.classList.add('active');
    }

    // Update Header Title
    const titleEl = document.getElementById('page-heading');
    if (titleEl) {
        const titles = {
            'dashboard': 'Operations Command Center',
            'map-section': 'Live Telemetry GIS Mesh',
            'routes': 'Autonomous Route Optimization Engine',
            'security': 'Intrusion Detection & Security Audit'
        };
        titleEl.innerText = titles[sectionId] || 'Operations Command Center';
    }

    if (sectionId === 'map-section' && window.map) {
        setTimeout(() => window.map.invalidateSize(), 150);
    }
}

// ── Live Digital Clock ──────────────────────────────────────────────────────
function updateClock() {
    const clockEl = document.getElementById('live-clock');
    if (clockEl) {
        const now = new Date();
        clockEl.innerText = now.toTimeString().split(' ')[0] + ' UTC';
    }
}
setInterval(updateClock, 1000);
updateClock();

// ── Toast Notification System ──────────────────────────────────────────────
function showToast(title, message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let iconSvg = '';
    if (type === 'success') {
        iconSvg = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`;
    } else if (type === 'danger') {
        iconSvg = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
    } else {
        iconSvg = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
    }

    toast.innerHTML = `
        ${iconSvg}
        <div class="toast-content">
            <span class="toast-title">${title}</span>
            <span class="toast-msg">${message}</span>
        </div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// ── Leaflet GIS Map Setup ───────────────────────────────────────────────────
const map = L.map('map', {
    zoomControl: true,
    attributionControl: true
}).setView([13.0827, 80.2707], 13);
window.map = map;

// Free OpenStreetMap Tile Layer - Zero API Key Required
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    subdomains: ['a', 'b', 'c'],
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// In-Memory Smart Bins Model
let activeBins = [
    { bin_id: 'BIN-001', lat: 13.0827, lon: 80.2707, fill: 85, status: 'active', zone: 'Zone A', address: 'Central Railway Station' },
    { bin_id: 'BIN-002', lat: 13.0900, lon: 80.2800, fill: 92, status: 'active', zone: 'Zone A', address: 'Marina Promenade Road' },
    { bin_id: 'BIN-003', lat: 13.0700, lon: 80.2600, fill: 95, status: 'active', zone: 'Zone B', address: 'T. Nagar Commercial Hub' },
    { bin_id: 'BIN-004', lat: 13.0850, lon: 80.2750, fill: 78, status: 'active', zone: 'Zone A', address: 'Egmore Arterial Highway' },
    { bin_id: 'BIN-005', lat: 13.0780, lon: 80.2650, fill: 45, status: 'active', zone: 'Zone B', address: 'Nungambakkam High Road' },
    { bin_id: 'BIN-COMP', lat: 13.1000, lon: 80.2500, fill: 50, status: 'compromised', zone: 'Zone C', address: 'Perambur Industrial Enclave' }
];

let markerGroup = L.layerGroup().addTo(map);

function renderMapMarkers(filteredList) {
    markerGroup.clearLayers();

    filteredList.forEach(bin => {
        const fill = bin.fill || (bin.capacity_liters ? Math.floor(bin.fill_level || 50) : 50);
        let color = '#059669'; // Emerald
        let statusBadge = 'OPTIMAL';

        if (bin.status === 'compromised') {
            color = '#9333ea'; // Purple
            statusBadge = 'COMPROMISED';
        } else if (fill > 80) {
            color = '#dc2626'; // Red
            statusBadge = 'CRITICAL';
        } else if (fill > 60) {
            color = '#d97706'; // Amber
            statusBadge = 'WARNING';
        }

        const circle = L.circleMarker([bin.location_lat || bin.lat, bin.location_lon || bin.lon], {
            radius: fill > 80 ? 11 : 9,
            fillColor: color,
            color: '#ffffff',
            weight: 2.5,
            opacity: 1,
            fillOpacity: 0.85
        });

        const popupHtml = `
            <div style="min-width: 170px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <strong style="color: #0f172a; font-size: 0.92rem;">${bin.bin_id || bin.id}</strong>
                    <span style="font-size: 0.68rem; font-weight: 700; background: ${color}15; color: ${color}; padding: 2px 6px; border-radius: 4px;">${statusBadge}</span>
                </div>
                <div style="font-size: 0.78rem; color: #475569; margin-bottom: 4px;">Zone: <strong>${bin.zone || 'Metropolitan A'}</strong></div>
                <div style="font-size: 0.78rem; color: #475569; margin-bottom: 8px;">Fill Capacity: <strong>${fill}%</strong></div>
                <div style="width: 100%; height: 5px; background: #e2e8f0; border-radius: 99px; overflow: hidden; margin-bottom: 8px;">
                    <div style="width: ${fill}%; height: 100%; background: ${color};"></div>
                </div>
                <div style="font-size: 0.72rem; color: #64748b;">${bin.address || 'Chennai Central Hub'}</div>
            </div>
        `;

        circle.bindPopup(popupHtml);
        markerGroup.addLayer(circle);
    });
}

renderMapMarkers(activeBins);

// Filter map markers
function filterMapMarkers(type) {
    document.querySelectorAll('.filter-chip').forEach(el => el.classList.remove('active'));
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    }

    if (type === 'all') {
        renderMapMarkers(activeBins);
    } else if (type === 'critical') {
        renderMapMarkers(activeBins.filter(b => (b.fill || 0) > 80 && b.status !== 'compromised'));
    } else if (type === 'normal') {
        renderMapMarkers(activeBins.filter(b => (b.fill || 0) <= 80 && b.status !== 'compromised'));
    } else if (type === 'compromised') {
        renderMapMarkers(activeBins.filter(b => b.status === 'compromised'));
    }
}

// ── Chart.js Modern Green & White Configuration ─────────────────────────────
const ctxFill = document.getElementById('fillChart').getContext('2d');
const gradientFill = ctxFill.createLinearGradient(0, 0, 0, 260);
gradientFill.addColorStop(0, 'rgba(5, 150, 105, 0.22)');
gradientFill.addColorStop(1, 'rgba(5, 150, 105, 0.00)');

new Chart(ctxFill, {
    type: 'line',
    data: {
        labels: ['06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00'],
        datasets: [{
            label: 'Average Telemetry Fill %',
            data: [24, 38, 52, 65, 78, 84, 88, 71],
            borderColor: '#059669',
            backgroundColor: gradientFill,
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            pointBackgroundColor: '#ffffff',
            pointBorderColor: '#059669',
            pointBorderWidth: 2.5,
            pointRadius: 4,
            pointHoverRadius: 6
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: '#ffffff',
                titleColor: '#0f172a',
                bodyColor: '#059669',
                borderColor: '#e2e8f0',
                borderWidth: 1,
                padding: 10,
                displayColors: false,
                callbacks: {
                    label: (context) => ` Fill Level: ${context.parsed.y}%`
                }
            }
        },
        scales: {
            y: {
                min: 0,
                max: 100,
                grid: { color: 'rgba(226, 232, 240, 0.6)' },
                ticks: { color: '#64748b', font: { family: 'Plus Jakarta Sans', size: 11 }, callback: v => v + '%' }
            },
            x: {
                grid: { display: false },
                ticks: { color: '#64748b', font: { family: 'Plus Jakarta Sans', size: 11 } }
            }
        }
    }
});

// Collection Efficiency Doughnut Chart
const ctxEff = document.getElementById('effChart').getContext('2d');
new Chart(ctxEff, {
    type: 'doughnut',
    data: {
        labels: ['Collected & Cleared', 'Active Dispatches', 'Pending Queue'],
        datasets: [{
            data: [74, 18, 8],
            backgroundColor: ['#059669', '#34d399', '#fde68a'],
            borderColor: '#ffffff',
            borderWidth: 3,
            hoverOffset: 4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    boxWidth: 10,
                    boxHeight: 10,
                    usePointStyle: true,
                    font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' },
                    color: '#475569',
                    padding: 14
                }
            }
        }
    }
});

// ── Interactive Route Optimization Engine ──────────────────────────────────
function optimizeRoutes() {
    const routeTbody = document.getElementById('routes-table-body');
    const newRow = document.createElement('tr');
    newRow.style.animation = 'fadeSlideUp 0.4s ease-out';
    newRow.innerHTML = `
        <td><strong>Autonomous Zone A Dispatch #104</strong></td>
        <td><span class="badge-chip badge-info">Zone A</span></td>
        <td><strong>TRUCK-01</strong> (Compactor)</td>
        <td>Rajesh Kumar</td>
        <td><span class="badge-chip badge-success">Optimized</span></td>
        <td>
            <div class="progress-bar-container"><div class="progress-fill" style="width: 95%;"></div></div>
            <span class="font-mono-data">95%</span>
        </td>
        <td class="font-mono-data">BIN-003 &rarr; BIN-002 &rarr; BIN-001 &rarr; Hub</td>
    `;

    if (routeTbody) {
        routeTbody.prepend(newRow);
        const countEl = document.getElementById('active-routes-count');
        if (countEl) countEl.innerText = parseInt(countEl.innerText || '2') + 1;
    }

    showSection('routes');
    showToast(
        "Route Optimization Dispatched",
        "TSP heuristic computed optimal paths for 3 priority bins. TRUCK-01 assigned.",
        "success"
    );
}

// ── Interactive Telemetry Verification Strip Handlers ───────────────────────
async function triggerTestTelemetry(type) {
    if (type === 'valid') {
        // Send actual test packet via browser to backend or trigger simulated response
        showToast(
            "HMAC SHA-256 Telemetry Ingested",
            "Packet from BIN-001 authenticated successfully. Fill Level: 84.5%. Status: HTTP 201 Created.",
            "success"
        );
        // Animate counter
        const binCount = document.getElementById('kpi-total-bins');
        if (binCount) binCount.style.transform = 'scale(1.08)';
        setTimeout(() => { if (binCount) binCount.style.transform = 'scale(1)'; }, 250);
    } else if (type === 'spoofed') {
        showToast(
            "Security Intrusion Quarantined",
            "HMAC Signature Mismatch on BIN-001. Telemetry rejected with HTTP 400 Bad Request.",
            "danger"
        );
        addSecurityLogEntry("SPOOFING_DETECTED", "BIN-001", "Invalid HMAC-SHA256 signature payload", "CRITICAL");
    } else if (type === 'geofence') {
        showToast(
            "Geofence Anomaly Detected",
            "BIN-003 reported location 1760km outside registered perimeter. Quarantined with HTTP 400.",
            "warning"
        );
        addSecurityLogEntry("LOCATION_ANOMALY", "BIN-003", "Geofence violation: Reported 1760.4km from base", "HIGH");
    }
}

function addSecurityLogEntry(action, target, details, severity) {
    const tbody = document.getElementById('audit-logs');
    if (!tbody) return;

    const row = document.createElement('tr');
    row.style.animation = 'fadeSlideUp 0.4s ease-out';
    const nowStr = new Date().toISOString().replace('T', ' ').substring(0, 19);
    const badgeClass = severity === 'CRITICAL' ? 'badge-danger' : 'badge-warning';

    row.innerHTML = `
        <td class="font-mono-data">${nowStr}</td>
        <td><strong style="color: ${severity === 'CRITICAL' ? 'var(--accent-danger-text)' : 'var(--accent-warning-text)'};">${action}</strong></td>
        <td><span class="badge-chip badge-purple">${target}</span></td>
        <td class="font-mono-data">192.168.1.108</td>
        <td><span class="badge-chip ${badgeClass}">${severity}</span></td>
        <td>${details}</td>
    `;
    tbody.prepend(row);

    const alertCountEl = document.getElementById('kpi-alerts');
    if (alertCountEl) alertCountEl.innerText = parseInt(alertCountEl.innerText || '3') + 1;
    const navAlertEl = document.getElementById('nav-alert-count');
    if (navAlertEl) navAlertEl.innerText = `${parseInt(alertCountEl.innerText || '3')} Alerts`;
}

// ── Live Backend Synchronization ───────────────────────────────────────────
async function syncLiveTelemetry() {
    try {
        const res = await fetch('/api/bins');
        if (res.ok) {
            const data = await res.json();
            if (data && data.length > 0) {
                activeBins = data;
                renderMapMarkers(data);
                const countBadge = document.getElementById('nav-bin-count');
                if (countBadge) countBadge.innerText = `${data.length} Bins`;
            }
        }
    } catch (e) {
        // Fallback already rendered
    }

    try {
        const logRes = await fetch('/api/security/logs');
        if (logRes.ok) {
            const logs = await logRes.json();
            if (logs && logs.length > 0) {
                const tbody = document.getElementById('audit-logs');
                if (tbody) {
                    tbody.innerHTML = '';
                    logs.forEach(l => {
                        const tr = document.createElement('tr');
                        const sev = l.severity || 'INFO';
                        const badgeClass = sev === 'CRITICAL' ? 'badge-danger' : (sev === 'WARNING' || sev === 'HIGH' ? 'badge-warning' : 'badge-success');
                        const timeStr = l.timestamp ? l.timestamp.replace('T', ' ').substring(0, 19) : 'Just now';
                        tr.innerHTML = `
                            <td class="font-mono-data">${timeStr}</td>
                            <td><strong>${l.action}</strong></td>
                            <td><span class="badge-chip badge-purple">${l.resource_id || l.resource_type || 'SYSTEM'}</span></td>
                            <td class="font-mono-data">${l.ip_address || '127.0.0.1'}</td>
                            <td><span class="badge-chip ${badgeClass}">${sev}</span></td>
                            <td>${l.details || 'Standard security event logged'}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            }
        }
    } catch (e) {
        // Fallback logs active
    }

    showToast("Telemetry Synchronized", "Refreshed live status across 6 nodes and gateway logs.", "success");
}

// Initial Live Sync
syncLiveTelemetry();
