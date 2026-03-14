"""
StockVerse Web Server
실행: python server.py
브라우저: http://localhost:5000
"""
import json, os, math, random, threading, time
from datetime import datetime
from collections import Counter
from flask import Flask, jsonify, request, render_template, Response

app = Flask(__name__)

# ══════════════════════════════════════════════
# 상수
# ══════════════════════════════════════════════
SAVE_FILE      = "save.json"
INITIAL_MONEY  = 10_000_000
TAX_RATE       = 0.22
SLIPPAGE       = 0.002
TICK_SEC       = 3          # 3초마다 틱
CANDLE_TICKS   = 20
DIVIDEND_TICKS = 200
MACRO_TICKS    = 80

# ══════════════════════════════════════════════
# 종목 데이터
# ══════════════════════════════════════════════
STOCK_NAMES = [
    "솔라릭스","유글","페이원","리프트업","GY","유스퀘어",
    "FluxMall","VisioPlay","HyperVerse",
    "한텍","메타블럭스","RG","Riva","Takora","JoyJoy"
]

PROFILES = {
    "솔라릭스":  {"base":350000,"mu":.06,"sigma":.55,"beta":1.8,"div":.000,
                  "desc":"🚗 전기차·에너지 혁신 기업",
                  "events":[("신형 전기차 출시",.08),("자율주행 공개",.06),("배터리 특허 획득",.04),
                             ("리콜 이슈",-.07),("생산 차질",-.06),("CEO 논란",-.05)]},
    "유글":      {"base":180000,"mu":.09,"sigma":.28,"beta":1.1,"div":.000,
                  "desc":"🔍 검색·AI·클라우드 빅테크",
                  "events":[("AI 모델 공개",.07),("클라우드 신기록",.05),("광고 수익 급증",.04),
                             ("반독점 소송",-.06),("과징금 부과",-.05),("정보유출 소송",-.06)]},
    "페이원":    {"base":80000, "mu":.05,"sigma":.35,"beta":1.2,"div":.015,
                  "desc":"💳 글로벌 간편결제 플랫폼",
                  "events":[("신흥국 진출",.06),("암호화폐 지원",.07),("대형 제휴 체결",.04),
                             ("해킹 사고",-.09),("경쟁사 무료화",-.05),("실적 하회",-.04)]},
    "리프트업":  {"base":25000, "mu":.04,"sigma":.70,"beta":.6, "div":.010,
                  "desc":"🎤 한국 소형 엔터테인먼트",
                  "events":[("신인 그룹 대흥행",.12),("투어 전석 매진",.08),("스트리밍 1위",.09),
                             ("아티스트 탈퇴",-.13),("사생활 스캔들",-.12),("계약 분쟁",-.10)]},
    "GY":        {"base":120000,"mu":.07,"sigma":.38,"beta":.7, "div":.020,
                  "desc":"🏢 한국 대형 엔터테인먼트 그룹",
                  "events":[("빌보드 1위",.09),("월드투어 매진",.07),("OTT 독점 계약",.06),
                             ("군입대 공지",-.08),("표절 의혹",-.07),("갑질 폭로",-.09)]},
    "유스퀘어":  {"base":15000, "mu":.12,"sigma":.85,"beta":1.5,"div":.000,
                  "desc":"🚀 AI 기반 B2B SaaS 스타트업",
                  "events":[("나스닥 상장 추진",.18),("시리즈B 유치",.14),("대기업 파트너십",.10),
                             ("창업자 사임",-.16),("런웨이 소진 경고",-.14),("회계 부정 의혹",-.18)]},
    "FluxMall":  {"base":220000,"mu":.08,"sigma":.30,"beta":1.0,"div":.000,
                  "desc":"📦 이커머스·물류·클라우드 공룡",
                  "events":[("클라우드 신기록",.07),("프라임 신기록",.05),("물류 자동화 발표",.06),
                             ("물류 파업",-.07),("독과점 분할 명령",-.10),("클라우드 장애",-.08)]},
    "VisioPlay": {"base":95000, "mu":.05,"sigma":.42,"beta":1.1,"div":.000,
                  "desc":"🎬 글로벌 스트리밍·오리지널 콘텐츠",
                  "events":[("오리지널 대흥행",.09),("구독자 폭증",.08),("게임 사업 진출",.06),
                             ("구독자 대이탈",-.11),("어닝 쇼크",-.09),("제작비 적자",-.08)]},
    "HyperVerse":{"base":140000,"mu":.03,"sigma":.52,"beta":1.4,"div":.005,
                  "desc":"🥽 소셜·메타버스·AR/VR 플랫폼",
                  "events":[("VR 헤드셋 공개",.10),("DAU 1억 돌파",.08),("AI칩 자체개발",.07),
                             ("투자손실 폭증",-.12),("청문회 소환",-.08),("SNS 이용자 이탈",-.09)]},
    "한텍":      {"base":78000, "mu":.06,"sigma":.32,"beta":1.2,"div":.025,
                  "desc":"📱 글로벌 전자·반도체·가전 대기업",
                  "events":[("차세대 반도체 공개",.07),("신작 흥행",.06),("파운드리 수주 신기록",.08),
                             ("반도체 재고 급증",-.07),("미국 수출 규제 타격",-.09),("노조 전면 파업",-.06)]},
    "메타블럭스":{"base":42000, "mu":.10,"sigma":.65,"beta":1.3,"div":.000,
                  "desc":"🎮 UGC 메타버스 게임 플랫폼",
                  "events":[("신규 DAU 5000만",.11),("대형 IP 콜라보",.09),("크리에이터 수익 확대",.07),
                             ("아동 착취 의혹",-.14),("이용자 이탈 가속",-.10),("경쟁 플랫폼 급부상",-.08)]},
    "RG":        {"base":95000, "mu":.06,"sigma":.30,"beta":1.1,"div":.022,
                  "desc":"🏠 가전·B2B 솔루션·에너지 복합 기업",
                  "events":[("AI 가전 라인업 공개",.06),("B2B 클라우드 수주",.07),("에너지 수출",.06),
                             ("주력 사업 적자",-.07),("경쟁사 신제품",-.05),("대규모 구조조정",-.08)]},
    "Riva":      {"base":98000, "mu":.07,"sigma":.36,"beta":1.0,"div":.018,
                  "desc":"🚙 한국 미래형 모빌리티 자동차",
                  "events":[("전기 SUV 대흥행",.08),("자율주행 레벨4",.07),("디자인 어워드 수상",.05),
                             ("엔진 결함 리콜",-.09),("노사 협상 결렬",-.06),("환율 급등",-.05)]},
    "Takora":    {"base":330000,"mu":.06,"sigma":.22,"beta":.8, "div":.028,
                  "desc":"🏭 글로벌 완성차·하이브리드 강자",
                  "events":[("하이브리드 신기록",.06),("수소차 기술 공개",.07),("신공장 가동",.05),
                             ("대규모 리콜",-.08),("전기차 전환 지연",-.06),("엔화 급등",-.05)]},
    "JoyJoy":    {"base":680000,"mu":.07,"sigma":.28,"beta":.6, "div":.012,
                  "desc":"🕹 콘솔·IP·게임 소프트웨어 왕국",
                  "events":[("차세대 콘솔 출시",.10),("신작 흥행",.08),("IP 모바일 출시",.07),
                             ("콘솔 판매 부진",-.09),("개발자 대거 퇴사",-.07),("경쟁 독점 타이틀",-.08)]},
}

