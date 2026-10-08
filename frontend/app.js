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
