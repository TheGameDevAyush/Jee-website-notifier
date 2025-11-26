import requests
import time

# JEE Main 2026 URL
URL = "https://examinationservices.nic.in/JeeMainx2026/Root/Home.aspx?enc=Ei4cajBkK1gZSfgr53ImFVj34FesvYg1WX45sPjGXBqfcvMYv/FHq/Da9QEnq781"

# Your Discord Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1443205846766194710/VeSmRp_--onGIwlgNZhXS3Apwh3VRNDnQPLSukQi_MP4Pjx0yV1nf_DbjkvtxwA7_jp4"

def send_discord(message):
    try:
        requests.post(WEBHOOK_URL, json={"content": message})
    except Exception as e:
        print("Failed to send Discord message:", e)

def is_live():
    try:
        r = requests.get(URL, timeout=10)
        # Page is live when NOT showing service unavailable & status is OK
        if r.status_code == 200 and "service unavailable" not in r.text.lower():
            return True
        return False
    except:
        return False

print("🔍 Monitoring JEE Main 2026 page...")

while True:
    if is_live():
        msg = (
            "🚀 **JEE MAIN 2026 WEBSITE IS LIVE!**\n"
            f"🔗 {URL}"
        )
        send_discord(msg)
        print("📢 Discord notification sent!")
        break

    print("❌ Still down... checking again in 30 seconds...")
    time.sleep(30)