MACRO_EVENTS = [
    ("🏦 중앙은행 금리 동결 — 시장 안도",+.015),("📉 금리 0.5%p 인상 — 긴축 우려",-.025),
    ("📈 고용 지표 예상 상회",+.018),("💥 CPI 인플레 급등 — 스태그플레이션",-.030),
    ("🌏 지정학적 리스크 고조",-.022),("💊 경기침체 공식 진입 선언",-.040),
    ("🚀 GDP 성장률 서프라이즈",+.022),("🏛 대규모 재정 부양책 발표",+.028),
    ("🔥 원자재 가격 폭등",-.020),("🤝 미중 무역 협상 타결",+.025),
]

LEVELS = [
    (0,"📊 주린이","#888888"),(12_000_000,"📈 개미투자자","#66bb66"),
    (20_000_000,"💼 중급 투자자","#5588ff"),(50_000_000,"🏦 큰손","#ffcc33"),
    (150_000_000,"💎 슈퍼개미","#dd88ff"),(500_000_000,"🚀 워렌버핏","#ff5533"),
]

ACHIEVEMENTS = [
    {"id":"first_buy", "name":"첫 매수",      "icon":"🎯", "check":lambda g:g["trades"]>=1},
    {"id":"trade10",   "name":"거래 10회",     "icon":"📊", "check":lambda g:g["trades"]>=10},
    {"id":"trade50",   "name":"거래 50회",     "icon":"📊📊","check":lambda g:g["trades"]>=50},
    {"id":"profit",    "name":"첫 흑자",       "icon":"💚", "check":lambda g:g["total"]>INITIAL_MONEY},
    {"id":"m20",       "name":"2천만 달성",    "icon":"💰", "check":lambda g:g["total"]>=20_000_000},
    {"id":"m50",       "name":"5천만 달성",    "icon":"💰💰","check":lambda g:g["total"]>=50_000_000},
    {"id":"m100",      "name":"1억 달성",      "icon":"🤑", "check":lambda g:g["total"]>=100_000_000},
    {"id":"div",       "name":"배당 수령",     "icon":"🎁", "check":lambda g:g["total_div"]>=1},
    {"id":"diverse",   "name":"4종목 이상 보유","icon":"🌐","check":lambda g:g["unique"]>=4},
    {"id":"all",       "name":"전 종목 보유",  "icon":"🌐🌐","check":lambda g:g["unique"]>=15},
    {"id":"recover",   "name":"손실 후 회복",  "icon":"🛡", "check":lambda g:g["recovered"]},
]

