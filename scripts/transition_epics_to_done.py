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

raw = f"{JIRA_EMAIL}:{JIRA_TOKEN}".encode("utf-8")
HEADERS = {
    "Authorization": f"Basic {base64.b64encode(raw).decode('utf-8')}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def main():
    r = requests.get(f"{JIRA_URL}/rest/api/3/search/jql?jql=project={PROJECT_KEY}%20AND%20issuetype=Epic&fields=key,status", headers=HEADERS, timeout=15)
    if r.status_code != 200:
        print("Failed to get epics:", r.status_code, r.text)
        return
        
    epics = r.json().get("issues", [])
    print(f"Found {len(epics)} Epics to check...")
    for ep in epics:
        key = ep["key"]
        st = ep.get("fields", {}).get("status", {}).get("name", "Unknown")
        if "done" in st.lower():
            print(f"[{key}] Already Done.")
            continue
            
        r_t = requests.get(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions", headers=HEADERS, timeout=15)
        transitions = r_t.json().get("transitions", [])
        done_t = next((t for t in transitions if "done" in t["name"].lower()), None)
        if done_t:
            r_post = requests.post(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions", headers=HEADERS, json={"transition": {"id": done_t["id"]}}, timeout=15)
            if r_post.status_code in [200, 204]:
                print(f"[{key}] Successfully marked Done.")
            else:
                print(f"[{key}] Transition failed: {r_post.status_code}")
        else:
            print(f"[{key}] No Done transition available.")

if __name__ == "__main__":
    main()
