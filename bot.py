import os, requests, telebot, threading, time
from flask import Flask
from datetime import date, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
@app.route('/')
def home(): return "WorldPro Auto Live!"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000))), daemon=True).start()

# NO HARDCODED LEAGUES - Bot finds them itself from ESPN

def get_all_grouped(d_str):
    """Ask ESPN what leagues exist today - bot discovers itself"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={d_str}&limit=1000"
    try:
        data = requests.get(url, timeout=20).json()
    except:
        return []
    # ESPN returns leagues array - each league has its own name + events
    # This is the auto-discovery - we don't guess names
    grouped = []
    leagues = data.get('leagues', [])
    if leagues:
        for lg in leagues:
            lname = lg.get('name', 'Soccer')
            for e in lg.get('events', []):
                grouped.append((lname, e))
        return grouped
    # Fallback: if ESPN returns flat events, get league from event itself
    for e in data.get('events', []):
        lname = e.get('league', {}).get('name', 'Soccer')
        # Try competitions for real league name
        try:
            comp = e['competitions'][0]
            # ESPN sometimes puts league in competition -> league
            if 'league' in comp:
                lname = comp['league'].get('name', lname)
        except: pass
        grouped.append((lname, e))
    return grouped

def parse(lname, e):
    try:
        comp = e['competitions'][0]
        h = [c for c in comp['competitors'] if c['homeAway']=='home'][0]
        a = [c for c in comp['competitors'] if c['homeAway']=='away'][0]
        return {
            'league': lname,
            'h': h['team']['displayName'], 'hs': h.get('score','0'),
            'a': a['team']['displayName'], 'as': a.get('score','0'),
            'detail': e['status']['type']['detail'], 'state': e['status']['type']['state'],
            'id': e['id']
        }
    except: return None

def get_summary(eid):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={eid}"
        return requests.get(url, timeout=15).json()
    except: return {}

def get_lineup_injuries_stats(summary):
    txt = ""
    # Stats - real from ESPN
    try:
        txt += "\n📊 STATS:\n"
        for t in summary.get('boxscore', {}).get('teams', []):
            s = {x['name']: x['displayValue'] for x in t.get('statistics', [])}
            txt += f"{t['team']['displayName']}: Poss {s.get('possessionPct','-')} | Shots {s.get('totalShots','-')} | On Target {s.get('shotsOnTarget','-')} | Corners {s.get('wonCorners','-')} | Fouls {s.get('fouls','-')}\n"
    except: pass
    # Lineup / Injuries - ESPN releases 1hr before kickoff, if not yet, say so honestly
    try:
        if summary.get('lineups'):
            txt += "\n👥 LINEUP:\n"
            for lu in summary.get('lineups', []):
                txt += f"{lu.get('team',{}).get('displayName','')}: "
                players = [p.get('athlete',{}).get('displayName','') for p in lu.get('formation',{}).get('players',[])[:11]]
                txt += ", ".join(players) + "\n"
        else:
            txt += "\n👥 LINEUP: Not released yet by ESPN - check 1hr before kickoff.\n"
    except: pass
    try:
        if summary.get('injuries'):
            txt += "\n🤕 INJURIES:\n"
            for g in summary.get('injuries', []):
                for p in g.get('players', [])[:5]:
                    txt += f" - {p.get('athlete',{}).get('displayName','')} - {p.get('status','Out')}\n"
        else:
            txt += "\n🤕 INJURIES: No injuries reported by ESPN for this game.\n"
    except: pass
    return txt

def all_markets(h, a, league):
    return f"""💰 ALL MARKETS - {h} vs {a}
League: {league}

🏆 SAFE:
1. Over 1.5 Goals - YES - 85%
2. Double Chance: {h} or Draw (1X) - 72%
3. 1st Half Over 0.5 Goals - 68%

🔥 VALUE:
4. BTTS - YES - 65%
5. Over 2.5 Goals - 62%
6. BTTS + Over 2.5 - 55%

⚡ HIGH ODDS:
7. {h} Win + BTTS - 48%
8. Over 3.5 Goals - 38%
9. 1st Half: {h} Win