# ══════════════════════════════════════════════
# 게임 상태 (서버 메모리)
# ══════════════════════════════════════════════
game_lock = threading.Lock()
game = {}
new_events = []   # SSE 이벤트 큐

def init_stock(name):
    p = PROFILES[name]
    return {"price":float(p["base"]),"year":2000,"candles":[],
            "tick":0,"open":float(p["base"]),"high":float(p["base"]),
            "low":float(p["base"]),"vol":0}

def init_game():
    global game
    game = {
        "money":float(INITIAL_MONEY),"portfolio":{},"buy_avg":{},
        "realized_pnl":0.0,"total_div":0.0,"trades":0,
        "unlocked":[],"trade_log":[],"recovered":False,
        "min_asset":float(INITIAL_MONEY),"tick":0,
        "stocks":{n:init_stock(n) for n in STOCK_NAMES},
        "last_news":"📡 시장 개장 대기 중...",
    }

def load_game():
    global game
    if not os.path.exists(SAVE_FILE):
        init_game(); return
    try:
        with open(SAVE_FILE,"r",encoding="utf-8") as f:
            d = json.load(f)
        # 비정상 주가 체크
        ok = all(d.get("stocks",{}).get(n,{}).get("price",0) >= PROFILES[n]["base"]*0.10
                 for n in STOCK_NAMES if n in d.get("stocks",{}))
        if not ok:
            d["stocks"] = {}; d["portfolio"] = {}; d["buy_avg"] = {}
        init_game()
        for k in ["money","portfolio","buy_avg","realized_pnl","total_div",
                  "trades","unlocked","trade_log","recovered","tick","last_news"]:
            if k in d: game[k] = d[k]
        game["min_asset"] = d.get("min_asset", float(INITIAL_MONEY))
        for n,sd in d.get("stocks",{}).items():
            if n in STOCK_NAMES: game["stocks"][n] = sd
        # 빠진 종목 보충
        for n in STOCK_NAMES:
            if n not in game["stocks"]: game["stocks"][n] = init_stock(n)
        print("[불러오기 완료]")
    except Exception as e:
        print(f"[불러오기 실패 → 새 게임] {e}")
        init_game()

def save_game():
    try:
        with open(SAVE_FILE,"w",encoding="utf-8") as f:
            json.dump(game, f, ensure_ascii=False)
    except Exception as e:
        print(f"[저장 실패] {e}")

# ══════════════════════════════════════════════
# GBM 틱 로직
# ══════════════════════════════════════════════
def randn():
    import math
    u,v=0,0
    while u==0: u=random.random()
    while v==0: v=random.random()
    return math.sqrt(-2*math.log(u))*math.cos(2*math.pi*v)

def tick_stock(s, name, macro_shock):
    p   = PROFILES[name]
    dt  = 1/252
    ret = (p["mu"] - .5*p["sigma"]**2)*dt + p["sigma"]*math.sqrt(dt)*randn() + p["beta"]*macro_shock
    news = None
    if random.random() < 0.04:
        title, impact = random.choice(p["events"])
        ret += impact + (random.random()-.5)*.02
        news = f"📰 [{name}] {title}"
    ret     = max(ret, -0.15)
    floor   = p["base"] * 0.05
    s["price"] = max(floor, s["price"] * math.exp(ret))
    s["high"]  = max(s["high"], s["price"])
    s["low"]   = min(s["low"],  s["price"])
    s["vol"]  += random.randint(10000, 500000)
    s["tick"] += 1
    if s["tick"] >= CANDLE_TICKS:
        s["candles"].append({"year":s["year"],"open":s["open"],"high":s["high"],
                              "low":s["low"],"close":s["price"],"vol":s["vol"]})
        s["year"]+=1; s["tick"]=0; s["open"]=s["price"]
        s["high"]=s["price"]; s["low"]=s["price"]; s["vol"]=0
    return news

