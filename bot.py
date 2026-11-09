import os, threading, re
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
from datetime import date, datetime, timedelta
TOKEN = os.environ.get("TOKEN")
API_KEY = os.environ.get("API_KEY")
CHANNEL = "@WorldSoccerFreeTips"
BASE = f"https://api.telegram.org/bot{TOKEN}"
HEADERS = {"x-apisports-key": API_KEY}
def send(chat_id, text):
    try:
        for i in range(0, len(text), 4000):
            requests.post(BASE + "/sendMessage", data={"chat_id": chat_id, "text": text[i:i+4000]}, timeout=15)
    except: pass
def get_matches():
    try:
        r = requests.get("https://v3.football.api-sports.io/fixtures", headers=HEADERS, params={"date": str(date.today())}, timeout=20)
        all_games = r.json().get("response", [])
        big = [m for m in all_games if m['league']['name'] in ['Premier League','La Liga','Serie A','Bundesliga','Ligue 1','UEFA Champions League','Premier Soccer League','Liga MX','Eredivisie','Primeira Liga']]
        rest = [m for m in all_games if m not in big]
        return (big + rest)[:10]
    except: return []
def get_injuries(fid):
    try:
        r = requests.get("https://v3.football.api-sports.io/injuries", headers=HEADERS, params={"fixture": fid}, timeout=10)
        data = r.json().get("response", [])
        if not data: return "No major injuries - Full squad available", 0
        names = []
        for inj in data[:5]:
            pl = inj.get("player", {}).get("name", "?")
            typ = inj.get("reason", "")
            names.append(f"{pl} ({typ})")
        return ", ".join(names), len(data)
    except: return "Injury data N/A", 0
def get_lineups(fid):
    try:
        r = requests.get("https://v3.football.api-sports.io/fixtures/lineups", headers=HEADERS, params={"fixture": fid}, timeout=10)
        data = r.json().get("response", [])
        if not data: return "Lineups: Not released yet - Check 1hr before kickoff"
        if len(data) >= 2:
            return f"Lineups: {data[0].get('formation','?')} vs {data[1].get('formation','?')} | Coach: {data[0].get('coach',{}).get('name','?')} vs {data[1].get('coach',{}).get('name','?')}"
        return f"Lineups: {data[0].get('formation','?')}"
    except: return "Lineups: Not released yet"
def get_h2h(home_id, away_id):
    try:
        r = requests.get("https://v3.football.api-sports.io/fixtures/headtohead", headers=HEADERS, params={"h2h": f"{home_id}-{away_id}", "last": 5}, timeout=10)
        data = r.json().get("response", [])
        if not data: return "H2H: No recent meetings - First time / Long time"
        results = []
        wins_h = wins_a = draws = 0
        for m in data[:5]:
            h = m['teams']['home']['name']; a = m['teams']['away']['name']; gh = m['goals']['home']; ga = m['goals']['away']
            results.append(f"{h} {gh}-{ga} {a}")
            if gh > ga: wins_h += 1
            elif ga > gh: wins_a += 1
            else: draws += 1
        return f"H2H Last 5: Home Wins {wins_h} | Draws {draws} | Away Wins {wins_a}\n" + " | ".join(results)
    except: return "H2H: N/A"
