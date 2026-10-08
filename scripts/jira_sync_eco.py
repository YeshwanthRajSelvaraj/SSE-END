import os
import sys
import json
import base64
import requests

JIRA_URL = os.getenv("JIRA_URL", "https://claudebugbounty.atlassian.net")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "yeshselva1@gmail.com")
_default_cred_path = os.path.expanduser("~/Desktop/bugbounty/claude-jira-api.txt")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN") or (open(_default_cred_path).read().strip() if os.path.exists(_default_cred_path) else "")
PROJECT_KEY = os.getenv("JIRA_PROJECT", "ECO")
BOARD_ID = int(os.getenv("JIRA_BOARD_ID", "38"))

raw = f"{JIRA_EMAIL}:{JIRA_TOKEN}".encode("utf-8")
HEADERS = {
    "Authorization": f"Basic {base64.b64encode(raw).decode('utf-8')}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def adf_from_text(summary_text, desc_text, ac_text, points, assignee_role):
    """Creates rich Atlassian Document Format (ADF) representation."""
    content = []
    
    # User Story heading
    content.append({
        "type": "heading",
        "attrs": {"level": 2},
        "content": [{"type": "text", "text": "User Story / Objective"}]
    })
    content.append({
        "type": "paragraph",
        "content": [{"type": "text", "text": desc_text}]
    })
    
    # Meta block
    content.append({
        "type": "paragraph",
        "content": [
            {"type": "text", "text": "Story Points: ", "marks": [{"type": "strong"}]},
            {"type": "text", "text": str(points)},
            {"type": "text", "text": "  |  Assigned Role: ", "marks": [{"type": "strong"}]},
            {"type": "text", "text": assignee_role}
        ]
    })
    
    # Acceptance Criteria heading
    content.append({
        "type": "heading",
        "attrs": {"level": 2},
        "content": [{"type": "text", "text": "Acceptance Criteria (Gherkin DoD)"}]
    })
    
    for line in ac_text.split("\n"):
        if line.strip():
            content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": line.strip()}]
            })
            
    return {
        "type": "doc",
        "version": 1,
        "content": content
    }

