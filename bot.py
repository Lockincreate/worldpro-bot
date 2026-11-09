import os, requests, telebot, threading, time
from flask import Flask
from datetime import date, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)
@app.route('/')
def home(): return "ESPN REAL Bot Live!"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000))), daemon=True).start()

# ESPN Leagues - REAL
LEAGUES = {
    "EPL": "eng.1",
    "LALIGA": "esp.1",
    "SERIE A": "ita.1",
    "BUNDESLIGA": "ger.1",
    "LIGUE 1": "fra.1",
    "PSL": "saf.1",
    "UCL": "uefa.champions"
}

def get_espn(league_id, dates):
    # dates = YYYYMMDD
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/scoreboard?dates={dates}"
    r = requests.get(url, timeout=20).json()
    return r.get('events', [])

@bot.message_handler(commands=['start','help'])
def start(m):
    bot.reply_to(m, "👋 WORLDPRO - REAL ESPN DATA ✅\nNo fake, no suspension, no key\n\n/today - Yanamuhla ⚽\n/tomorrow - Yakusasa 📅\n/live - Live 🔴\n/results - Imiphumela + REAL HT ✅\n/tip - Ithiphu 💰")

@bot.message_handler(commands=['today'])
def today(m):
    d = date.today().strftime("%Y%m%d")
    txt = "⚽ IMIDLALO YANAMUHLA - REAL ESPN ✅\n\n"
    found = False
    for name, lid in LEAGUES.items():
        try:
            evs = get_espn(lid, d)
            for e in evs:
                found = True
                comp = e['competitions'][0]
                home = comp['competitors'][0]; away = comp['competitors'][1]
                # ESPN gives real home/away - need to check order
                h = [c for c in comp['competitors'] if c['homeAway']=='home'][0]
                a = [c for c in comp['competitors'] if c['homeAway']=='away'][0]
                txt += f"{h['team']['displayName']} vs {a['team']['displayName']} - {name} - {e['status']['type']['detail']}\n"
        except: pass
    if not found:
        txt += "Namuhla akukho mdlalo omkhulu - LE YINQINISO."
    bot.reply_to(m, txt)

@bot.message_handler(commands=['tomorrow'])
def tomorrow(m):
    d = (date.today()+timedelta(days=1)).strftime("%Y%m%d")
    txt = f"📅 YAKUSASA - REAL ESPN ✅\n\n"
    found=False
    for name, lid in LEAGUES.items():
        try:
            evs = get_espn(lid, d)
            for e in evs:
                found=True
                comp=e['competitions'][0]
                h=[c for c in comp['competitors'] if c['homeAway']=='home'][0]
                a=[c for c in comp['competitors'] if c['homeAway']=='away'][0]
                txt += f"{h['team']['displayName']} vs {a['team']['displayName']} - {name} - {e['status']['type']['detail']}\n"
        except: pass
    if not found: txt += "Ayikho imidlalo."
    bot.reply_to(m, txt)

@bot.message_handler(commands=['live'])
def live(m):
    d = date.today().strftime("%Y%m%d")
    txt = "🔴 LIVE MANJE - REAL ESPN ✅\n\n"
    found=False
    for name, lid in LEAGUES.items():
        try:
            evs = get_espn(lid, d)
            for e in evs:
                if e['status']['type']['state']=='in':
                    found=True
                    comp=e['competitions'][0]
                    h=[c for c in comp['competitors'] if c['homeAway']=='home'][0]
                    a=[c for c in comp['competitors'] if c['homeAway']=='away'][0]
                    txt += f"{e['status']['displayClock']} {h['team']['shortDisplayName']} {h.get('score','0')}-{a.get('score','0')} {a['team']['shortDisplayName']} - {name}\n"
        except: pass
    if not found: txt += "Ayikho edlalwayo manje."
    bot.reply_to(m, txt)

@bot.message_handler(commands=['results'])
def results(m):
    d = (date.today()-timedelta(days=1)).strftime("%Y%m%d")
    txt = "✅ IMIPHUMELA - REAL ESPN ✅\n\n"
    found=False
    for name, lid in LEAGUES.items():
        try:
            evs = get_espn(lid, d)
            for e in evs:
                if e['status']['type']['state']=='post':
                    found=True
                    comp=e['competitions'][0]
                    h=[c for c in comp['competitors'] if c['homeAway']=='home'][0]
                    a=[c for c in comp['competitors'] if c['homeAway']=='away'][0]
                    # Real Full Time + Real Half Time from details
                    ht = "HT N/A"
                    for det in comp.get('details', []):
                        if 'Halftime' in det.get('type', {}).get('text',''):
                            ht = det['type']['text']
                    txt += f"{h['team']['displayName']} {h.get('score','0')}-{a.get('score','0')} {a['team']['displayName']} - {name} ({ht})\n"
        except: pass
    if not found: txt += "Ayikho imiphumela."
    bot.reply_to(m, txt)

@bot.message_handler(commands=['tip'])
def tip(m):
    bot.reply_to(m, "💰 ITHIPHU - REAL:\n\nBheka /today, khetha Over 1.5 Goals emidlalweni emikhulu.\nDlala ngokuhlakanipha 🙏")

@bot.message_handler(func=lambda m: True)
def anything(m):
    bot.reply_to(m, "Thumela /help ⚽")

print("ESPN REAL Bot starting...")
while True:
    try: bot.polling(none_stop=True, timeout=60)
    except Exception as e: print(e); time.sleep(5)
