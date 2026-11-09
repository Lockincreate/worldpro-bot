import os, requests, telebot, threading, time
from flask import Flask
from datetime import date, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
@app.route('/')
def home(): return "WorldPro Smart Bot Live!"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000))), daemon=True).start()

def get_all_games(d_str):
    # ALL leagues - no filter
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard?dates={d_str}"
    try:
        r = requests.get(url, timeout=20).json()
        return r.get('events', [])
    except:
        return []

def format_game(e):
    try:
        comp = e['competitions'][0]
        league = e.get('league', {}).get('name', 'Soccer')
        h = [c for c in comp['competitors'] if c['homeAway']=='home'][0]
        a = [c for c in comp['competitors'] if c['homeAway']=='away'][0]
        hs = h.get('score', '0'); as_ = a.get('score', '0')
        status = e['status']['type']['detail']
        state = e['status']['type']['state']
        return f"{h['team']['displayName']} {hs}-{as_} {a['team']['displayName']} - {league} - {status}", state, h['team']['displayName'], a['team']['displayName']
    except:
        return None, None, None, None

@bot.message_handler(commands=['start','help'])
def start(m):
    bot.reply_to(m, "👋 WORLDPRO SMART ✅\n\n/today - Yanamuhla - ALL leagues ⚽\n/tomorrow - Yakusasa 📅\n/live - Live 🔴\n/results - Izolo ✅\n/tip - Ithiphu REAL 💰\n\nUngabhala nje igama: Pirates, Chiefs, Arsenal, Sundowns...")

@bot.message_handler(commands=['today'])
def today(m):
    d = date.today().strftime("%Y%m%d")
    evs = get_all_games(d)
    if not evs:
        bot.reply_to(m, "⚽ YANAMUHLA:\n\nAkukho mdlalo nhlobo namuhla - ngempela, Monday kuyathula.")
        return
    txt = "⚽ IMIDLALO YANAMUHLA - REAL ESPN ✅\n\n"
    for e in evs[:30]:
        line, _, _, _ = format_game(e)
        if line: txt += line + "\n"
    bot.reply_to(m, txt)

@bot.message_handler(commands=['tomorrow'])
def tomorrow(m):
    d = (date.today()+timedelta(days=1)).strftime("%Y%m%d")
    evs = get_all_games(d)
    if not evs:
        bot.reply_to(m, "📅 YAKUSASA: Akukho mdlalo.")
        return
    txt = "📅 YAKUSASA - REAL ✅\n\n"
    for e in evs[:30]:
        line, _, _, _ = format_game(e)
        if line: txt += line + "\n"
    bot.reply_to(m, txt)

@bot.message_handler(commands=['live'])
def live(m):
    d = date.today().strftime("%Y%m%d")
    evs = get_all_games(d)
    txt = "🔴 LIVE MANJE ✅\n\n"
    found=False
    for e in evs:
        line, state, _, _ = format_game(e)
        if state=='in':
            found=True; txt+=line+"\n"
    if not found: txt+="Ayikho edlalwayo manje."
    bot.reply_to(m, txt)

@bot.message_handler(commands=['results'])
def results(m):
    d = (date.today()-timedelta(days=1)).strftime("%Y%m%d")
    evs = get_all_games(d)
    if not evs:
        bot.reply_to(m, "Ayikho imiphumela.")
        return
    txt = "✅ IMIPHUMELA IZOLO ✅\n\n"
    for e in evs[:30]:
        line, _, _, _ = format_game(e)
        if line: txt+=line+"\n"
    bot.reply_to(m, txt)

@bot.message_handler(commands=['tip'])
def tip(m):
    d = date.today().strftime("%Y%m%d")
    evs = get_all_games(d)
    if not evs:
        bot.reply_to(m, "💰 ITHIPHU:\n\nNamuhla akukho mdlalo omkhulu, ungadlali. Linda kusasa - kuzoba ne Champions League. Dlala ngokuhlakanipha 🙏")
        return
    # Pick first 3 games as real tip
    txt = "💰 ITHIPHU YANAMUHLA - REAL GAMES ✅\n\n"
    for e in evs[:3]:
        line, _, h, a = format_game(e)
        txt += f"{h} vs {a}\n👉 Over 1.5 Goals - Iqhaza eliphephile\n\n"
    txt += "Dlala kancane, ungabheji konke! 🙏"
    bot.reply_to(m, txt)

@bot.message_handler(func=lambda m: True)
def search_team(m):
    q = m.text.strip().lower()
    if q.startswith('/'): return
    # Search today + tomorrow + yesterday
    found_txt = ""
    for days in [0,1,-1]:
        d = (date.today()+timedelta(days=days)).strftime("%Y%m%d")
        evs = get_all_games(d)
        for e in evs:
            line, _, h, a = format_game(e)
            if h and (q in h.lower() or q in a.lower()):
                label = "NAMUHLA" if days==0 else "YAKUSASA" if days==1 else "IZOLO"
                found_txt += f"{label}: {line}\n"
    if found_txt:
        bot.reply_to(m, f"🔍 UTHOLE {m.text.upper()} ✅\n\n{found_txt}")
    else:
        bot.reply_to(m, f"Angimtholanga u-{m.text} emidlalweni yalezi zinsuku ezi-3. Zama /today ukubona yonke imidlalo ⚽")

print("Smart Bot starting...")
while True:
    try: bot.polling(none_stop=True, timeout=60)
    except Exception as e: print(e); time.sleep(5)
