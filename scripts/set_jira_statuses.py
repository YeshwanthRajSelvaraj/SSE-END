import os
import sys
import json
import base64
import requests

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

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

def transition_issue(key, target_state_name):
    """Transitions an issue to target_state_name ('In Progress' or 'Done')."""
    try:
        r = requests.get(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions", headers=HEADERS, timeout=15)
    except Exception as e:
        print(f"  [{key}] Transition fetch error: {e}")
        return False
    if r.status_code != 200:
        print(f"Failed to fetch transitions for {key}: {r.status_code}")
        return False
        
    transitions = r.json().get("transitions", [])
    t_match = None
    target_lower = target_state_name.lower()
    
    if "progress" in target_lower:
        t_match = next((t for t in transitions if "progress" in t["name"].lower() or "start" in t["name"].lower()), None)
    elif "done" in target_lower:
        t_match = next((t for t in transitions if any(k in t["name"].lower() for k in ["done", "close", "resolv", "complete"])), None)
    else:
        t_match = next((t for t in transitions if target_lower in t["name"].lower()), None)
        
    if not t_match:
        # Check current status
        r_iss = requests.get(f"{JIRA_URL}/rest/api/3/issue/{key}?fields=status", headers=HEADERS, timeout=15)
        cur_status = r_iss.json().get("fields", {}).get("status", {}).get("name", "Unknown") if r_iss.status_code == 200 else "Unknown"
        if target_lower in cur_status.lower():
            print(f"  [{key}] Already in status: {cur_status}")
            return True
        print(f"  [{key}] Transition to '{target_state_name}' not directly available. Available: {[t['name'] for t in transitions]} (Current: {cur_status})")
        return False
        
    r_post = requests.post(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions", headers=HEADERS, json={"transition": {"id": t_match["id"]}}, timeout=15)
    if r_post.status_code in [200, 204]:
        print(f"  [{key}] Successfully transitioned to '{t_match['name']}'")
        return True
    else:
        print(f"  [{key}] Failed transition: {r_post.status_code} - {r_post.text}")
        return False

def main():
    print(f"=== Adjusting Jira Statuses: 5 In Progress, Rest Done ===")
    
    # 1. Fetch all issues in project ECO via Agile board
    r = requests.get(f"{JIRA_URL}/rest/agile/1.0/board/{BOARD_ID}/issue?maxResults=100", headers=HEADERS, timeout=15)
    if r.status_code != 200:
        print(f"Fetch failed: {r.status_code} - {r.text}")
        sys.exit(1)

        
    all_issues = r.json().get("issues", [])
    # Separate Epics vs Stories/Tasks
    stories_and_tasks = [i for i in all_issues if i["fields"]["issuetype"]["name"] in ["Story", "Task"]]
    epics = [i for i in all_issues if i["fields"]["issuetype"]["name"] == "Epic"]
    
    print(f"Found {len(stories_and_tasks)} Stories/Tasks and {len(epics)} Epics.")
    
    # Sort stories by key ID descending (newest first) or by story key
    def key_num(item):
        try:
            return int(item["key"].split("-")[1])
        except Exception:
            return 0
            
    stories_sorted = sorted(stories_and_tasks, key=key_num, reverse=True)
    
    # Pick exactly 5 key items to be "In Progress"
    # Choose 5 high-impact active stories representing ongoing operations
    in_progress_candidates = stories_sorted[:5]
    in_progress_keys = set(i["key"] for i in in_progress_candidates)
    
    print(f"\nSelected 5 issues for IN PROGRESS:")
    for i in in_progress_candidates:
        print(f"  - {i['key']}: {i['fields']['summary']}")
        
    print(f"\nApplying transitions...")
    # First, transition the 5 to In Progress
    for i in in_progress_candidates:
        transition_issue(i["key"], "In Progress")
        
    # Second, transition all remaining stories/tasks to Done
    for i in stories_sorted[5:]:
        transition_issue(i["key"], "Done")
        
    # Also ensure all Epics are Done or in valid state
    for ep in epics:
        transition_issue(ep["key"], "Done")

    # 3. Final Verification
    print(f"\n=== Final Board State Summary ===")
    r_verify = requests.get(f"{JIRA_URL}/rest/agile/1.0/board/{BOARD_ID}/issue?maxResults=100", headers=HEADERS, timeout=15)
    ip_count = 0

    done_count = 0
    other_count = 0
    for i in r_verify.json().get("issues", []):
        st = i["fields"]["status"]["name"]
        t = i["fields"]["issuetype"]["name"]
        summ = i["fields"]["summary"]
        if "progress" in st.lower():
            ip_count += 1
            print(f"[IN PROGRESS] {i['key']:<8} | {t:<7} | {summ}")
        elif any(k in st.lower() for k in ["done", "close", "resolv"]):
            done_count += 1
        else:
            other_count += 1
            print(f"[{st.upper()}] {i['key']:<8} | {t:<7} | {summ}")
            
    print(f"\nTotals: In Progress: {ip_count} | Done: {done_count} | Other: {other_count}")
    print(f"Board URL: {JIRA_URL}/jira/software/c/projects/{PROJECT_KEY}/boards/{BOARD_ID}")

if __name__ == "__main__":
    main()
