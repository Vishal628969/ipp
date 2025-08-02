import requests
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Replace with your AbuseIPDB API key
ABUSE_API_KEY = "ffc956c74f85b7220dc0913cd6866f1a28d8d0e8ca03a616d5c275848c7de5462b6e33f6c5d1be3c"

# Replace with your bot token
BOT_TOKEN = "8305345460:AAFFtOl1funHKy7URmNKOSrw-_rhy0xigZM"

# Datacenter ASNs to score higher risk
DATACENTER_ASNS = ["AS14061", "AS14618", "AS16509", "AS15169", "AS13335"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Welcome!\n\nSend /ip followed by the IP address you want to check.\nExample: /ip 1.1.1.1"
    )

async def check_ip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Please provide an IP address. Example: /ip 1.1.1.1")
        return

    ip = context.args[0]
    result = {
        "ip": ip,
        "country": "Unknown",
        "score": 0
    }

    # IP-API Check
    try:
        geo = requests.get(f"http://ip-api.com/json/{ip}").json()
        result["country"] = geo.get("country", "Unknown")
        asn = geo.get("as", "")
        if any(dc_asn in asn for dc_asn in DATACENTER_ASNS):
            result["score"] += 30
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching country info: {e}")

    # AbuseIPDB Check
    try:
        headers = {
            "Key": ABUSE_API_KEY,
            "Accept": "application/json"
        }
        response = requests.get("https://api.abuseipdb.com/api/v2/check", headers=headers, params={"ipAddress": ip, "maxAgeInDays": 90})
        data = response.json()
        if data['data']['abuseConfidenceScore'] >= 25:
            result["score"] += 40
    except Exception as e:
        await update.message.reply_text(f"❌ Error checking AbuseIPDB: {e}")

    result["score"] = min(result["score"], 100)

    # Risk Level Message
    if result["score"] <= 20:
        risk_level = "🟢 Low Risk"
    elif result["score"] <= 60:
        risk_level = "🟡 Medium Risk"
    else:
        risk_level = "🔴 High Risk"

    msg = (
        f"🔍 IP Check Result:\n\n"
        f"📍 IP: {result['ip']}\n"
        f"🌍 Country: {result['country']}\n"
        f"⚠️ Risk Score: {result['score']} / 100\n"
        f"🔎 Status: {risk_level}"
    )
    await update.message.reply_text(msg)

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ip", check_ip))

    app.run_polling()