def total_asset():
    return game["money"] + sum(
        game["stocks"][n]["price"]*q for n,q in game["portfolio"].items() if q>0)

def check_achievements():
    tot    = total_asset()
    unique = sum(1 for q in game["portfolio"].values() if q>0)
    gs     = {"trades":game["trades"],"total":tot,"total_div":game["total_div"],
              "unique":unique,"recovered":game["recovered"]}
    newly  = []
    for a in ACHIEVEMENTS:
        if a["id"] not in game["unlocked"] and a["check"](gs):
            game["unlocked"].append(a["id"])
            newly.append(f"🏆 업적 달성! {a['icon']} {a['name']}")
    return newly

def market_tick():
    """백그라운드 틱 스레드"""
    save_counter = 0
    while True:
        time.sleep(TICK_SEC)
        with game_lock:
            game["tick"] += 1
            macro_shock, macro_news = 0.0, ""
            if game["tick"] % MACRO_TICKS == 0:
                title, shock = random.choice(MACRO_EVENTS)
                macro_shock = shock; macro_news = title

            stock_news_list = []
            for name in STOCK_NAMES:
                news = tick_stock(game["stocks"][name], name, macro_shock)
                if news: stock_news_list.append(news)

            display_news = macro_news or (stock_news_list[0] if stock_news_list else "")
            if display_news: game["last_news"] = display_news

            # 배당
            div_msg = ""
            if game["tick"] % DIVIDEND_TICKS == 0:
                total_d = sum(
                    game["stocks"][n]["price"] * q * PROFILES[n]["div"] / 4
                    for n,q in game["portfolio"].items() if q>0
                )
                if total_d > 0:
                    game["money"] += total_d; game["total_div"] += total_d
                    div_msg = f"🎁 분기 배당금 +{int(total_d):,}원 입금"

            # 회복 감지
            tot = total_asset()
            if tot < game["min_asset"]: game["min_asset"] = tot
            if not game["recovered"] and tot>INITIAL_MONEY and game["min_asset"]<INITIAL_MONEY*.7:
                game["recovered"] = True

            new_ach = check_achievements()

            # SSE 이벤트 큐에 추가
            evt = {"type":"tick","news":display_news}
            if div_msg:   evt["dividend"] = div_msg
            if new_ach:   evt["achievements"] = new_ach
            new_events.append(evt)

            save_counter += 1
            if save_counter >= 5:   # 15초마다 저장
                save_game(); save_counter = 0

# ══════════════════════════════════════════════
# Flask 라우트
# ══════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/state")
def api_state():
    with game_lock:
        tot = total_asset()
        lvl = LEVELS[0]
        for l in LEVELS:
            if tot >= l[0]: lvl = l
        return jsonify({
            "money":   game["money"],
            "total":   tot,
            "pnl_pct": (tot/INITIAL_MONEY-1)*100,
            "level":   {"name":lvl[1],"color":lvl[2]},
            "portfolio":  game["portfolio"],
            "buy_avg":    game["buy_avg"],
            "trade_log":  game["trade_log"][-30:],
            "unlocked":   game["unlocked"],
            "last_news":  game["last_news"],
            "stocks": {
                n: {
                    "price":  s["price"],
                    "year":   s["year"],
                    "open":   s["open"],
                    "high":   s["high"],
                    "low":    s["low"],
                    "vol":    s["vol"],
                    "candles":s["candles"][-300:],  # 최근 300봉만
                    "desc":   PROFILES[n]["desc"],
                    "chg":    (s["price"]/s["candles"][-1]["close"]-1)*100 if s["candles"] else 0,
                }
                for n,s in game["stocks"].items()
            }
        })

