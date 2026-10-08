# Verification Checklist

- [ ] 1. Navigate to http://127.0.0.1:8001/
- [ ] 2. Verify removed UI elements (Breadcrumbs, HMAC pill, IoT strip)
- [ ] 3. Check sidebar for 'Security Gateway Lab' below 'Intrusion Logs' & click it
- [ ] 4. Test Security Gateway Lab triggers (Transmit Valid HMAC, Inject Spoofed Hash, Inject Geofence Breach)
- [ ] 5. Open profile dropdown
- [ ] 6. Switch to 'Rajesh Kumar (Field Driver)' -> verify RBAC & automatic view switch to Driver Manifest
- [ ] 7. Click 'Mark Collected' on first stop -> verify progress update & status chip
- [ ] 8. Switch to 'SOC Security Analyst' -> verify RBAC (Intrusion Logs & Lab visible, Optimized Routes hidden)
- [ ] 9. Switch to 'System Administrator'
- [ ] 10. Navigate to 'Optimized Routes', select Zone B/All Zones, click 'Calculate & Dispatch Route' -> observe TSP recalculation
- [ ] 11. Return to 'Live Telemetry Map' & verify map rendering
- [ ] 12. Complete report