def get_real_tip(m):
    fid = m['fixture']['id']; home_id = m['teams']['home']['id']; away_id = m['teams']['away']['id']
    home_name = m['teams']['home']['name']; away_name = m['teams']['away']['name']
    try:
        r = requests.get("https://v3.football.api-sports.io/predictions", headers=HEADERS, params={"fixture": fid}, timeout=15)
        data = r.json().get("response", [])
        if not data: return "No prediction data yet from API. Try again 1hr before kickoff.\nOver 1.5: YES (Safe)\nStraight Win: Home"
        pred = data[0]["predictions"]; teams = data[0]["teams"]; comparison = data[0].get("comparison", {})
        advice = pred.get("advice", "No advice"); percent = pred.get("percent", {}); under_over = pred.get("under_over", "Over 1.5"); goals = pred.get("goals", {})
        form_h = teams.get("home", {}).get("league", {}).get("form", "N/A"); form_a = teams.get("away", {}).get("league", {}).get("form", "N/A")
        inj_text, inj_count = get_injuries(fid); lineup_text = get_lineups(fid); h2h_text = get_h2h(home_id, away_id)
        try:
            hg = float(str(goals.get("home", "0")).replace("+","").replace("-","0") or 0); ag = float(str(goals.get("away", "0")).replace("+","").replace("-","0") or 0); total_exp = hg + ag
        except: hg, ag, total_exp = 1.4, 1.0, 2.4
        def to_int(v):
            try: return int(str(v).replace("%",""))
            except: return 0
        ph = to_int(percent.get('home', 0)); pd = to_int(percent.get('draw', 0)); pa = to_int(percent.get('away', 0))
        if ph >= pa and ph >= pd: winner = home_name; winner_code = f"1 - {home_name} WINS"; winner_pct = ph
        elif pa > ph and pa >= pd: winner = away_name; winner_code = f"2 - {away_name} WINS"; winner_pct = pa
        else: winner = "DRAW"; winner_code = "X - DRAW"; winner_pct = pd
        cs_h = round(hg); cs_a = round(ag)
        if cs_h == 0 and cs_a == 0: cs_h, cs_a = 1, 0
        over15 = "YES ✅" if total_exp > 1.5 else "NO ❌"; over25 = "YES ✅" if total_exp > 2.5 else "NO ❌"
        btts = "YES ✅" if hg > 0.8 and ag > 0.8 else "NO ❌"
        double_chance = f"1X - {home_name} or Draw" if ph >= pa else f"X2 - Draw or {away_name}"
        if total_exp >= 2.8: first_half = "Over 0.5 ✅ - Early goals expected"; first_btts = "YES"; second_half = "Over 1.5 ✅ - More goals 2nd half"
        elif total_exp >= 2.0: first_half = "Over 0.5 ✅"; first_btts = "NO"; second_half = "Over 0.5 ✅"
        else: first_half = "Under 1.5 - Slow start, be careful"; first_btts = "NO"; second_half = "Over 0.5 - Goals late"
        if winner_pct >= 60: best_bet = f"STRAIGHT WIN: {winner_code} - STRONG 💪"; safe_bet = f"DOUBLE CHANCE: {double_chance} - VERY SAFE 🛡️"
        elif winner_pct >= 45: best_bet = f"STRAIGHT WIN: {winner_code} - MEDIUM"; safe_bet = f"OVER 1.5 GOALS: {over15} - SAFER 🛡️"
        else: best_bet = f"AVOID Straight Win - Too Close! Bet OVER 1.5 Instead"; safe_bet = f"OVER 1.5 GOALS: {over15} + DOUBLE CHANCE: {double_chance}"
        corners_est = "Over 8.5 Corners" if total_exp >= 2.5 else "Under 10.5 Corners"
        cards_est = "Over 3.5 Cards - Derby / Tight game" if abs(ph-pa) < 15 else "Under 4.5 Cards"
        tip = f"""🏆 WHO WILL WIN: {winner} ({winner_pct}%)
Advice: {advice}
Win %: Home {ph}% | Draw {pd}% | Away {pa}%

💰 HOW TO BET:
✅ BEST BET: {best_bet}
🛡️ SAFE BET: {safe_bet}
🔥 HIGH ODDS BET: Correct Score {cs_h}-{cs_a} + BTTS {btts}
🎯 DOUBLE CHANCE: {double_chance}

📊 FULL STATISTICS:
FORM: Home {form_h} | Away {form_a}
INJURIES ({inj_count}): {inj_text}
{lineup_text}
{h2h_text}
Expected Goals: {hg} - {ag} (Total {round(total_exp,1)})
Attack vs Defence: {comparison}

--- ALL TIPS ---
Straight Win (1X2): {winner_code}
Over 1.5: {over15}
Over 2.5: {over25}
Over/Under API: {under_over}
BTTS (Both To Score): {btts}
Correct Score Prediction: {cs_h}-{cs_a}
1st Half Totals: {first_half}
1st Half BTTS: {first_btts}
2nd Half Totals: {second_half}
Corners: {corners_est}
Cards: {cards_est}

⚠️ Play safe. 18+ Gamble Responsibly."""
        return tip
    except Exception as e: return f"Over 1.5 Goals / BTTS: YES / 1st Half: Over 0.5\nError: {e}"
def make_tips():
    matches = get_matches()
    if not matches: return "No big matches today bhuti. Check tomorrow."
    text = "🌍 WORLD PRO - FULL BRAIN ANALYSIS\nAll Stats + Injuries + Form + H2H + Best Bets\n\n"
    for m in matches:
        league = m['league']['name']; home = m['teams']['home']['name']; away = m['teams']['away']['name']
        real = get_real_tip(m); text += f"{league}\n{home} vs {away}\n{real}\n\n---\n\n"
    return text
def search_team(name):
    try:
        r = requests.get("https://v3.football.api-sports.io/teams", headers=HEADERS, params={"search": name.strip()}, timeout=15)
        data = r.json().get("response", [])
        if not data: return None
        return data[0]["team"]
    except: return None
