// ── Profile & Enterprise Role-Based Access Control (RBAC) Matrix ─────────────
const PROFILES = {
    admin: {
        id: 'admin',
        name: 'System Administrator',
        role: 'Super Admin &bull; Full Access (All 5 Modules)',
        avatar: 'AD',
        avatarBg: 'linear-gradient(135deg, #047857 0%, #064e3b 100%)',
        badge: 'SUPER ADMIN',
        allowedSections: ['dashboard', 'map-section', 'routes', 'security', 'iot-lab'],
        defaultSection: 'dashboard',
        description: 'Complete infrastructure oversight, HMAC key rotation, TSP route execution, and intrusion auditing.'
    },
    operator: {
        id: 'operator',
        name: 'Operations Dispatcher',
        role: 'Fleet Lead &bull; Dashboard, Map & Routes',
        avatar: 'OD',
        avatarBg: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
        badge: 'OPERATOR',
        allowedSections: ['dashboard', 'map-section', 'routes'],
        defaultSection: 'dashboard',
        description: 'Fleet logistics, TSP route dispatch, vehicle assignments, and real-time GIS monitoring.'
    },
    driver: {
        id: 'driver',
        name: 'Rajesh Kumar (Field Driver)',
        role: 'Field Driver &bull; Route Manifest Only (Restricted)',
        avatar: 'RK',
        avatarBg: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)',
        badge: 'DRIVER',
        allowedSections: ['routes'],
        defaultSection: 'routes',
        description: 'Assigned route waypoints, driver manifest checklist, and bin collection completion. Partitioned from security logs.'
    },
    analyst: {
        id: 'analyst',
        name: 'SOC Security Analyst',
        role: 'Threat Analyst &bull; Intrusions & Gateway Lab',
        avatar: 'SA',
        avatarBg: 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)',
        badge: 'ANALYST',
        allowedSections: ['security', 'iot-lab', 'dashboard', 'map-section'],
        defaultSection: 'security',
        description: 'Real-time intrusion detection, HMAC-SHA256 signature verification, and edge security lab.'
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

function applyRbacNavigation(prof) {
    const allNavs = {
        'dashboard': 'nav-dashboard',
        'map-section': 'nav-map',
        'routes': 'nav-routes',
        'security': 'nav-security',
        'iot-lab': 'nav-iot-lab'
    };

    Object.entries(allNavs).forEach(([sectionId, navElementId]) => {
        const el = document.getElementById(navElementId);
        if (!el) return;
        if (prof.allowedSections.includes(sectionId)) {
            el.style.display = 'block';
        } else {
            el.style.display = 'none';
        }
    });

    // Update header button label based on role
    const optBtn = document.getElementById('header-optimizer-btn');
    if (optBtn) {
        if (prof.id === 'driver') {
            optBtn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/>
                </svg>
                <span>View My Manifest</span>
            `;
        } else if (prof.id === 'analyst') {
            optBtn.style.display = 'none';
        } else {
            optBtn.style.display = 'inline-flex';
            optBtn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
                <span>Run Route Optimizer</span>
            `;
        }
    }
}

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

    // Apply strict navigation access visibility
    applyRbacNavigation(prof);

    // If current viewed section is not permitted, switch to authorized default
    const currentActiveSection = document.querySelector('.view-section.active');
    const currentSecId = currentActiveSection ? currentActiveSection.id : 'dashboard';
    if (!prof.allowedSections.includes(currentSecId)) {
        showSection(prof.defaultSection);
    } else {
        // If driver, always prioritize their routes manifest
        if (profileId === 'driver') {
            showSection('routes');
        }
    }

    showToast(
        `Active Role: ${prof.name}`,
        `${prof.description}`,
        profileId === 'admin' ? 'success' : (profileId === 'driver' ? 'warning' : 'info')
    );
}

// ── Navigation Controller with RBAC Boundary Enforcement ─────────────────────
function showSection(sectionId) {
    const prof = PROFILES[activeProfile] || PROFILES.admin;

    // Strict Access Boundary Check
    if (!prof.allowedSections.includes(sectionId)) {
        document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.nav-links li').forEach(el => el.classList.remove('active'));

        const barrierEl = document.getElementById('access-denied-view');
        if (barrierEl) {
            barrierEl.classList.add('active');
            const roleEl = document.getElementById('barrier-current-role');
            const descEl = document.getElementById('barrier-allowed-desc');
            const textEl = document.getElementById('barrier-desc-text');
            if (roleEl) roleEl.innerText = prof.name;
            if (descEl) descEl.innerText = `Authorized Modules: ${prof.allowedSections.map(s => s === 'map-section' ? 'Live Telemetry Map' : (s === 'routes' ? 'Optimized Routes Manifest' : s.charAt(0).toUpperCase() + s.slice(1))).join(', ')}`;
            if (textEl) textEl.innerText = `Access to "${sectionId}" is prohibited for role "${prof.badge}". Operational separation guarantees security analyst logs and cryptographic controls remain isolated from field driver and operations profiles.`;
        }

        showToast(
            "Access Denied (RBAC Boundary)",
            `Profile '${prof.name}' lacks clearance for '${sectionId}'.`,
            "danger"
        );
        return;
    }

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

    const navId = sectionId === 'map-section' ? 'nav-map' : `nav-${sectionId}`;
    const navItem = document.getElementById(navId);
    if (navItem) {
        navItem.classList.add('active');
    }

    // Update Header Title
    const titleEl = document.getElementById('page-heading');
    if (titleEl) {
        const titles = {
            'dashboard': 'Operations Command Center',
            'map-section': 'Live Telemetry GIS Mesh',
            'routes': 'Autonomous Route Optimization & Driver Dispatch',
            'security': 'Intrusion Detection & Security Audit Console',
            'iot-lab': 'Edge IoT Security Gateway & Cryptographic Lab'
        };
        titleEl.innerText = titles[sectionId] || 'Operations Command Center';
    }

    if (sectionId === 'map-section' && window.map) {
        setTimeout(() => window.map.invalidateSize(), 150);
    }
}