@app.route("/api/stock/<name>")
def api_stock(name):
    if name not in game["stocks"]: return jsonify({"error":"not found"}),404
    with game_lock:
        s = game["stocks"][name]
        return jsonify({
            "price":  s["price"], "year":s["year"],
            "open":s["open"],"high":s["high"],"low":s["low"],"vol":s["vol"],
            "candles": s["candles"],
            "desc": PROFILES[name]["desc"],
        })

@app.route("/api/buy", methods=["POST"])
def api_buy():
    data = request.json
    name = data.get("name"); qty = int(data.get("qty",1))
    if name not in game["stocks"]: return jsonify({"ok":False,"msg":"종목 없음"})
    with game_lock:
        s  = game["stocks"][name]
        ep = s["price"]*(1+SLIPPAGE)
        if game["money"] < ep*qty:
            return jsonify({"ok":False,"msg":"잔액 부족!"})
        game["money"] -= ep*qty
        pq = game["portfolio"].get(name,0)
        pa = game["buy_avg"].get(name,0.0)
        nq = pq+qty
        game["buy_avg"][name]   = (pa*pq+ep*qty)/nq
        game["portfolio"][name] = nq
        game["trades"] += qty
        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] 매수 {name} {qty}주 @ {int(ep):,}"
        game["trade_log"].append(entry)
        new_ach = check_achievements()
        save_game()
        return jsonify({"ok":True,"msg":entry,"money":game["money"],"achievements":new_ach})

@app.route("/api/sell", methods=["POST"])
def api_sell():
    data = request.json
    name = data.get("name"); qty = int(data.get("qty",1))
    if name not in game["stocks"]: return jsonify({"ok":False,"msg":"종목 없음"})
    with game_lock:
        qty_have = game["portfolio"].get(name,0)
        qty      = min(qty, qty_have)
        if qty <= 0: return jsonify({"ok":False,"msg":"보유 주식 없음!"})
        s   = game["stocks"][name]
        avg = game["buy_avg"].get(name,s["price"])
        ep  = s["price"]*(1-SLIPPAGE)
        rp  = (ep-avg)*qty
        tax = max(0.0, rp*TAX_RATE)
        game["money"]   += ep*qty-tax
        game["realized_pnl"] += rp-tax
        game["portfolio"][name] = qty_have-qty
        game["trades"] += qty
        ts    = datetime.now().strftime("%H:%M:%S")
        sign  = "+" if rp>=0 else ""
        tax_s = f" 세금-{int(tax):,}" if tax>0 else ""
        entry = f"[{ts}] 매도 {name} {qty}주 @ {int(ep):,} 손익{sign}{int(rp):,}{tax_s}"
        game["trade_log"].append(entry)
        new_ach = check_achievements()
        save_game()
        return jsonify({"ok":True,"msg":entry,"money":game["money"],"achievements":new_ach})

@app.route("/api/new_game", methods=["POST"])
def api_new_game():
    with game_lock:
        if os.path.exists(SAVE_FILE): os.remove(SAVE_FILE)
        init_game()
    return jsonify({"ok":True})

@app.route("/api/achievements")
def api_achievements():
    with game_lock:
        return jsonify([
            {"id":a["id"],"name":a["name"],"icon":a["icon"],
             "done":a["id"] in game["unlocked"]}
            for a in ACHIEVEMENTS
        ])

@app.route("/api/events")
def api_events():
    """SSE 스트림 — 틱마다 뉴스/배당 등 푸시"""
    def generate():
        idx = [len(new_events)]   # 리스트로 감싸 클로저 변수 수정 허용
        # 연결 즉시 ping 전송 (브라우저 연결 확인용)
        yield "data: {\"type\":\"ping\"}\n\n"
        while True:
            try:
                with game_lock:
                    evts = new_events[idx[0]:]
                    idx[0] = len(new_events)
                for e in evts:
                    yield f"data: {json.dumps(e, ensure_ascii=False)}\n\n"
                # 30초마다 keepalive (프록시/도커 타임아웃 방지)
                if int(time.time()) % 30 == 0:
                    yield ": keepalive\n\n"
            except GeneratorExit:
                break
            except Exception:
                pass
            time.sleep(0.5)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering":"no",
            "Connection":       "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

@app.errorhandler(500)
def internal_error(e):
    import traceback
    return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

# ══════════════════════════════════════════════
if __name__ == "__main__":
    load_game()
    t = threading.Thread(target=market_tick, daemon=True)
    t.start()
    print("=" * 45)
    print("  📈 StockVerse 웹서버 시작!")
    print("  브라우저에서 http://localhost:5000 열기")
    print("=" * 45)
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
dddosodos