def main():
    print(f"=== Jira Synchronization for {PROJECT_KEY} ===")
    print(f"Jira Instance: {JIRA_URL}")
    print(f"User: {JIRA_EMAIL}")
    
    # 1. Verify User & Project
    r_user = requests.get(f"{JIRA_URL}/rest/api/3/myself", headers=HEADERS)
    if r_user.status_code != 200:
        print(f"Auth failed: {r_user.status_code} - {r_user.text}")
        sys.exit(1)
    print(f"Authenticated as: {r_user.json().get('displayName')} ({r_user.json().get('accountId')})")
    
    # 2. Get existing sprints on board
    r_sprints = requests.get(f"{JIRA_URL}/rest/agile/1.0/board/{BOARD_ID}/sprint", headers=HEADERS)
    existing_sprints = {}
    if r_sprints.status_code == 200:
        for s in r_sprints.json().get("values", []):
            existing_sprints[s.get("name")] = s.get("id")
            print(f"Found Sprint: {s.get('name')} (ID: {s.get('id')}, State: {s.get('state')})")
    
    SPRINTS_DEF = [
        {
            "name": "ECO Sprint 1: Security & Auth",
            "goal": "Deliver authenticated HMAC-SHA256 ingestion, geofence tripwire, and automated CI/CD security gate."
        },
        {
            "name": "ECO Sprint 2: Route & Fleet",
            "goal": "Implement real geodesic Nearest-Neighbor TSP optimization, map polyline visualization, and interactive Driver Waypoint checklist."
        },
        {
            "name": "ECO Sprint 3: RBAC & Gateway",
            "goal": "Enforce strict profile boundaries (Driver isolated from security logs), add dedicated Security Gateway Lab tab, and package manifests."
        }
    ]
    
    sprint_ids = {}
    for s_def in SPRINTS_DEF:
        name = s_def["name"]
        if name in existing_sprints:
            sprint_ids[name] = existing_sprints[name]
            print(f"Reusing Sprint: '{name}' -> ID {sprint_ids[name]}")
        else:
            payload = {
                "name": name,
                "originBoardId": BOARD_ID,
                "goal": s_def["goal"]
            }
            r_create_s = requests.post(f"{JIRA_URL}/rest/agile/1.0/sprint", headers=HEADERS, json=payload)
            if r_create_s.status_code in [200, 201]:
                sid = r_create_s.json().get("id")
                sprint_ids[name] = sid
                print(f"Created Sprint: '{name}' -> ID {sid}")
            else:
                print(f"Failed to create sprint '{name}': {r_create_s.status_code} - {r_create_s.text}")

    # 3. Load or Search Existing Issues in Project ECO
    r_search = requests.get(f"{JIRA_URL}/rest/api/3/search?jql=project={PROJECT_KEY}&maxResults=100", headers=HEADERS)
    existing_issues = {}
    if r_search.status_code == 200:
        for iss in r_search.json().get("issues", []):
            existing_issues[iss["fields"]["summary"].strip()] = iss["key"]
            print(f"Existing Issue in {PROJECT_KEY}: {iss['key']} - {iss['fields']['summary']}")

    # 4. Create Epics
    EPICS = [
        {
            "key_alias": "ECO-EPIC-1",
            "epic_name": "Sensor Security",
            "summary": "EPIC 1: Cryptographic Anti-Spoofing & Gateway Integrity",
            "desc": "Hardware-level HMAC-SHA256 signing, anti-replay nonces, and physical geofence validation for IoT bin nodes."
        },
        {
            "key_alias": "ECO-EPIC-2",
            "epic_name": "Route Engine",
            "summary": "EPIC 2: Autonomous Route Optimization & Fleet Logistics",
            "desc": "Traveling Salesperson Problem (TSP) heuristic, vehicle allocation, and driver collection checklists."
        },
        {
            "key_alias": "ECO-EPIC-3",
            "epic_name": "RBAC Isolation",
            "summary": "EPIC 3: Role-Based Access Control (RBAC) & Boundary Isolation",
            "desc": "Least-privilege operational isolation between field truck drivers and SOC security analysts."
        },
        {
            "key_alias": "ECO-EPIC-4",
            "epic_name": "DevSecOps CI/CD",
            "summary": "EPIC 4: DevSecOps Pipeline & Infrastructure Orchestration",
            "desc": "Automated SAST scanning, container vulnerability verification, and production rollout."
        }
    ]
    
    epic_keys = {}
    for ep in EPICS:
        summary = ep["summary"]
        if summary in existing_issues:
            epic_keys[ep["key_alias"]] = existing_issues[summary]
            print(f"Epic already exists: {epic_keys[ep['key_alias']]} ({summary})")
        elif "EPIC 1: Anti-Spoofing & Sensor Cryptographic Validation" in existing_issues and ep["key_alias"] == "ECO-EPIC-1":
            epic_keys["ECO-EPIC-1"] = existing_issues["EPIC 1: Anti-Spoofing & Sensor Cryptographic Validation"]
            print(f"Reusing existing Epic 1: {epic_keys['ECO-EPIC-1']}")
        else:
            payload = {
                "fields": {
                    "project": {"key": PROJECT_KEY},
                    "summary": summary,
                    "issuetype": {"id": "10000"},  # Epic
                    "customfield_10011": ep["epic_name"],  # Epic Name
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": ep["desc"]}]
                            }
                        ]
                    }
                }
            }
            r_ep = requests.post(f"{JIRA_URL}/rest/api/3/issue", headers=HEADERS, json=payload)
            if r_ep.status_code in [200, 201]:
                k = r_ep.json().get("key")
                epic_keys[ep["key_alias"]] = k
                existing_issues[summary] = k
                print(f"Created Epic: {k} -> {summary}")
            else:
                print(f"Failed to create Epic '{summary}': {r_ep.status_code} - {r_ep.text}")

    # 5. User Stories & Tasks to create
    STORIES = [
        {
            "id": "ECO-101",
            "summary": "US-01: Implement HMAC-SHA256 Telemetry Signature Ingestion Pipeline",
            "epic_ref": "ECO-EPIC-1",
            "sprint_name": "ECO Sprint 1: Security & Auth",
            "type": "Story",
            "type_id": "10009",
            "points": 8,
            "priority": "Highest",
            "assignee_role": "Backend Security Engineer",
            "desc": "As a Security Operations Center Analyst, I want all incoming smart bin telemetry to be verified with HMAC-SHA256 using edge hardware device keys so that adversaries cannot spoof false fill levels.",
            "ac": "Given a telemetry packet with valid HMAC signature\nWhen it hits POST /api/iot/telemetry\nThen the gateway responds with HTTP 201 Created and saves reading.\n\nGiven a packet with tampered payload or forged signature\nWhen it hits POST /api/iot/telemetry\nThen the gateway responds with HTTP 400 Bad Request, marks node as COMPROMISED, and logs a CRITICAL audit event."
        },
        {
            "id": "ECO-102",
            "summary": "US-02: GIS Geofence Anomaly Detection Tripwire (50m Boundary)",
            "epic_ref": "ECO-EPIC-1",
            "sprint_name": "ECO Sprint 1: Security & Auth",
            "type": "Story",
            "type_id": "10009",
            "points": 5,
            "priority": "High",
            "assignee_role": "GIS Engineer",
            "desc": "As an Operations Dispatcher, I want reported bin coordinates to be verified against registered GPS anchors using geodesic calculation so that physically relocated or GPS-spoofed nodes are instantly detected.",
            "ac": "Given reported coordinates deviating > 50 meters from registered anchor\nWhen telemetry is ingested\nThen the gateway rejects the packet with HTTP 400 and logs LOCATION_ANOMALY with HIGH severity."
        },
        {
            "id": "ECO-201",
            "summary": "US-03: Greedy Nearest-Neighbor TSP Route Optimization Engine",
            "epic_ref": "ECO-EPIC-2",
            "sprint_name": "ECO Sprint 2: Route & Fleet",
            "type": "Story",
            "type_id": "10009",
            "points": 8,
            "priority": "High",
            "assignee_role": "Full-Stack Logistics Developer",
            "desc": "As a Municipal Fleet Dispatcher, I want an autonomous optimization algorithm to calculate the shortest round-trip path from Chennai Central Depot visiting all high-fill bins so that fuel and drive time are minimized.",
            "ac": "Given a set of bins with fill >= threshold\nWhen route optimizer is triggered\nThen it starts at Depot [13.0827, 80.2707], greedily visits the nearest unvisited node, returns to Depot, and outputs cumulative distance, duration, and carbon savings."
        },
        {
            "id": "ECO-202",
            "summary": "US-04: Interactive Field Driver Waypoint Manifest & Collection Checklist",
            "epic_ref": "ECO-EPIC-2",
            "sprint_name": "ECO Sprint 2: Route & Fleet",
            "type": "Story",
            "type_id": "10009",
            "points": 5,
            "priority": "High",
            "assignee_role": "Frontend Engineer",
            "desc": "As a Field Truck Driver (Rajesh Kumar), I want a turn-by-turn waypoint manifest where I can click [Mark Collected] at each bin so that progress is tracked and bin telemetry resets in real time.",
            "ac": "Given an active dispatched route\nWhen the driver clicks [Mark Collected] on a stop\nThen bin fill resets to 0%, stop is marked with a checkmark badge, and the route progress bar increments towards 100%."
        },
        {
            "id": "ECO-301",
            "summary": "US-05: Strict Profile RBAC Isolation: Driver vs Security Analyst Partitioning",
            "epic_ref": "ECO-EPIC-3",
            "sprint_name": "ECO Sprint 3: RBAC & Gateway",
            "type": "Story",
            "type_id": "10009",
            "points": 5,
            "priority": "Highest",
            "assignee_role": "Frontend & Security Engineer",
            "desc": "As a Chief Information Security Officer, I want field drivers to be strictly partitioned to their route manifest without access to intrusion logs, while security analysts have access to threat logs and gateway testing.",
            "ac": "Given active profile is 'Rajesh Kumar (Field Driver)'\nWhen navigating the sidebar\nThen Intrusion Logs and Security Gateway Lab are hidden, and unauthorized access attempts trigger the Access Control Barrier.\n\nGiven active profile is 'SOC Security Analyst'\nWhen inspecting the sidebar\nThen Intrusion Logs and Security Gateway Lab are visible, and Route Dispatching is hidden."
        },
        {
            "id": "ECO-302",
            "summary": "US-06: Dedicated Left Sidebar Tab: Security Gateway & Attack Lab",
            "epic_ref": "ECO-EPIC-3",
            "sprint_name": "ECO Sprint 3: RBAC & Gateway",
            "type": "Story",
            "type_id": "10009",
            "points": 5,
            "priority": "Medium",
            "assignee_role": "Full-Stack Security Developer",
            "desc": "As a Security Analyst, I want a dedicated left sidebar lab below Intrusion Logs to simulate valid HMAC packets, inject spoofed hashes, and test geofence violations with a live monospace terminal.",
            "ac": "Given the user navigates to the 'Security Gateway Lab' tab\nWhen clicking 'Inject Spoofed Hash'\nThen the terminal displays payload and HMAC mismatch in red, and a critical incident is added to Intrusion Logs."
        },
        {
            "id": "ECO-401",
            "summary": "TASK-01: GitHub Actions CI/CD Pipeline with Automated SAST & Container Scanning",
            "epic_ref": "ECO-EPIC-4",
            "sprint_name": "ECO Sprint 1: Security & Auth",
            "type": "Task",
            "type_id": "10042",
            "points": 3,
            "priority": "High",
            "assignee_role": "DevSecOps Engineer",
            "desc": "As a Release Manager, I want every git push to run automated unit tests, Bandit SAST security scans, and Trivy container vulnerability audits before merge.",
            "ac": "Given code pushed to main\nWhen GitHub Actions runs\nThen test-and-scan and build-container jobs must pass 100% green without critical vulnerabilities."
        }
    ]

    synced_issues = []

    for item in STORIES:
        summary = item["summary"]
        epic_target = epic_keys.get(item["epic_ref"])
        target_sprint_id = sprint_ids.get(item["sprint_name"])
        
        # Check if already created or existing
        iss_key = None
        for ex_sum, ex_key in existing_issues.items():
            if summary.lower() in ex_sum.lower() or item["id"].lower() in ex_sum.lower():
                iss_key = ex_key
                break
                
        if not iss_key:
            adf_doc = adf_from_text(summary, item["desc"], item["ac"], item["points"], item["assignee_role"])
            payload = {
                "fields": {
                    "project": {"key": PROJECT_KEY},
                    "summary": summary,
                    "issuetype": {"id": item["type_id"]},
                    "customfield_10014": epic_target,  # Epic Link
                    "customfield_10034": float(item["points"]),  # Story points
                    "priority": {"name": item["priority"]},
                    "description": adf_doc
                }
            }
            r_iss = requests.post(f"{JIRA_URL}/rest/api/3/issue", headers=HEADERS, json=payload)
            if r_iss.status_code in [200, 201]:
                iss_key = r_iss.json().get("key")
                existing_issues[summary] = iss_key
                print(f"Created Issue: {iss_key} ({item['type']}) -> {summary}")
            else:
                print(f"Failed to create '{summary}': {r_iss.status_code} - {r_iss.text}")
                continue
        else:
            print(f"Issue exists: {iss_key} -> {summary}")

        # Add to sprint
        if iss_key and target_sprint_id:
            r_sp = requests.post(f"{JIRA_URL}/rest/agile/1.0/sprint/{target_sprint_id}/issue", headers=HEADERS, json={"issues": [iss_key]})
            if r_sp.status_code in [200, 204]:
                print(f"  -> Added {iss_key} to Sprint ID {target_sprint_id} ({item['sprint_name']})")
            else:
                print(f"  -> Warning adding to sprint: {r_sp.status_code} - {r_sp.text}")

        # Transition to Done or In Progress
        r_trans = requests.get(f"{JIRA_URL}/rest/api/3/issue/{iss_key}/transitions", headers=HEADERS)
        if r_trans.status_code == 200:
            transitions = r_trans.json().get("transitions", [])
            done_t = next((t for t in transitions if any(k in t["name"].lower() for k in ["done", "close", "resolv", "complete"])), None)
            if done_t:
                r_post_t = requests.post(f"{JIRA_URL}/rest/api/3/issue/{iss_key}/transitions", headers=HEADERS, json={"transition": {"id": done_t["id"]}})
                if r_post_t.status_code in [200, 204]:
                    print(f"  -> Transitioned {iss_key} to {done_t['name']}")
                else:
                    print(f"  -> Transition failed: {r_post_t.status_code}")
        
        synced_issues.append({
            "key": iss_key,
            "summary": summary,
            "type": item["type"],
            "points": item["points"],
            "sprint": item["sprint_name"],
            "epic": epic_target,
            "url": f"{JIRA_URL}/browse/{iss_key}"
        })

    print("\n=== Synchronization Completed Successfully! ===")
    print(f"Board URL: {JIRA_URL}/jira/software/c/projects/{PROJECT_KEY}/boards/{BOARD_ID}")
    for item in synced_issues:
        print(f"  - [{item['key']}] {item['summary']} | SP: {item['points']} | Sprint: {item['sprint']} | {item['url']}")

    # Save summary report
    report = {
        "jira_instance": JIRA_URL,
        "project_key": PROJECT_KEY,
        "board_id": BOARD_ID,
        "board_url": f"{JIRA_URL}/jira/software/c/projects/{PROJECT_KEY}/boards/{BOARD_ID}",
        "sprints": SPRINTS_DEF,
        "epics": epic_keys,
        "synced_issues": synced_issues
    }
    with open("docs/jira_live_sync_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("\nSaved report to docs/jira_live_sync_report.json")

if __name__ == "__main__":
    main()