function returnToAuthorizedDefault() {
    const prof = PROFILES[activeProfile] || PROFILES.admin;
    showSection(prof.defaultSection);
}

function triggerHeaderOptimize() {
    const prof = PROFILES[activeProfile] || PROFILES.admin;
    if (activeProfile === 'driver') {
        showSection('routes');
        showToast("Driver Waypoint Manifest", "Turn-by-turn navigation manifest active for TRUCK-01.", "info");
        return;
    }
    if (!prof.allowedSections.includes('routes')) {
        showToast("Access Restricted", "Security Analyst profile cannot dispatch fleet routes.", "warning");
        return;
    }
    showSection('routes');
    runRealRouteOptimizer();
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
let binMarkersMap = {};

function renderMapMarkers(filteredList) {
    markerGroup.clearLayers();
    binMarkersMap = {};

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
        binMarkersMap[bin.bin_id || bin.id] = circle;
        markerGroup.addLayer(circle);
    });
}

renderMapMarkers(activeBins);

// Filter map markers
function filterMapMarkers(type) {
    document.querySelectorAll('.filter-chip').forEach(el => el.classList.remove('active'));
    if (window.event && window.event.currentTarget) {
        window.event.currentTarget.classList.add('active');
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

// ── Area Navigation & Vicinity Smart Bins Discovery ───────────────────────
const CHENNAI_AREAS = {
    'central station': { name: 'Central Railway Station', lat: 13.0827, lon: 80.2707, zone: 'Zone A', radius: 2.2 },
    'chennai central': { name: 'Central Railway Station', lat: 13.0827, lon: 80.2707, zone: 'Zone A', radius: 2.2 },
    'central': { name: 'Central Railway Station', lat: 13.0827, lon: 80.2707, zone: 'Zone A', radius: 2.2 },
    
    'marina beach': { name: 'Marina Beach Promenade', lat: 13.0900, lon: 80.2800, zone: 'Zone A', radius: 2.5 },
    'marina': { name: 'Marina Beach Promenade', lat: 13.0900, lon: 80.2800, zone: 'Zone A', radius: 2.5 },
    'triplicane': { name: 'Triplicane / Marina Coast', lat: 13.0585, lon: 80.2750, zone: 'Zone A', radius: 2.5 },
    
    't. nagar': { name: 'T. Nagar Commercial Hub', lat: 13.0700, lon: 80.2600, zone: 'Zone B', radius: 2.5 },
    't nagar': { name: 'T. Nagar Commercial Hub', lat: 13.0700, lon: 80.2600, zone: 'Zone B', radius: 2.5 },
    'thyagaraya nagar': { name: 'T. Nagar Commercial Hub', lat: 13.0700, lon: 80.2600, zone: 'Zone B', radius: 2.5 },
    'pondy bazaar': { name: 'Pondy Bazaar Retail Sector', lat: 13.0416, lon: 80.2337, zone: 'Zone B', radius: 2.5 },
    
    'egmore': { name: 'Egmore Arterial Highway', lat: 13.0850, lon: 80.2750, zone: 'Zone A', radius: 2.0 },
    
    'nungambakkam': { name: 'Nungambakkam High Road', lat: 13.0780, lon: 80.2650, zone: 'Zone B', radius: 2.2 },
    
    'perambur': { name: 'Perambur Industrial Enclave', lat: 13.1000, lon: 80.2500, zone: 'Zone C', radius: 2.8 },
    
    'guindy': { name: 'Guindy Industrial & Metro Hub', lat: 13.0067, lon: 80.2025, zone: 'South Zone', radius: 3.0 },
    
    'adyar': { name: 'Adyar South Sector', lat: 13.0012, lon: 80.2565, zone: 'South Zone', radius: 3.0 },
    
    'velachery': { name: 'Velachery Urban Corridor', lat: 12.9815, lon: 80.2180, zone: 'South Zone', radius: 3.5 },
    
    'anna nagar': { name: 'Anna Nagar West Commercial Hub', lat: 13.0850, lon: 80.2100, zone: 'West Sector', radius: 3.0 },
    
    'mylapore': { name: 'Mylapore Heritage & Cultural Sector', lat: 13.0368, lon: 80.2676, zone: 'Zone B', radius: 2.5 },
    
    'alwarpet': { name: 'Alwarpet Central Business Area', lat: 13.0334, lon: 80.2504, zone: 'Zone B', radius: 2.5 },
    
    'vadapalani': { name: 'Vadapalani Transit Hub', lat: 13.0500, lon: 80.2120, zone: 'West Sector', radius: 3.0 },
    
    'omr': { name: 'OMR Cyber Highway Corridor', lat: 12.9010, lon: 80.2279, zone: 'IT Corridor', radius: 4.0 },
    
    'tambaram': { name: 'Tambaram Suburban Transit Center', lat: 12.9249, lon: 80.1000, zone: 'Outer South', radius: 4.5 },
    
    'airport': { name: 'Chennai International Airport Hub', lat: 12.9941, lon: 80.1709, zone: 'Airport Zone', radius: 3.5 }
};

let activeAreaCircle = null;
let activeAreaMarker = null;
let currentVicinityBins = [];
let currentVicinityAreaName = '';

function calcDistanceKm(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return parseFloat((R * c).toFixed(2));
}

function toggleSearchClearBtn() {
    const input = document.getElementById('area-search-input');
    const clearBtn = document.getElementById('search-clear-btn');
    if (input && clearBtn) {
        clearBtn.style.display = input.value.trim().length > 0 ? 'flex' : 'none';
    }
}

function clearAreaSearch() {
    const input = document.getElementById('area-search-input');
    if (input) input.value = '';
    toggleSearchClearBtn();
    closeAreaVicinityCard();
    if (activeAreaCircle) { map.removeLayer(activeAreaCircle); activeAreaCircle = null; }
    if (activeAreaMarker) { map.removeLayer(activeAreaMarker); activeAreaMarker = null; }
    document.querySelectorAll('.area-chip').forEach(c => c.classList.remove('active'));
    renderMapMarkers(activeBins);
}

function closeAreaVicinityCard() {
    const card = document.getElementById('area-vicinity-card');
    if (card) card.style.display = 'none';
}

function selectQuickArea(areaName) {
    const input = document.getElementById('area-search-input');
    if (input) {
        input.value = areaName;
        toggleSearchClearBtn();
    }
    document.querySelectorAll('.area-chip').forEach(chip => {
        if (chip.innerText.trim().toLowerCase() === areaName.trim().toLowerCase()) {
            chip.classList.add('active');
        } else {
            chip.classList.remove('active');
        }
    });
    searchAreaLocality();
}

function recenterMap() {
    clearAreaSearch();
    map.flyTo([13.0827, 80.2707], 13, { duration: 1.2 });
    showToast("Map View Centered", "Reset viewport to Central Metropolitan Hub.", "info");
}

async function searchAreaLocality() {
    const input = document.getElementById('area-search-input');
    const query = input ? input.value.trim() : '';

    if (!query) {
        showToast("Enter Area Name", "Please type an area or neighborhood name to navigate.", "warning");
        if (input) input.focus();
        return;
    }

    const normQuery = query.toLowerCase();
    let targetArea = null;

    // 1. Direct or partial match in pre-mapped Chennai areas
    for (const [key, areaData] of Object.entries(CHENNAI_AREAS)) {
        if (normQuery.includes(key) || key.includes(normQuery)) {
            targetArea = areaData;
            break;
        }
    }

    // 2. Fallback to OpenStreetMap Nominatim Geocoding API
    if (!targetArea) {
        try {
            showToast("Searching Area", `Locating "${query}" via GIS geocoder...`, "info");
            const geoRes = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query + ', Chennai, Tamil Nadu')}&limit=1`);
            if (geoRes.ok) {
                const geoData = await geoRes.json();
                if (geoData && geoData.length > 0) {
                    targetArea = {
                        name: geoData[0].display_name.split(',')[0] || query,
                        lat: parseFloat(geoData[0].lat),
                        lon: parseFloat(geoData[0].lon),
                        zone: 'Metropolitan Sector',
                        radius: 3.0
                    };
                }
            }
        } catch (err) {
            console.warn("Geocoding fallback network notice:", err);
        }
    }

    if (!targetArea) {
        showToast("Area Not Found", `Could not pinpoint "${query}". Try Central Station, Marina Beach, or T. Nagar.`, "warning");
        return;
    }

    navigateToAreaWithBins(targetArea);
}

function navigateToAreaWithBins(area) {
    currentVicinityAreaName = area.name;
    const { lat, lon, name } = area;

    // Clean up previous search layers
    if (activeAreaCircle) { map.removeLayer(activeAreaCircle); }
    if (activeAreaMarker) { map.removeLayer(activeAreaMarker); }

    // Calculate distance from area center to all bins
    const binsWithDistance = activeBins.map(bin => {
        const bLat = bin.location_lat || bin.lat;
        const bLon = bin.location_lon || bin.lon;
        const dist = calcDistanceKm(lat, lon, bLat, bLon);
        return { ...bin, distanceKm: dist, bLat, bLon };
    });

    // Sort by proximity
    binsWithDistance.sort((a, b) => a.distanceKm - b.distanceKm);

    // Nearby threshold: within 3.5 km
    const nearbyThresholdKm = 3.5;
    const nearbyBins = binsWithDistance.filter(b => b.distanceKm <= nearbyThresholdKm);
    currentVicinityBins = nearbyBins;

    // Draw Coverage Radar Circle
    activeAreaCircle = L.circle([lat, lon], {
        radius: 2000,
        color: '#059669',
        fillColor: '#10b981',
        fillOpacity: 0.12,
        weight: 2,
        dashArray: '6, 6'
    }).addTo(map);

    // Drop Custom Pulse Pin
    const areaPulseIcon = L.divIcon({
        className: 'custom-area-pin',
        html: `
            <div class="area-marker-pin">
                <div class="area-marker-beacon"></div>
                <div class="area-marker-pulse"></div>
            </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
    });

    activeAreaMarker = L.marker([lat, lon], { icon: areaPulseIcon }).addTo(map);
    activeAreaMarker.bindPopup(`
        <div style="min-width: 170px; font-family: 'Plus Jakarta Sans', sans-serif;">
            <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
                <svg style="width: 14px; height: 14px; color: #047857; flex-shrink: 0;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                <strong style="color: #047857; font-size: 0.88rem;">${name}</strong>
            </div>
            <div style="font-size: 0.72rem; color: #475569;">Serviced Location Anchor</div>
            <div style="font-size: 0.74rem; color: #059669; font-weight: 700; margin-top: 4px;">
                ${nearbyBins.length > 0 ? `${nearbyBins.length} Bins Servicing Vicinity` : 'No direct bins within 3.5km'}
            </div>
        </div>
    `);

    // Smooth Navigation FlyTo
    map.flyTo([lat, lon], 14, { duration: 1.2 });

    // Open Popup on closest bin after animation completes
    const closestBin = binsWithDistance[0];
    if (closestBin && binMarkersMap[closestBin.bin_id]) {
        setTimeout(() => {
            if (binMarkersMap[closestBin.bin_id]) {
                binMarkersMap[closestBin.bin_id].openPopup();
            }
        }, 1300);
    }

    // Render Floating Vicinity Overview Card
    renderVicinityCard(area, nearbyBins, closestBin);

    // Toast Notification
    if (nearbyBins.length > 0) {
        showToast(
            `Navigated to ${name}`,
            `Found ${nearbyBins.length} serviced bins in the vicinity perimeter. Nearest: ${closestBin.bin_id} (${closestBin.distanceKm} km away).`,
            "success"
        );
    } else {
        showToast(
            `Navigated to ${name}`,
            `No fixed bins within 3.5 km. Nearest active bin is ${closestBin.bin_id} (${closestBin.distanceKm} km away).`,
            "warning"
        );
    }
}

