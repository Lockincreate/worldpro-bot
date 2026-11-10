import requests, time, os
from datetime import date, datetime

TOKEN = os.getenv("TOKEN") 
API_KEY = os.getenv("API_KEY",)
BASE = f"https://api.telegram.org/bot{TOKEN}"
HEADERS = {"x-apisports-key": API_KEY}

# BRAIN: Leagues that score a lot - mystery list, updated
HIGH = ["Eredivisie", "Bundesliga", "Eliteserien", "Allsvenskan", "Veikkausliiga", "Premier League", "Champions League", "Super Lig", "Jupiler Pro League", "Premiership", "La Liga"]
MEDIUM = ["Serie A", "Ligue 1", "Primeira Liga", "Eredivisie", "Championship", "Liga Portugal"]

def get_today():
    # Only 1 request - PARA is date=today, status=NS, no season, no live
    try:
        r = requests.get("https://v3.football.api-sports.io/fixtures", headers=HEADERS, params={"date": str(date.today()), "status": "NS"}, timeout=15)
        return r.json().get("response", [])
    except:
        return []

def get_hockey():
    try:
        r = requests.get("https://v1.hockey.api-sports.io/games", headers=HEADERS, params={"date": str(date.today())}, timeout=10)
        return r.json().get("response", [])[:2]
    except: return []

def get_basket():
    try:
        r = requests.get("https://v1.basketball.api-sports.io/games", headers=HEADERS, params={"date": str(date.today())}, timeout=10)
        return r.json().get("response", [])[:2]
    except: return []

def brain_safe(matches):
    # SAFE: Home team is strong at home + high league = 1X + Over 1.5
    # This is the "don't lose your money" brain
    picks = []
    for m in matches:
        league = m["league"]["name"]
        home = m["teams"]["home"]["name"]; away = m["teams"]["away"]["name"]
        if league in HIGH or league in MEDIUM:
            picks.append(f"⚽ {league}\n{home} vs {away}\n👉 1X + Over 1.5 Goals (Safe)\n")
        if len(picks) >= 2: break
    return picks

def brain_medium(matches):
    # MEDIUM: High scoring league only = Over 2.5 + BTTS
    picks = []
    for m in matches:
        league = m["league"]["name"]
        home = m["teams"]["home"]["name"]; away = m["teams"]["away"]["name"]
        if league in HIGH:
            picks.append(f"⚽ {league}\n{home} vs {away}\n👉 Over 2.5 + BTTS YES\n")
        if len(picks) >= 2: break
    return picks

def brain_jackpot(matches):
    # JACKPOT: Only the craziest scoring leagues, Over 3.5 / Over 4.5
    picks = []
    for m in matches:
        league = m["league"]["name"]
        home = m["teams"]["home"]["name"]; away = m["teams"]["away"]["name"]
        # Only top 4 crazy leagues for jackpot
        if league in ["Eredivisie", "Bundesliga", "Eliteserien", "Super Lig"]:
            picks.append(f"⚽ {league}\n{home} vs {away}\n👉 Over 3.5 Goals (Jackpot)\n")
        if len(picks) >= 2: break
    return picks

def brain_mystery(matches):
    # MYSTERY: Mix sports + LATE games (after 19:00) - teams tired, more goals
    # Plus unknown leagues - bookies don't watch them, we catch value
    picks = []
    for m in matches:
        hour = m["fixture"]["date"][11:13]
        try: h = int(hour)
        except: h = 12
        league = m["league"]["name"]
        home = m["teams"]["home"]["name"]; away = m["teams"]["away"]["name"]
        # Mystery rule: late game OR unknown league (not in top list) = value
        if h >= 19 or league not in HIGH + MEDIUM:
            picks.append(f"🕵️ MYSTERY | {league}\n{home} vs {away}\n👉 Over 2.5 Goals (Late / Unknown)\n")
            if len(picks) >= 1: break
    # Add 1 hockey mystery - hockey always scores late
    for g in get_hockey()[:1]:
        picks.append(f"🏒 MYSTERY | {g['league']['name']}\n{g['teams']['home']['name']} vs {g['teams']['away']['name']}\n👉 Over 5.5 Goals\n")
    # Add 1 basketball mystery
    for g in get_basket()[:1]:
        picks.append(f"🏀 MYSTERY | {g['league']['name']}\n{g['teams']['home']['name']} vs {g['teams']['away']['name']}\n👉 Over 155.5 Points\n")
    return picks[:3]

def make_all():
    m = get_today()
    if not m:
        return "No games today bhuti. Rest."
    s = brain_safe(m)
    med = brain_medium(m)
    j = brain_jackpot(m)
    mys = brain_mystery(m)
    text = "🔥 WORLD PRO - 4 BRAINS, 4 CHANCES 🔥\n\n"
    text += "🛡️ SAFE TICKET (High win %)\n" + ("\n".join(s) if s else "No safe today\n") + "\n"
    text += "⚡ MEDIUM TICKET (Good odds)\n" + ("\n".join(med) if med else "No medium today\n") + "\n"
    text += "💰 JACKPOT TICKET (Big money)\n" + ("\n".join(j) if j else "No jackpot today - skip\n") + "\n"
    text += "🕵️ MYSTERY TICKET (Secret)\n" + ("\n".join(mys) if mys else "No mystery today\n")
    text += "\nPlay SAFE with small stake. Split your money: 50% Safe, 30% Medium, 10% Jackpot, 10% Mystery. 18+"
    return text

def send(chat_id, text):
    requests.post(BASE + "/sendMessage", data={"chat_id": chat_id, "text": text})

offset = 0
print("4-Brain Bot running...")
while True:
    try:
        r = requests.get(BASE + "/getUpdates", params={"offset": offset, "timeout": 10}).json()
        for u in r.get("result", []):
            offset = u["update_id"] + 1
            msg = u.get("message", {}); chat = msg.get("chat", {}).get("id"); text = msg.get("text", "")
            if text == "/start":
                send(chat, "World Pro - 4 Brains 🧠🕵️\n/all = 4 tickets at once\n/safe = Safe only\n/medium = Medium only\n/jackpot = Jackpot only\n/mystery = Mystery only\n/ticket = Same as /all")
            elif text in ["/ticket", "/all"]:
                send(chat, make_all())
            elif text == "/safe":
                m = get_today(); send(chat, "🛡️ SAFE\n\n" + "\n".join(brain_safe(m)) if brain_safe(m) else "No safe today")
            elif text == "/medium":
                m = get_today(); send(chat, "⚡ MEDIUM\n\n" + "\n".join(brain_medium(m)) if brain_medium(m) else "No medium today")
            elif text == "/jackpot":
                m = get_today(); send(chat, "💰 JACKPOT\n\n" + "\n".join(brain_jackpot(m)) if brain_jackpot(m) else "No jackpot today")
            elif text == "/mystery":
                m = get_today(); send(chat, "🕵️ MYSTERY\n\n" + "\n".join(brain_mystery(m)) if brain_mystery(m) else "No mystery today")
        time.sleep(3)
    except Exception as e:
        print("Error:", e); time.sleep(5)