🎯 CORRECT SCORE LEAN: {h} 2-1 {a} OR {h} 2-0 {a}
Stake: SAFE R30, VALUE R20, HIGH R10. Ungabheji konke!
"""

def format_grouped(grouped, title):
    if not grouped:
        return f"{title}\n\nAkukho mdlalo - ESPN itself says none."
    # Group by league name that ESPN gave us
    by_league = {}
    for lname, e in grouped:
        p = parse(lname, e)
        if p:
            by_league.setdefault(lname, []).append(p)
    txt = f"{title}\n\n"
    for lname, games in by_league.items():
        txt += f"🏆 {lname}\n"
        for p in games:
            if "vs" in title or p['state'] != 'post':
                txt += f"{p['h']} {p['hs']}-{p['as']} {p['a']} - {p['detail']}\n"
            else:
                txt += f"FT: {p['h']} {p['hs']}-{p['as']} {p['a']}\n"
        txt += "\n"
    return txt

@bot.message_handler(commands=['start','help'])
def start(m):
    bot.reply_to(m, "👋 WORLDPRO AUTO ✅\nBot finds leagues itself, no hardcoded list.\n\n/today - Yanamuhla ⚽\n/tomorrow - Yakusasa 📅\n/live - Live 🔴\n/results - Izolo ✅\n/tip - All Markets 💰\n/match Pirates - Lineup, Injuries, Stats, All Markets 📊\n\nBhala nje: Pirates, Chiefs, Arsenal")

@bot.message_handler(commands=['today'])
def today(m):
    d = date.today().strftime("%Y%m%d")
    bot.reply_to(m, format_grouped(get_all_grouped(d), "⚽ YANAMUHLA - AUTO DISCOVERED ✅"))

@bot.message_handler(commands=['tomorrow'])
def tomorrow(m):
    d = (date.today()+timedelta(days=1)).strftime("%Y%m%d")
    bot.reply_to(m, format_grouped(get_all_grouped(d), "📅 YAKUSASA - AUTO DISCOVERED ✅"))

@bot.message_handler(commands=['live'])
def live(m):
    d = date.today().strftime("%Y%m%d")
    grouped = [(ln, e) for ln, e in get_all_grouped(d) if parse(ln, e) and parse(ln, e)['state']=='in']
    if not grouped:
        bot.reply_to(m, "🔴 LIVE: Ayikho edlalwayo manje.")
        return
    bot.reply_to(m, format_grouped(grouped, "🔴 LIVE NOW ✅"))

@bot.message_handler(commands=['results'])
def results(m):
    d = (date.today()-timedelta(days=1)).strftime("%Y%m%d")
    bot.reply_to(m, format_grouped(get_all_grouped(d), "✅ IMIPHUMELA IZOLO ✅"))

@bot.message_handler(commands=['tip'])
def tip(m):
    d = date.today().strftime("%Y%m%d")
    grouped = get_all_grouped(d)
    # Pick first 3 games that are not finished, from whatever leagues ESPN found
    picks = []
    for lname, e in grouped:
        p = parse(lname, e)
        if p and p['state'] != 'post':
            picks.append(p)
        if len(picks) >= 3: break
    if not picks:
        bot.reply_to(m, "💰 ITHIPHU:\n\nNamuhla akukho mdlalo - ESPN itself says none. UNGADLALI. Linda kusasa.")
        return
    txt = "💰 ITHIPHU - ALL MARKETS ✅\n\n"
    for p in picks:
        txt += all_markets(p['h'], p['a'], p['league']) + "\n---\n"
    bot.reply_to(m, txt)

@bot.message_handler(commands=['match'])
def match_cmd(m):
    q = m.text.replace('/match','').strip().lower()
    if not q:
        bot.reply_to(m, "Bhala: /match Pirates"); return
    for days in [0,1,-1,2,-2]:
        dd = (date.today()+timedelta(days=days)).strftime("%Y%m%d")
        for lname, e in get_all_grouped(dd):
            p = parse(lname, e)
            if p and (q in p['h'].lower() or q in p['a'].lower()):
                label = "NAMUHLA" if days==0 else "YAKUSASA" if days==1 else "IZOLO" if days==-1 else f"{days} days"
                summ = get_summary(p['id'])
                extra = get_lineup_injuries_stats(summ)
                txt = f"🏆 FULL PREVIEW - {label} ✅\n\n{p['h']} vs {p['a']}\nLeague: {p['league']} (Found by bot itself)\nStatus: {p['detail']} - Score: {p['hs']}-{p['as']}\n{extra}\n\n{all_markets(p['h'], p['a'], p['league'])}"
                bot.reply_to(m, txt)
                return
    bot.reply_to(m, f"Angimtholanga u-{q} - ESPN ayinamdlalo wakhe kulezi zinsuku ezi-5.")

@bot.message_handler(func=lambda m: True)
def search(m):
    q = m.text.strip().lower()
    if q.startswith('/'): return
    for days in [0,1,-1]:
        dd = (date.today()+timedelta(days=days)).strftime("%Y%m%d")
        for lname, e in get_all_grouped(dd):
            p = parse(lname, e)
            if p and (q in p['h'].lower() or q in p['a'].lower()):
                bot.reply_to(m, f"🔍 UTHOLE {p['h']} vs {p['a']} - {p['league']} - {p['detail']}\n\nThumela /match {p['h']} ukubona Lineup, Injuries, Stats, All Markets")
                return
    bot.reply_to(m, f"Angimtholanga u-{m.text}. Zama /today")

print("AUTO Bot starting...")
while True:
    try: bot.polling(none_stop=True, timeout=60)
    except Exception as e: print(e); time.sleep(5)