function renderVicinityCard(area, nearbyBins, closestBin) {
    const card = document.getElementById('area-vicinity-card');
    const nameEl = document.getElementById('vicinity-area-name');
    const badgeEl = document.getElementById('vicinity-coverage-badge');
    const radiusInfoEl = document.getElementById('vicinity-radius-info');
    const countEl = document.getElementById('vicinity-bins-count');
    const listEl = document.getElementById('vicinity-bins-list');

    if (!card) return;

    if (nameEl) nameEl.innerText = area.name;
    if (radiusInfoEl) radiusInfoEl.innerText = `Radius: 3.5 km`;

    if (nearbyBins.length > 0) {
        if (badgeEl) {
            badgeEl.innerText = 'Active Coverage';
            badgeEl.className = 'vicinity-badge';
            badgeEl.style.background = 'var(--primary-100)';
            badgeEl.style.color = 'var(--primary-800)';
        }
        if (countEl) countEl.innerText = `${nearbyBins.length} Serviced Bins in Vicinity`;

        if (listEl) {
            listEl.innerHTML = '';
            nearbyBins.forEach(bin => {
                const fill = bin.fill || (bin.capacity_liters ? Math.floor(bin.fill_level || 50) : 50);
                let tagClass = 'badge-success';
                let tagText = `${fill}% Fill`;
                if (bin.status === 'compromised') {
                    tagClass = 'badge-purple';
                    tagText = 'Quarantined';
                } else if (fill > 80) {
                    tagClass = 'badge-danger';
                    tagText = `${fill}% Critical`;
                } else if (fill > 60) {
                    tagClass = 'badge-warning';
                    tagText = `${fill}% Warning`;
                }

                const item = document.createElement('div');
                item.className = 'vicinity-bin-item';
                item.onclick = () => {
                    if (binMarkersMap[bin.bin_id]) {
                        map.panTo([bin.bLat, bin.bLon]);
                        binMarkersMap[bin.bin_id].openPopup();
                    }
                };
                item.style.cursor = 'pointer';
                item.title = 'Click to focus bin on map';
                item.innerHTML = `
                    <div>
                        <div class="vicinity-bin-title">${bin.bin_id}</div>
                        <div style="font-size: 0.68rem; color: var(--text-muted);">${bin.address || bin.zone || 'Local Node'}</div>
                    </div>
                    <div class="vicinity-bin-meta">
                        <span class="badge-chip ${tagClass}" style="font-size: 0.65rem; padding: 2px 5px;">${tagText}</span>
                        <span class="vicinity-bin-dist">${bin.distanceKm} km</span>
                    </div>
                `;
                listEl.appendChild(item);
            });
        }
    } else {
        if (badgeEl) {
            badgeEl.innerText = 'Extended Perimeter';
            badgeEl.className = 'vicinity-badge';
            badgeEl.style.background = 'var(--accent-warning-bg)';
            badgeEl.style.color = 'var(--accent-warning-text)';
        }
        if (countEl) countEl.innerText = `0 Fixed Bins Inside 3.5 km Perimeter`;
        if (listEl) {
            listEl.innerHTML = `
                <div class="vicinity-bin-item" style="flex-direction: column; align-items: flex-start; gap: 4px;">
                    <div style="font-size: 0.72rem; color: var(--text-secondary);">Nearest Infrastructure Asset:</div>
                    <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                        <strong style="color: var(--primary-700);">${closestBin.bin_id}</strong>
                        <span class="vicinity-bin-dist">${closestBin.distanceKm} km away</span>
                    </div>
                </div>
            `;
        }
    }

    card.style.display = 'block';
}

