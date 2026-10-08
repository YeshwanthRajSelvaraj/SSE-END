import os
import json
import base64
import requests

JIRA_URL = os.getenv("JIRA_URL", "https://claudebugbounty.atlassian.net")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "yeshselva1@gmail.com")
_cred = os.path.expanduser("~/Desktop/bugbounty/claude-jira-api.txt")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN") or (open(_cred).read().strip() if os.path.exists(_cred) else "")
PROJECT_KEY = os.getenv("JIRA_PROJECT", "ECO")

raw = f"{JIRA_EMAIL}:{JIRA_TOKEN}".encode("utf-8")
headers = {
    "Authorization": f"Basic {base64.b64encode(raw).decode('utf-8')}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

r = requests.get(f"{JIRA_URL}/rest/api/3/issue/createmeta?projectKeys={PROJECT_KEY}", headers=headers)
if r.status_code == 200:
    for proj in r.json().get("projects", []):
        print("Project:", proj["key"], proj["name"])
        for it in proj.get("issuetypes", []):
            print(f"  Type ID: {it['id']:<6} | Name: {it['name']}")
else:
    print("Error:", r.status_code, r.text)
