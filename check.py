# check.py
import requests
import time
import os
import base64
import json

URL = "https://examinationservices.nic.in/JeeMainx2026/Root/Home.aspx?enc=Ei4cajBkK1gZSfgr53ImFVj34FesvYg1WX45sPjGXBqfcvMYv/FHq/Da9QEnq781"
WEBHOOK_URL = "https://discord.com/api/webhooks/1443205846766194710/VeSmRp_--onGIwlgNZhXS3Apwh3VRNDnQPLSukQi_MP4Pjx0yV1nf_DbjkvtxwA7_jp4"

# Controls
RETRY_ATTEMPTS = 3
RETRY_BACKOFFS = [5, 10, 20]  # seconds between retries within a single action run

# Optional: when True the script will attempt to disable the scheduled cron
# in .github/workflows/notifier.yml after successfully notifying.
# To enable, set the environment variable DISABLE_ON_SUCCESS=true in the workflow.
DISABLE_ON_SUCCESS = os.getenv("DISABLE_ON_SUCCESS", "false").lower() in ("1", "true", "yes")

def send_discord(content):
    payload = {
        "content": content
    }
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print("Failed to send Discord message:", e)
        return False

def probe_once():
    try:
        r = requests.get(URL, timeout=10)
        status = r.status_code
        text = r.text.lower() if r.text else ""
        print("HTTP", status)
        # Consider site live only if 200 and not containing "service unavailable"
        if status == 200 and "service unavailable" not in text:
            return True, status, text
        return False, status, text
    except Exception as e:
        print("Request failed:", e)
        return False, None, None

def is_live_with_retries():
    for i in range(RETRY_ATTEMPTS):
        live, status, text = probe_once()
        if live:
            print("Site appears LIVE (attempt", i+1, ")")
            return True, status
        if i < len(RETRY_BACKOFFS):
            wait = RETRY_BACKOFFS[i]
        else:
            wait = RETRY_BACKOFFS[-1]
        print(f"Not live yet (attempt {i+1}). Waiting {wait}s before next try.")
        time.sleep(wait)
    return False, status

# Optional: disable the schedule in the workflow file to avoid duplicate alerts.
# This uses the GitHub Contents API to update .github/workflows/notifier.yml
def disable_workflow_schedule():
    github_token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")  # e.g. "username/reponame"
    path = ".github/workflows/notifier.yml"
    if not github_token or not repo:
        print("GITHUB_TOKEN or GITHUB_REPOSITORY not present; cannot auto-disable workflow.")
        return False

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }

    # Get current file content (to get sha)
    url_get = f"https://api.github.com/repos/{repo}/contents/{path}"
    resp = requests.get(url_get, headers=headers, timeout=15)
    if resp.status_code != 200:
        print("Failed to fetch workflow file:", resp.status_code, resp.text)
        return False

    data = resp.json()
    sha = data.get("sha")
    content_b64 = data.get("content", "")
    content = base64.b64decode(content_b64).decode("utf-8")

    # Replace schedule block. This is a simple, conservative replacement:
    # convert the schedule to an empty array to stop runs.
    new_content = content
    if "schedule:" in content:
        # naive but practical replacement — replace first occurrence of schedule block
        new_content = content.replace('schedule:\n    - cron: "*/1 * * * *"', "schedule: []  # disabled by notifier")
    else:
        print("No schedule block found in workflow; skipping modification.")
        return False

    if new_content == content:
        print("Replacement didn't change content; skipping commit.")
        return False

    new_b64 = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

    put_payload = {
        "message": "ci: disable scheduled runs after successful notification",
        "content": new_b64,
        "sha": sha,
        "committer": {
            "name": "github-actions[bot]",
            "email": "41898282+github-actions[bot]@users.noreply.github.com"
        }
    }

    url_put = f"https://api.github.com/repos/{repo}/contents/{path}"
    put = requests.put(url_put, headers=headers, json=put_payload, timeout=15)
    if put.status_code in (200, 201):
        print("Workflow schedule disabled successfully.")
        return True
    else:
        print("Failed to update workflow file:", put.status_code, put.text)
        return False

def main():
    live, status = is_live_with_retries()
    if live:
        message = f"🚀 **JEE MAIN 2026 WEBSITE IS LIVE!**\n🔗 {URL}\nHTTP status: {status}"
        if send_discord(message):
            print("Discord notification sent.")
            if DISABLE_ON_SUCCESS:
                print("DISABLE_ON_SUCCESS is true — attempting to disable workflow schedule.")
                disable_workflow_schedule()
        else:
            print("Failed to send discord notification despite site being live.")
    else:
        print("Site still down after retries. Status:", status)
        # Optionally you could send a "still down" message, but that will spam the channel every run.
        # If you want periodic down reports, enable below:
        # send_discord(f"⚠️ JEE site still down (status: {status}) - will keep monitoring.")

if __name__ == "__main__":
    main()