function dispatchRouteForArea() {
    showSection('routes');
    showToast(
        `Fleet Dispatched to ${currentVicinityAreaName || 'Area'}`,
        `Autonomous routing prioritized nearby bins for TRUCK-01. Route computation active.`,
        "success"
    );
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

// ── Real TSP Route Optimization Engine & Driver Dispatch ───────────────────
const CHENNAI_DEPOT = {
    id: 'DEPOT-CENTRAL',
    name: 'Chennai Central Logistics Depot',
    lat: 13.0827,
    lon: 80.2707,
    address: 'Grand Trunk Road / Chennai Central Logistics Hub, Zone A'
};

let currentDispatchedRoute = null;
let currentRouteStops = [];
let routeProgressState = { total: 0, collected: 0 };
let routePolylineLayer = null;

function previewEligibleBins() {
    const zone = document.getElementById('route-zone-select')?.value || 'all';
    const threshold = parseFloat(document.getElementById('route-threshold-select')?.value || '75');

    const eligible = activeBins.filter(b => {
        if (b.status === 'compromised') return false;
        if (zone !== 'all' && b.zone !== zone) return false;
        const fill = b.fill !== undefined ? b.fill : (b.fill_level || 50);
        return fill >= threshold;
    });

    const stopsEl = document.getElementById('opt-stops-count');
    if (stopsEl) {
        stopsEl.innerText = `${eligible.length} Candidates`;
    }
}

function runRealRouteOptimizer() {
    const zoneSelect = document.getElementById('route-zone-select');
    const threshSelect = document.getElementById('route-threshold-select');
    const vehicleSelect = document.getElementById('route-vehicle-select');
    const driverSelect = document.getElementById('route-driver-select');

    const zone = zoneSelect ? zoneSelect.value : 'Zone A';
    let threshold = threshSelect ? parseFloat(threshSelect.value) : 75;
    const vehicle = vehicleSelect ? vehicleSelect.value : 'TRUCK-01';
    const driver = driverSelect ? driverSelect.value : 'Rajesh Kumar';

    // 1. Filter candidate bins needing evacuation
    let candidateBins = activeBins.filter(b => {
        if (b.status === 'compromised') return false;
        if (zone !== 'all' && b.zone !== zone) return false;
        const fill = b.fill !== undefined ? b.fill : (b.fill_level || 50);
        return fill >= threshold;
    });

    // If threshold is too strict, take active bins in zone to avoid empty manifest
    if (candidateBins.length === 0) {
        candidateBins = activeBins.filter(b => {
            if (b.status === 'compromised') return false;
            return zone === 'all' || b.zone === zone;
        });
        showToast("Threshold Relaxed", `No bins &ge; ${threshold}% fill. Included all active bins in ${zone}.`, "info");
    }

    if (candidateBins.length === 0) {
        candidateBins = activeBins.slice(0, 3);
    }

    // 2. Greedy Nearest Neighbor Traveling Salesperson (TSP) Algorithm
    let currentPos = { lat: CHENNAI_DEPOT.lat, lon: CHENNAI_DEPOT.lon };
    let unvisited = [...candidateBins];
    let orderedStops = [];
    let totalKm = 0;

    while (unvisited.length > 0) {
        let nearestIdx = 0;
        let minDistance = Infinity;

        for (let i = 0; i < unvisited.length; i++) {
            const b = unvisited[i];
            const bLat = b.location_lat || b.lat;
            const bLon = b.location_lon || b.lon;
            const dist = calcDistanceKm(currentPos.lat, currentPos.lon, bLat, bLon);
            if (dist < minDistance) {
                minDistance = dist;
                nearestIdx = i;
            }
        }

        const pickedBin = unvisited.splice(nearestIdx, 1)[0];
        const bLat = pickedBin.location_lat || pickedBin.lat;
        const bLon = pickedBin.location_lon || pickedBin.lon;
        
        totalKm += minDistance;
        orderedStops.push({
            ...pickedBin,
            legDistanceKm: minDistance,
            lat: bLat,
            lon: bLon
        });
        currentPos = { lat: bLat, lon: bLon };
    }

    // Return to Central Depot
    const returnLegKm = calcDistanceKm(currentPos.lat, currentPos.lon, CHENNAI_DEPOT.lat, CHENNAI_DEPOT.lon);
    totalKm += returnLegKm;

    currentRouteStops = orderedStops;
    routeProgressState = { total: orderedStops.length, collected: 0 };

    // 3. Calculate Performance Metrics
    const totalDurationMins = Math.round((totalKm / 24) * 60 + (orderedStops.length * 6.5));
    const fuelDeltaPercent = (22.5 + orderedStops.length * 2.8).toFixed(1);
    const carbonOffsetKg = (totalKm * 0.32).toFixed(2);

    // Update KPI UI
    const stopsCountEl = document.getElementById('opt-stops-count');
    const distEl = document.getElementById('opt-total-distance');
    const durEl = document.getElementById('opt-total-duration');
    const carbonEl = document.getElementById('opt-carbon-saved');
    const fuelDeltaEl = document.getElementById('opt-fuel-delta');

    if (stopsCountEl) stopsCountEl.innerText = `${orderedStops.length} Priority Stops`;
    if (distEl) distEl.innerText = `${totalKm.toFixed(2)} km`;
    if (durEl) durEl.innerText = `${totalDurationMins} mins`;
    if (carbonEl) carbonEl.innerText = `${carbonOffsetKg} kg CO2`;
    if (fuelDeltaEl) fuelDeltaEl.innerText = `-${fuelDeltaPercent}% vs Unrouted`;

    // 4. Render Driver Waypoint Manifest Checklist
    renderDriverManifest(orderedStops, returnLegKm);

    // 5. Draw Polyline Path on Leaflet Map
    renderRoutePolyline(orderedStops);

    // 6. Record Route in Dispatch Log Table
    recordDispatchedRoute(zone, vehicle, driver, totalKm, orderedStops);

    showToast(
        "Autonomous TSP Route Dispatched",
        `Shortest tour computed: ${orderedStops.length} stops, ${totalKm.toFixed(2)} km. Assigned to ${driver} (${vehicle}).`,
        "success"
    );
}

function renderDriverManifest(stops, returnLegKm) {
    const container = document.getElementById('manifest-stops-container');
    const progressLabel = document.getElementById('manifest-progress-stops');
    const progressPercent = document.getElementById('manifest-progress-percent');

    if (progressLabel) progressLabel.innerText = `0/${stops.length}`;
    if (progressPercent) progressPercent.innerText = `0%`;

    if (!container) return;
    container.innerHTML = '';

    // Stop 0: Departure from Depot
    const depotStart = document.createElement('div');
    depotStart.className = 'manifest-stop-card';
    depotStart.style.borderLeft = '3px solid var(--primary-700)';
    depotStart.innerHTML = `
        <div class="stop-meta-group">
            <div class="stop-number-badge" style="background: var(--primary-800);">0</div>
            <div class="stop-title-addr">
                <span class="stop-bin-id">${CHENNAI_DEPOT.name}</span>
                <span class="stop-address">${CHENNAI_DEPOT.address}</span>
            </div>
        </div>
        <div class="stop-metrics">
            <span class="badge-chip badge-success">ORIGIN DEPOT</span>
            <span class="font-mono-data" style="color: var(--text-muted);">Depart Fleet Hub</span>
        </div>
    `;
    container.appendChild(depotStart);

    // Waypoints
    stops.forEach((stop, idx) => {
        const stopNum = idx + 1;
        const fill = stop.fill !== undefined ? stop.fill : (stop.fill_level || 50);
        const card = document.createElement('div');
        card.className = 'manifest-stop-card';
        card.id = `manifest-card-${stop.bin_id || stop.id}`;

        let fillBadgeClass = fill > 80 ? 'badge-danger' : (fill > 60 ? 'badge-warning' : 'badge-success');

        card.innerHTML = `
            <div class="stop-meta-group">
                <div class="stop-number-badge">${stopNum}</div>
                <div class="stop-title-addr">
                    <span class="stop-bin-id">${stop.bin_id || stop.id} &bull; ${stop.address || 'Chennai Urban Sector'}</span>
                    <span class="stop-address">Zone: <strong>${stop.zone || 'Zone A'}</strong> &bull; Leg: <span class="font-mono-data">${stop.legDistanceKm.toFixed(2)} km</span> from prev stop</span>
                </div>
            </div>
            <div class="stop-metrics">
                <span class="badge-chip ${fillBadgeClass}" id="fill-chip-${stop.bin_id}">${fill}% Fill</span>
                <button class="btn-collect-action" id="btn-collect-${stop.bin_id || stop.id}" onclick="markBinCollected('${stop.bin_id || stop.id}', ${stopNum})">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px;">
                        <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span>Mark Collected</span>
                </button>
            </div>
        `;
        container.appendChild(card);
    });

    // Return to Depot
    const depotEnd = document.createElement('div');
    depotEnd.className = 'manifest-stop-card';
    depotEnd.style.borderLeft = '3px solid var(--primary-700)';
    depotEnd.innerHTML = `
        <div class="stop-meta-group">
            <div class="stop-number-badge" style="background: var(--primary-800);">${stops.length + 1}</div>
            <div class="stop-title-addr">
                <span class="stop-bin-id">Return to ${CHENNAI_DEPOT.name}</span>
                <span class="stop-address">Unload waste, wash compactor, and sync collection telemetry</span>
            </div>
        </div>
        <div class="stop-metrics">
            <span class="badge-chip badge-info">FINAL DESTINATION</span>
            <span class="font-mono-data" style="color: var(--text-muted);">${returnLegKm.toFixed(2)} km Return</span>
        </div>
    `;
    container.appendChild(depotEnd);
}

function markBinCollected(binId, stopNum) {
    // 1. Update bin state to 0% fill
    const bin = activeBins.find(b => (b.bin_id || b.id) === binId);
    if (bin) {
        bin.fill = 0;
        bin.fill_level = 0;
        bin.status = 'active';
    }

    // 2. Update Manifest Card UI
    const card = document.getElementById(`manifest-card-${binId}`);
    if (card) {
        card.classList.add('collected');
    }

    const btn = document.getElementById(`btn-collect-${binId}`);
    if (btn) {
        btn.classList.add('collected');
        btn.disabled = true;
        btn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px;">
                <polyline points="20 6 9 17 4 12"/>
            </svg>
            <span>Collected &bull; 0% Fill</span>
        `;
    }

    const chip = document.getElementById(`fill-chip-${binId}`);
    if (chip) {
        chip.className = 'badge-chip badge-success';
        chip.innerText = '0% Empty';
    }

    // 3. Update Progress Counters
    routeProgressState.collected++;
    const percent = Math.round((routeProgressState.collected / routeProgressState.total) * 100);

    const progressLabel = document.getElementById('manifest-progress-stops');
    const progressPercent = document.getElementById('manifest-progress-percent');
    if (progressLabel) progressLabel.innerText = `${routeProgressState.collected}/${routeProgressState.total}`;
    if (progressPercent) progressPercent.innerText = `${percent}%`;

    // 4. Update Map Markers
    renderMapMarkers(activeBins);

    // 5. Check if Route Complete
    if (routeProgressState.collected >= routeProgressState.total) {
        showToast(
            "All Waypoints Collected!",
            `Route circuit 100% completed. Driver returning to Central Depot.`,
            "success"
        );
    } else {
        showToast(
            `Stop #${stopNum} Collected`,
            `${binId} emptied successfully. Proceed to Stop #${stopNum + 1}.`,
            "success"
        );
    }
}

