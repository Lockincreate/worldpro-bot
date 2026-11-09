import os, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
def _keep_alive():
    port = int(os.environ.get("PORT", 10000))
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers(); self.wfile.write(b"Bot is alive")
        def log_message(self, *a): pass
    HTTPServer(("0.0.0.0", port), H).serve_forever()
threading.Thread(target=_keep_alive, daemon=True).start()
import requests, time, threading, os
from datetime import date, datetime

TOKEN = os.environ.get("TOKEN")
API_KEY = os.environ.get("API_KEY")
CHANNEL = "@WorldSoccerFreeTips"

BASE = f"https://api.telegram.org/bot{TOKEN}"
HEADERS = {"x-apisports-key": API_KEY}

def send(chat_id, text):
    try:
        requests.post(BASE + "/sendMessage", data={"chat_id": chat_id, "text": text}, timeout=15)
    except:
        pass

def get_matches():
    try:
        r = requests.get("https://v3.football.api-sports.io/fixtures", headers=HEADERS, params={"date": str(date.today())}, timeout=20)
        all_games = r.json().get("response", [])
        big = [m for m in all_games if m['league']['name'] in ['Premier League','La Liga','Serie A','Bundesliga','Ligue 1','UEFA Champions League','Premier Soccer League','Liga MX','Eredivisie','Primeira Liga']]
        rest = [m for m in all_games if m not in big]
        return (big + rest)[:10]
    except:
        return []

def get_injuries(fid):
    try:
        r = requests.get("https://v3.football.api-sports.io/injuries", headers=HEADERS, params={"fixture": fid}, timeout=10)
        data = r.json().get("response", [])
        if not data:
            return "No major injuries", 0
        names = []
        for inj in data[:4]:
            pl = inj.get("player", {}).get("name", "?")
            typ = inj.get("reason", "")
            names.append(f"{pl} ({typ})")
        return ", ".join(names), len(data)
    except:
        return "Injury data N/A", 0

def get_lineups(fid):
    try:
        r = requests.get("https://v3.football.api-sports.io/fixtures/lineups", headers=HEADERS, params={"fixture": fid}, timeout=10)
        data = r.json().get("response", [])
        if not data:
            return "Lineups: Not released yet"
        if len(data) >= 2:
            return f"Lineups: {data[0].get('formation','?')} vs {data[1].get('formation','?')}"
        return f"Lineups: {data[0].get('formation','?')}"
    except:
        return "Lineups: Not released yet"

def get_h2h(home_id, away_id):
    try:
        r = requests.get("https://v3.football.api-sports.io/fixtures/headtohead", headers=HEADERS, params={"h2h": f"{home_id}-{away_id}", "last": 3}, timeout=10)
        data = r.json().get("response", [])
        if not data:
            return "H2H: No recent meetings"
        results = []
        for m in data[:3]:
            h = m['teams']['home']['name']
            a = m['teams']['away']['name']
            results.append(f"{h} {m['goals']['home']}-{m['goals']['away']} {a}")
        return "H2H Last 3: " + " | ".join(results)
    except:
        return "H2H: N/A"

def get_real_tip(m):
    fid = m['fixture']['id']
    home_id = m['teams']['home']['id']
    away_id = m['teams']['away']['id']
    try:
        r = requests.get("https://v3.football.api-sports.io/predictions", headers=HEADERS, params={"fixture": fid}, timeout=15)
        data = r.json().get("response", [])
        if not data:
            return "Over 1.5 Goals / BTTS: YES / 1st Half: Over 0.5"
        pred = data[0]["predictions"]
        teams = data[0]["teams"]
        advice = pred.get("advice", "No advice")
        percent = pred.get("percent", {})
        under_over = pred.get("under_over", "Over 1.5")
        goals = pred.get("goals", {})
        form_h = teams.get("home", {}).get("league", {}).get("form", "N/A")
        form_a = teams.get("away", {}).get("league", {}).get("form", "N/A")
        inj_text, inj_count = get_injuries(fid)
        lineup_text = get_lineups(fid)
        h2h_text = get_h2h(home_id, away_id)
        try:
            hg = float(str(goals.get("home", "0")).replace("+","").replace("-","0") or 0)
            ag = float(str(goals.get("away", "0")).replace("+","").replace("-","0") or 0)
            total_exp = hg + ag
        except:
            total_exp = 2.5
        over15 = "YES" if total_exp > 1.5 else "NO"
        btts = "YES - Both scoring" if hg > 0.8 and ag > 0.8 else "NO"
        if total_exp >= 2.8 or inj_count >= 3:
            first_half = "Over 0.5 - Early goals expected"
            first_btts = "YES"
        elif total_exp >= 2.0:
            first_half = "Over 0.5"
            first_btts = "NO"
        else:
            first_half = "Under 1.5 - Slow start"
            first_btts = "NO"
        tip = f"Advice: {advice}\nWin %: Home {percent.get('home','?')} | Draw {percent.get('draw','?')} | Away {percent.get('away','?')}\nFORM: Home {form_h} | Away {form_a}\nINJURIES ({inj_count}): {inj_text}\n{lineup_text}\n{h2h_text}\nExpected Goals: {hg} - {ag} (Total {round(total_exp,1)})\n--- TIPS ---\nOver 1.5: {over15}\nOver/Under: {under_over}\nBTTS: {btts}\n1st Half Totals: {first_half}\n1st Half BTTS: {first_btts}"
        return tip
    except:
        return "Over 1.5 Goals / BTTS: YES / 1st Half: Over 0.5"

def make_tips():
    matches = get_matches()
    if not matches:
        return "No big matches today bhuti. Check tomorrow."
    text = "WORLD PRO - FULL BRAIN ANALYSIS\nPlayers + Injuries + Form + H2H + Live API\n\n"
    for m in matches:
        league = m['league']['name']
        home = m['teams']['home']['name']
        away = m['teams']['away']['name']
        real = get_real_tip(m)
        text += f"{league}\n{home} vs {away}\n{real}\n\n"
    text += "Play safe. 18+"
    return text

def auto_post_loop():
    posted = ""
    while True:
        now = datetime.now()
        today = str(date.today())
        if now.hour == 9 and now.minute == 0 and posted != today:
            send(CHANNEL, make_tips())
            posted = today
        time.sleep(30)

threading.Thread(target=auto_post_loop, daemon=True).start()
offset = 0
print("Bot is running - FULL BRAIN VERSION")
while True:
    try:
        r = requests.get(BASE + "/getUpdates", params={"offset": offset, "timeout": 10}).json()
        for u in r.get("result", []):
            offset = u["update_id"] + 1
            msg = u.get("message", {})
            chat = msg.get("chat", {}).get("id")
            text = msg.get("text", "")
            if text == "/start":
                send(chat, "Welcome to World Pro! Type /today or /tip for FULL analysis")
            elif text in ["/today", "/tip"]:
                send(chat, "Analyzing players, injuries, form, H2H... wait 10 sec")
                send(chat, make_tips())
        time.sleep(3)
    except Exception as e:
        print("Bot error:", e)
        time.sleep(5)