def search_league(name):
    try:
        r = requests.get("https://v3.football.api-sports.io/leagues", headers=HEADERS, params={"search": name.strip()}, timeout=15)
        data = r.json().get("response", [])
        if not data: return None
        # Prefer leagues with standings - pick first with current season
        for item in data:
            lg = item.get("league", {})
            # Skip cups if possible when name is generic
            if "cup" not in lg.get("name","").lower() or "premier" in name.lower():
                return lg
        return data[0].get("league")
    except: return None
def get_team_next_fixture(team_id):
    try:
        today = str(date.today()); future = str(date.today() + timedelta(days=60))
        r = requests.get("https://v3.football.api-sports.io/fixtures", headers=HEADERS, params={"team": team_id, "from": today, "to": future, "season": 2026}, timeout=15)
        data = r.json().get("response", [])
        if data: return data
        r2 = requests.get("https://v3.football.api-sports.io/fixtures", headers=HEADERS, params={"team": team_id, "from": today, "to": future}, timeout=15)
        return r2.json().get("response", [])
    except: return []
def get_standings_for_team(team_id):
    try:
        r = requests.get("https://v3.football.api-sports.io/fixtures", headers=HEADERS, params={"team": team_id, "last": 1}, timeout=15)
        data = r.json().get("response", [])
        if not data: return None
        league_id = data[0]['league']['id']; season = data[0]['league']['season']
        r2 = requests.get("https://v3.football.api-sports.io/standings", headers=HEADERS, params={"league": league_id, "season": season}, timeout=15)
        st = r2.json().get("response", [])
        if not st: return None
        return st[0]['league']
    except: return None
def get_standings_by_league(league_id, season=None):
    try:
        if not season: season = 2026
        r = requests.get("https://v3.football.api-sports.io/standings", headers=HEADERS, params={"league": league_id, "season": season}, timeout=15)
        st = r.json().get("response", [])
        if st: return st[0]['league']
        # Try 2025 if 2026 empty
        r2 = requests.get("https://v3.football.api-sports.io/standings", headers=HEADERS, params={"league": league_id, "season": 2025}, timeout=15)
        st2 = r2.json().get("response", [])
        if st2: return st2[0]['league']
        return None
    except: return None
def send_full_standings(chat, league):
    # Shows ALL teams, not just top 16 - split into 2 messages
    all_rows = league['standings'][0]
    header = f"🏆 {league['name']} - FULL LOG STANDINGS - ALL {len(all_rows)} TEAMS\n\n"
    txt1 = header
    txt2 = ""
    for idx, s in enumerate(all_rows):
        line = f"{s['rank']}. {s['team']['name']} - P{s['all']['played']} W{s['all']['win']} D{s['all']['draw']} L{s['all']['lose']} GF{s['all']['goals']['for']} GA{s['all']['goals']['against']} Pts {s['points']}\n"
        if idx < 12:
            txt1 += line
        else:
            txt2 += line
    send(chat, txt1)
    if txt2:
        send(chat, f"🏆 {league['name']} - CONTINUED\n\n" + txt2)
def analyse_one_match(m):
    league = m['league']['name']; home = m['teams']['home']['name']; away = m['teams']['away']['name']
    date_str = m['fixture']['date'][:10]; time_str = m['fixture']['date'][11:16]; venue = m['fixture'].get('venue', {}).get('name','')
    real = get_real_tip(m)
    return f"🌍 WORLD PRO - {league}\n{home} vs {away}\nDate: {date_str} {time_str} | {venue}\n\n{real}"