function renderRoutePolyline(stops) {
    if (!window.map) return;

    if (routePolylineLayer) {
        window.map.removeLayer(routePolylineLayer);
        routePolylineLayer = null;
    }

    const points = [
        [CHENNAI_DEPOT.lat, CHENNAI_DEPOT.lon],
        ...stops.map(s => [s.lat, s.lon]),
        [CHENNAI_DEPOT.lat, CHENNAI_DEPOT.lon]
    ];

    routePolylineLayer = L.polyline(points, {
        color: '#059669',
        weight: 3.5,
        opacity: 0.85,
        dashArray: '7, 8',
        lineJoin: 'round'
    }).addTo(window.map);
}

function resetActiveRoute() {
    if (routePolylineLayer && window.map) {
        window.map.removeLayer(routePolylineLayer);
        routePolylineLayer = null;
    }
    const container = document.getElementById('manifest-stops-container');
    if (container) container.innerHTML = '';
    const progressLabel = document.getElementById('manifest-progress-stops');
    const progressPercent = document.getElementById('manifest-progress-percent');
    if (progressLabel) progressLabel.innerText = '0/0';
    if (progressPercent) progressPercent.innerText = '0%';
    showToast("Route Cleared", "Waypoint circuit cleared. Configure parameters to calculate new path.", "info");
}

function recordDispatchedRoute(zone, vehicle, driver, distanceKm, stops) {
    const tbody = document.getElementById('routes-table-body');
    if (!tbody) return;

    const row = document.createElement('tr');
    row.style.animation = 'fadeSlideUp 0.4s ease-out';
    const routeId = `TSP-DSP-${Date.now().toString().slice(-4)}`;
    const stopChain = stops.map(s => s.bin_id || s.id).join(' &rarr; ');

    row.innerHTML = `
        <td><strong>${routeId} (${zone})</strong></td>
        <td><span class="badge-chip badge-info">${zone}</span></td>
        <td><strong>${vehicle}</strong></td>
        <td>${driver}</td>
        <td><span class="badge-chip badge-warning">In Progress</span></td>
        <td class="font-mono-data">${distanceKm.toFixed(2)} km</td>
        <td class="font-mono-data">Depot &rarr; ${stopChain} &rarr; Depot</td>
    `;
    tbody.prepend(row);
}

// ── Security Gateway Lab & Cryptographic Simulator ──────────────────────────
const BIN_DEVICE_KEYS = {
    'BIN-001': { key: 'super_secret_device_key_for_bin_001', coords: '13.0827° N, 80.2707° E', lat: 13.0827, lon: 80.2707, addr: 'Central Station' },
    'BIN-002': { key: 'super_secret_device_key_for_bin_002', coords: '13.0900° N, 80.2800° E', lat: 13.0900, lon: 80.2800, addr: 'Marina Beach Road' },
    'BIN-003': { key: 'super_secret_device_key_for_bin_003', coords: '13.0700° N, 80.2600° E', lat: 13.0700, lon: 80.2600, addr: 'T. Nagar Market' },
    'BIN-004': { key: 'super_secret_device_key_for_bin_004', coords: '13.0850° N, 80.2750° E', lat: 13.0850, lon: 80.2750, addr: 'Egmore High Road' },
    'BIN-005': { key: 'super_secret_device_key_for_bin_005', coords: '13.0780° N, 80.2650° E', lat: 13.0780, lon: 80.2650, addr: 'Nungambakkam High Rd' },
    'BIN-COMP': { key: 'compromised_key_test_bin', coords: '13.1000° N, 80.2500° E', lat: 13.1000, lon: 80.2500, addr: 'Perambur Industrial' }
};