def handle_smart_text(chat, text):
    low = text.lower().strip()
    if low.startswith("/") and low not in ["/start","/today","/tip","/help"]:
        low = low[1:]; text = text[1:]
    if low in ["hi","hello","hey","hola","sawubona","dumela","yebo","yo","morning","good morning","heita"]:
        send(chat, "Hey bhuti! 👋 I'm World Pro - Full Brain.\n\nType any match:\nReal Madrid vs Barcelona\nKaizer Chiefs vs Amazulu\n\nOr one team:\nMan City\n\nOr standings for ANY team / ANY league:\nKaizer Chiefs log standings\nPremier League standings\nPSL standings\n\nOr /today for today's tips")
        return
    if low in ["help","/help","menu","commands"]:
        send(chat, "WORLD PRO - ALL BRAIN:\n\n/today - Today's top tips\n\nOr type:\nTeam vs Team - e.g. Arsenal vs Chelsea\nOne team - e.g. Sundowns\nANY standings - e.g. Man City log standings / Premier League standings / PSL table\n\nI show: Who Will Win, Best Bet, Safe Bet, Correct Score, Form, Injuries, Lineups, H2H, Corners, Cards 🌍")
        return
    if low in ["tip","tips","give me tip","give me tips","today's games","todays games","who will win","who wins","prediction","predictions","today","who will win today"]:
        send(chat, "Analyzing FULL BRAIN... Players, injuries, form, H2H, corners, cards... wait 15 sec"); send(chat, make_tips()); return
    if "log" in low or "standing" in low or "table" in low or "position" in low:
        team_name = low.replace("log","").replace("standings","").replace("standing","").replace("table","").replace("position","").replace("standings","").strip()
        if not team_name: team_name = "Kaizer Chiefs"
        send(chat, f"Getting FULL standings for {team_name}... wait 10 sec - ALL teams")
        # 1. Try as LEAGUE first - e.g. Premier League, PSL, La Liga
        lg = search_league(team_name)
        # Check if user actually typed a league name
        league_keywords = ["premier", "psl", "la liga", "serie", "bundesliga", "ligue", "eredivisie", "primeira", "championship", "league", "soccer league", "division"]
        is_league_query = any(k in team_name.lower() for k in league_keywords)
        if is_league_query and lg:
            league = get_standings_by_league(lg["id"])
            if league:
                send_full_standings(chat, league); return
        # 2. Try as TEAM - e.g. Kaizer Chiefs, Man City, Sundowns -> show its league FULL table
        t = search_team(team_name)
        if not t:
            # If league search found something but not league keyword, try it anyway
            if lg:
                league = get_standings_by_league(lg["id"])
                if league:
                    send_full_standings(chat, league); return
            send(chat, f"Couldn't find team or league '{team_name}'.\nTry: Man City log standings\nOr: Premier League standings"); return
        league = get_standings_for_team(t["id"])
        if not league: send(chat, "No standings found yet"); return
        send_full_standings(chat, league); return
    if " vs " in low or " v " in low:
        parts = re.split(r'\s+vs\s+|\s+v\s+', text, flags=re.IGNORECASE)
        if len(parts) >= 2:
            team1_name = parts[0].strip(); team2_name = parts[1].strip()
            send(chat, f"Searching {team1_name} vs {team2_name} worldwide... 🌍 FULL BRAIN loading... wait 15 sec")
            t1 = search_team(team1_name)
            if not t1: send(chat, f"Couldn't find team '{team1_name}'. Try full name e.g. Real Madrid, Kaizer Chiefs"); return
            fixtures = get_team_next_fixture(t1["id"])
            if not fixtures: send(chat, f"No upcoming match found for {t1['name']}"); return
            found = None
            for f in fixtures:
                h = f['teams']['home']['name'].lower(); a = f['teams']['away']['name'].lower()
                if team2_name.lower() in h or team2_name.lower() in a: found = f; break
            if not found: found = fixtures[0]
            send(chat, analyse_one_match(found)); return
    if len(text) >= 3 and len(text) <= 40:
        send(chat, f"Searching {text} worldwide... 🌍 wait 15 sec")
        t = search_team(text)
        if not t: send(chat, f"Couldn't find '{text}'.\nTry full name e.g. Manchester City\nOr Team vs Team e.g. Arsenal vs Chelsea\nOr /today"); return
        fixtures = get_team_next_fixture(t["id"])
        if not fixtures: send(chat, f"Found {t['name']} but no upcoming match found."); return
        send(chat, analyse_one_match(fixtures[0])); return
    send(chat, "I didn't understand bhuti 😅\nTry:\nReal Madrid vs Barcelona\nOr: Man City\nOr: Premier League standings\nOr: /today")
def auto_post_loop():
    posted = ""
    while True:
        now = datetime.now(); today = str(date.today())
        if now.hour == 9 and now.minute == 0 and posted != today:
            send(CHANNEL, make_tips()); posted = today
        time.sleep(30)
threading.Thread(target=auto_post_loop, daemon=True).start()
offset = 0
print("Bot is running - ALL BRAIN ALL STANDINGS VERSION")
while True:
    try:
        r = requests.get(BASE + "/getUpdates", params={"offset": offset, "timeout": 10}).json()
        for u in r.get("result", []):
            offset = u["update_id"] + 1
            msg = u.get("message", {}); chat = msg.get("chat", {}).get("id"); text = msg.get("text", "")
            if not text: continue
            if text == "/start":
                send(chat, "Welcome to World Pro! 🌍 ALL BRAIN\n\nType any match:\nReal Madrid vs Barcelona\n\nOr one team:\nKaizer Chiefs\n\nOr ANY standings:\nKaizer Chiefs log standings\nPremier League standings\nPSL standings\n\nOr /today")
            elif text in ["/today", "/tip"]:
                send(chat, "Analyzing FULL BRAIN... wait 15 sec"); send(chat, make_tips())
            else: handle_smart_text(chat, text)
        time.sleep(3)
    except Exception as e:
        print("Bot error:", e); time.sleep(5)