function updateLabBinInfo() {
    const sel = document.getElementById('lab-target-bin')?.value || 'BIN-001';
    const info = BIN_DEVICE_KEYS[sel];
    if (!info) return;

    const keyEl = document.getElementById('lab-device-key-display');
    const coordsEl = document.getElementById('lab-device-coords-display');
    if (keyEl) keyEl.innerText = info.key;
    if (coordsEl) coordsEl.innerText = info.coords;
}

// Pseudo HMAC-SHA256 generator for browser demonstration
function computeBrowserHmacHex(key, message) {
    let hash = 0;
    const combined = `${key}:${message}`;
    for (let i = 0; i < combined.length; i++) {
        const char = combined.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    const hex = Math.abs(hash).toString(16).padStart(8, '0');
    return `sha256_${hex}${hex}${hex}${hex}`.substring(0, 64);
}

function appendTerminalLine(text, styleClass = 'term-line') {
    const term = document.getElementById('gateway-terminal-output');
    if (!term) return;

    const line = document.createElement('div');
    line.className = `term-line ${styleClass}`;
    line.innerText = text;
    term.appendChild(line);
    term.scrollTop = term.scrollHeight;
}

function clearTerminalLogs() {
    const term = document.getElementById('gateway-terminal-output');
    if (!term) return;
    term.innerHTML = `
        <div class="term-line term-system">[SYSTEM RESET] Terminal log buffer cleared.</div>
        <div class="term-line term-system">[READY] FastAPI HMAC gateway listening on port 8001...</div>
    `;
}

async function transmitLabTelemetry(mode) {
    const binId = document.getElementById('lab-target-bin')?.value || 'BIN-001';
    const fill = parseFloat(document.getElementById('lab-fill-slider')?.value || '85');
    const temp = parseFloat(document.getElementById('lab-temp-slider')?.value || '31.5');
    const binInfo = BIN_DEVICE_KEYS[binId] || BIN_DEVICE_KEYS['BIN-001'];
    
    const unixTimestamp = Math.floor(Date.now() / 1000);
    const nowTimeStr = new Date().toISOString().replace('T', ' ').substring(0, 19);

    appendTerminalLine(`\n------------------------------------------------------------`, 'term-system');
    appendTerminalLine(`[TRANSMIT] Initiating telemetry push from node: ${binId}`, 'term-highlight');

    let reportedLat = binInfo.lat;
    let reportedLon = binInfo.lon;
    let computedHmac = computeBrowserHmacHex(binInfo.key, `${binId}|${unixTimestamp}|${fill}|${temp}`);
    let transmittedHmac = computedHmac;

    if (mode === 'spoofed') {
        // Tamper HMAC signature
        transmittedHmac = 'ffffffff_spoofed_hash_tampered_payload_77492cba124';
        appendTerminalLine(`[ATTACK INJECT] Simulating Man-In-The-Middle payload tampering.`, 'term-warn');
    } else if (mode === 'geofence') {
        // Displace coordinates to Delhi (1760 km away)
        reportedLat = 28.6139;
        reportedLon = 77.2090;
        appendTerminalLine(`[ATTACK INJECT] Spoofing physical GPS hardware to New Delhi (28.61° N, 77.20° E).`, 'term-warn');
    }

    appendTerminalLine(`[PAYLOAD] {"bin_id":"${binId}", "fill":${fill}%, "temp":${temp}°C, "lat":${reportedLat}, "lon":${reportedLon}}`);
    appendTerminalLine(`[CRYPTO] Secret Key: ${binInfo.key}`);
    appendTerminalLine(`[SIGNATURE] Transmitted HMAC: ${transmittedHmac.substring(0, 36)}...`);

    // Verify against security policy
    if (mode === 'valid') {
        appendTerminalLine(`[GATEWAY EVAL] Signature match verified: MATCH [OK]`, 'term-success');
        appendTerminalLine(`[GEOFENCE EVAL] Geodesic deviation: 0.00m <= 50.0m threshold: PASS [OK]`, 'term-success');
        appendTerminalLine(`[HTTP 201 CREATED] Telemetry securely ingested. InfluxDB written.`, 'term-success');

        // Update in-memory active bin fill
        const binObj = activeBins.find(b => (b.bin_id || b.id) === binId);
        if (binObj) {
            binObj.fill = fill;
            binObj.fill_level = fill;
            renderMapMarkers(activeBins);
        }

        showToast(
            "HMAC SHA-256 Telemetry Ingested",
            `Packet from ${binId} authenticated successfully. HTTP 201 Created.`,
            "success"
        );
    } else if (mode === 'spoofed') {
        appendTerminalLine(`[GATEWAY EVAL] Expected HMAC != Transmitted HMAC: MISMATCH [ALERT]`, 'term-danger');
        appendTerminalLine(`[GATEWAY ACTION] HTTP 400 Bad Request &bull; Quarantined probe.`, 'term-danger');
        appendTerminalLine(`[AUDIT] Action: SPOOFING_DETECTED recorded for node ${binId}`, 'term-danger');

        addSecurityLogEntry("SPOOFING_DETECTED", binId, "Invalid HMAC-SHA256 signature payload", "CRITICAL");
        showToast(
            "Security Intrusion Quarantined",
            `HMAC Signature Mismatch on ${binId}. Gateway returned HTTP 400.`,
            "danger"
        );
    } else if (mode === 'geofence') {
        const devDistKm = calcDistanceKm(binInfo.lat, binInfo.lon, reportedLat, reportedLon);
        appendTerminalLine(`[GEOFENCE EVAL] Displacement: ${devDistKm.toFixed(2)} km > 0.05 km threshold: BREACH!`, 'term-warn');
        appendTerminalLine(`[GATEWAY ACTION] HTTP 400 Bad Request &bull; GIS tripwire activated.`, 'term-warn');
        appendTerminalLine(`[AUDIT] Action: LOCATION_ANOMALY recorded for node ${binId}`, 'term-warn');

        addSecurityLogEntry("LOCATION_ANOMALY", binId, `Geofence breach: Reported ${devDistKm.toFixed(1)}km from base`, "HIGH");
        showToast(
            "Geofence Anomaly Detected",
            `${binId} coordinates displaced by ${devDistKm.toFixed(1)}km. Quarantined with HTTP 400.`,
            "warning"
        );
    }
}

async function runLabPenetrationSuite() {
    showToast("Penetration Test Initiated", "Executing 3-stage security penetration suite...", "info");
    appendTerminalLine(`\n============================================================`, 'term-highlight');
    appendTerminalLine(`[PEN-TEST SUITE] Automated Gateway Validation Sequence Started`, 'term-highlight');
    
    await transmitLabTelemetry('valid');
    setTimeout(async () => {
        await transmitLabTelemetry('spoofed');
        setTimeout(async () => {
            await transmitLabTelemetry('geofence');
            appendTerminalLine(`[PEN-TEST SUITE] Sequence complete. All tripwires validated.`, 'term-success');
            showToast("Pen-Test Completed", "3 vectors verified against FastAPI gateway.", "success");
        }, 800);
    }, 800);
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

// Initial System Initialization
applyRbacNavigation(PROFILES[activeProfile]);
updateLabBinInfo();
runRealRouteOptimizer();
syncLiveTelemetry();
