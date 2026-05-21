import anthropic
import json
import os
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
today = datetime.now(JST)
today_str = today.strftime("%Y年%-m月%-d日")
today_iso = today.strftime("%Y/%m/%d %H:%M")
weekdays = ["月","火","水","木","金","土","日"]
today_label = f"{today_str}（{weekdays[today.weekday()]}）"

PROMPT = f"""あなたは信頼性の高い日本語ニュースキュレーターです。
今日（{today_str}）の重要ニュースをまとめてください。

【参照ソース（信憑性順）】
1. NHK NEWS WEB (nhk.or.jp)
2. Reuters日本語版 (jp.reuters.com)
3. 日本経済新聞 (nikkei.com)
4. BBC News Japan (bbc.com/japanese)
5. 共同通信 (nordot.app)

【条件】
- エンタメ・スポーツ・芸能は必ず除外
- 政治・経済・国際・社会・科学技術から各2〜3記事（合計10〜12記事）
- 要約は必ず5行（各行25〜35字の読みやすい文）
- URLはドメインを正確に記載（実在するドメインのみ）
- 最も重要な記事1件のみimportance: "high"、残りは"medium"

【出力形式 - 必ずJSONのみ、前後に余計なテキスト不要】
{{
  "articles": [
    {{
      "id": "1",
      "genre": "politics|economy|international|science|society",
      "title": "記事タイトル（30字以内）",
      "source": "ソース名",
      "url": "https://ソースのトップURL",
      "summary": ["1行目", "2行目", "3行目", "4行目", "5行目"],
      "importance": "high|medium",
      "tags": ["タグ1", "タグ2"]
    }}
  ]
}}"""

def generate_news():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": PROMPT}]
    )
    raw = message.content[0].text
    clean = raw.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)
    return data["articles"]

def build_html(articles):
    genres = [
        {"id": "all",           "label": "全て",   "emoji": "📰"},
        {"id": "international", "label": "国際",   "emoji": "🌏"},
        {"id": "politics",      "label": "政治",   "emoji": "🏛️"},
        {"id": "economy",       "label": "経済",   "emoji": "📈"},
        {"id": "science",       "label": "科学",   "emoji": "🔬"},
        {"id": "society",       "label": "社会",   "emoji": "🏙️"},
    ]

    articles_json = json.dumps(articles, ensure_ascii=False)
    genres_json   = json.dumps(genres,   ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="朝刊">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' https://script.google.com https://*.googleapis.com; img-src 'self' data:; manifest-src 'self'; worker-src 'self';">
<title>朝刊ブリーフィング</title>
<style>
:root{{--bg:#0d0d12;--surface:#141418;--border:#1e1e26;--gold:#c9a84c;--text:#e8e4d9;--muted:#6a6458;--dim:#333;}}
*{{box-sizing:border-box;-webkit-tap-highlight-color:transparent;margin:0;padding:0;}}
body{{background:var(--bg);color:var(--text);font-family:-apple-system,'Hiragino Sans','Yu Gothic',sans-serif;min-height:100dvh;max-width:430px;margin:0 auto;}}
::-webkit-scrollbar{{display:none;}}
#header{{background:rgba(13,13,18,0.96);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);position:sticky;top:0;z-index:100;border-bottom:1px solid var(--border);padding-top:env(safe-area-inset-top,44px);}}
.header-inner{{padding:14px 20px 12px;display:flex;justify-content:space-between;align-items:flex-end;}}
.header-date{{font-size:11px;color:var(--dim);margin-bottom:3px;letter-spacing:0.04em;}}
.header-title{{font-size:22px;font-weight:700;letter-spacing:-0.02em;}}
.header-sources{{font-size:10px;color:#2a2a35;text-align:right;line-height:1.6;}}
.tabs{{display:flex;overflow-x:auto;gap:8px;padding:0 20px 14px;scrollbar-width:none;}}
.tab{{flex-shrink:0;padding:8px 14px;border-radius:20px;border:none;background:#1a1a22;color:#666;font-size:13px;cursor:pointer;display:flex;gap:5px;align-items:center;transition:all 0.15s;font-family:-apple-system,'Hiragino Sans',sans-serif;}}
.tab.active{{background:var(--gold);color:#000;font-weight:700;}}
.tab-count{{background:#252530;border-radius:10px;padding:1px 6px;font-size:10px;color:#444;}}
.tab.active .tab-count{{background:rgba(0,0,0,0.2);color:#000;}}
#content{{padding-bottom:40px;}}
.section-label{{padding:18px 20px 8px;font-size:10px;color:var(--dim);letter-spacing:0.1em;}}
.top-wrap{{padding:14px 16px 0;}}
.top-label{{font-size:10px;color:var(--gold);letter-spacing:0.15em;margin-bottom:10px;padding-left:4px;}}
.top-card{{border-radius:20px;padding:22px;cursor:pointer;border:1px solid rgba(255,255,255,0.06);position:relative;overflow:hidden;transition:opacity 0.15s;-webkit-user-select:none;user-select:none;}}
.top-card:active{{opacity:0.75;}}
.top-glow{{position:absolute;top:0;right:0;width:100px;height:100px;border-radius:0 20px 0 0;pointer-events:none;}}
.badge{{padding:4px 10px;border-radius:20px;font-size:12px;display:inline-flex;align-items:center;gap:4px;}}
.badges{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;}}
.source-badge{{background:rgba(255,255,255,0.06);color:#666;}}
.top-title{{font-size:18px;font-weight:700;line-height:1.45;margin-bottom:11px;letter-spacing:-0.01em;}}
.top-lead{{font-size:13px;color:#7a7060;line-height:1.6;margin-bottom:14px;letter-spacing:0.02em;}}
.top-footer{{display:flex;justify-content:space-between;align-items:center;}}
.tags{{display:flex;gap:6px;}}
.tag{{font-size:11px;color:#444;}}
.row{{margin:0 16px;border-bottom:1px solid #141418;padding:16px 4px;cursor:pointer;display:flex;gap:14px;align-items:flex-start;transition:opacity 0.15s;-webkit-user-select:none;user-select:none;}}
.row:active{{opacity:0.55;}}
.row-icon{{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;margin-top:2px;border:1px solid rgba(255,255,255,0.05);}}
.row-body{{flex:1;min-width:0;}}
.row-meta{{display:flex;gap:6px;margin-bottom:4px;align-items:center;font-size:11px;}}
.row-title{{font-size:15px;font-weight:600;color:#d0ccbc;margin-bottom:4px;line-height:1.4;letter-spacing:-0.01em;}}
.row-lead{{font-size:12px;color:#555;line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}}
.row-arrow{{color:#2a2a35;font-size:16px;flex-shrink:0;margin-top:10px;}}
#detail{{display:none;min-height:100dvh;flex-direction:column;}}
#detail.active{{display:flex;}}
.detail-header{{padding-top:env(safe-area-inset-top,44px);padding-bottom:22px;padding-left:20px;padding-right:20px;flex-shrink:0;}}
.back-btn{{background:rgba(255,255,255,0.08);border:none;color:#fff;border-radius:20px;padding:8px 16px;font-size:14px;cursor:pointer;margin-bottom:18px;display:inline-block;font-family:-apple-system,'Hiragino Sans',sans-serif;}}
.detail-title{{font-size:19px;font-weight:700;line-height:1.5;letter-spacing:-0.01em;}}
.detail-body{{flex:1;overflow-y:auto;padding:22px 20px;}}
.summary-box{{background:var(--surface);border-radius:16px;padding:20px;margin-bottom:18px;}}
.summary-label{{font-size:11px;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:12px;}}
.summary-row{{display:flex;gap:12px;margin-bottom:12px;align-items:flex-start;}}
.summary-num{{width:22px;height:22px;border-radius:50%;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;}}
.summary-text{{font-size:15px;line-height:1.65;letter-spacing:0.02em;}}
.detail-tags{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:22px;}}
.detail-tag{{background:#1e1e26;color:#555;padding:5px 12px;border-radius:20px;font-size:12px;}}
.source-link{{display:flex;align-items:center;justify-content:space-between;background:var(--surface);border-radius:14px;padding:16px 20px;text-decoration:none;}}
.source-link-label{{font-size:11px;color:#555;margin-bottom:4px;}}
.footer-note{{text-align:center;padding:24px 20px 8px;font-size:10px;color:#1e1e26;}}
#list.hidden{{display:none;}}
</style>
</head>
<body>
<div id="list">
  <div id="header">
    <div class="header-inner">
      <div>
        <div class="header-date">{today_label}</div>
        <div class="header-title">朝刊ブリーフィング</div>
      </div>
      <div class="header-sources">NHK / 日経<br>Reuters / 時事</div>
    </div>
    <div class="tabs" id="tabs"></div>
  </div>
  <div id="content"></div>
</div>
<div id="detail">
  <div class="detail-header" id="detail-header">
    <button class="back-btn" onclick="closeDetail()">← 戻る</button>
    <div class="badges" id="detail-badges"></div>
    <div class="detail-title" id="detail-title"></div>
  </div>
  <div class="detail-body">
    <div class="summary-box" id="summary-box">
      <div class="summary-label" id="summary-label-el"></div>
      <div id="summary-rows"></div>
    </div>
    <div class="detail-tags" id="detail-tags"></div>
    <a class="source-link" id="source-link" href="#" target="_blank" rel="noopener noreferrer">
      <div>
        <div class="source-link-label">元記事を開く</div>
        <div class="source-link-name" id="source-link-name"></div>
      </div>
      <div class="source-link-icon" id="source-link-icon">↗</div>
    </a>
  </div>
</div>
<script>
const NEWS={articles_json};
const GENRES={genres_json};
const COLORS={{politics:{{bg:"#15192a",accent:"#4a7fc1",light:"#7aabea"}},economy:{{bg:"#14221a",accent:"#3a9c5a",light:"#6ecf8a"}},international:{{bg:"#221525",accent:"#9c4ab0",light:"#cd7ee0"}},science:{{bg:"#0f1e22",accent:"#3a9c9c",light:"#6ecfcf"}},society:{{bg:"#22190e",accent:"#c9863c",light:"#e8ad6a"}}}};
function col(g){{return COLORS[g]||{{bg:"#181820",accent:"#c9a84c",light:"#e0c87a"}};}}
let activeGenre="all";
function genreInfo(id){{return GENRES.find(g=>g.id===id)||GENRES[0];}}
function count(id){{return id==="all"?NEWS.length:NEWS.filter(a=>a.genre===id).length;}}
function renderTabs(){{
  document.getElementById("tabs").innerHTML=GENRES.map(g=>`<button class="tab${{activeGenre===g.id?" active":""}}" onclick="setGenre('${{g.id}}')">${{g.emoji}} ${{g.label}}${{count(g.id)>0?`<span class="tab-count">${{count(g.id)}}</span>`:""}}</button>`).join("");
}}
function setGenre(id){{activeGenre=id;renderTabs();renderContent();window.scrollTo(0,0);}}
function renderContent(){{
  const filtered=activeGenre==="all"?NEWS:NEWS.filter(a=>a.genre===activeGenre);
  const top=filtered.find(a=>a.importance==="high");
  const rest=filtered.filter(a=>a!==top);
  const el=document.getElementById("content");
  let html="";
  if(top){{
    const c=col(top.genre);const gi=genreInfo(top.genre);
    html+=`<div class="top-wrap"><div class="top-label">◈ TOP STORY</div><div class="top-card" style="background:${{c.bg}};border-color:${{c.accent}}33" onclick="openDetail('${{top.id}}')"><div class="top-glow" style="background:radial-gradient(circle at top right,${{c.accent}}18,transparent 70%)"></div><div class="badges"><span class="badge" style="background:${{c.accent}}22;color:${{c.light}}">${{gi.emoji}} ${{gi.label}}</span><span class="badge source-badge">${{top.source}}</span></div><div class="top-title" style="color:#f0ece0">${{top.title}}</div><div class="top-lead">${{top.summary[0]}}</div><div class="top-footer"><div class="tags">${{(top.tags||[]).slice(0,2).map(t=>`<span class="tag">#${{t}}</span>`).join("")}}</div><span style="font-size:13px;color:${{c.accent}}">詳細 →</span></div></div></div>`;
  }}
  if(top&&rest.length>0)html+=`<div class="section-label">その他のニュース</div>`;
  rest.forEach((a,i)=>{{
    const c=col(a.genre);const gi=genreInfo(a.genre);
    html+=`<div class="row" style="${{i===rest.length-1?"border-bottom:none":""}}" onclick="openDetail('${{a.id}}')"><div class="row-icon" style="background:${{c.bg}}">${{gi.emoji}}</div><div class="row-body"><div class="row-meta"><span style="color:${{c.light}}">${{gi.label}}</span><span style="color:#2a2a35">·</span><span style="color:#444">${{a.source}}</span></div><div class="row-title">${{a.title}}</div><div class="row-lead">${{a.summary[0]}}</div></div><div class="row-arrow">›</div></div>`;
  }});
  if(filtered.length===0)html=`<div style="text-align:center;padding:80px 20px"><div style="font-size:40px;margin-bottom:12px">📭</div><p style="color:#444;font-size:14px">このジャンルの記事はありません</p></div>`;
  html+=`<div class="footer-note">自動更新 {today_iso} · NHK / 日経 / Reuters / 時事</div>`;
  el.innerHTML=html;
}}
function openDetail(id){{
  const a=NEWS.find(x=>x.id===id);if(!a)return;
  const c=col(a.genre);const gi=genreInfo(a.genre);
  document.getElementById("detail-header").style.background=c.bg;
  document.getElementById("detail-header").style.borderBottom=`1px solid ${{c.accent}}22`;
  document.getElementById("detail-badges").innerHTML=`<span class="badge" style="background:${{c.accent}}22;color:${{c.light}}">${{gi.emoji}} ${{gi.label}}</span><span class="badge source-badge">${{a.source}}</span>`;
  document.getElementById("detail-title").textContent=a.title;
  document.getElementById("summary-box").style.borderLeft=`3px solid ${{c.accent}}`;
  document.getElementById("summary-label-el").style.color=c.light;
  document.getElementById("summary-label-el").textContent="5行要約";
  document.getElementById("summary-rows").innerHTML=(a.summary||[]).map((line,i)=>`<div class="summary-row"><div class="summary-num" style="background:${{i===0?c.accent:"rgba(255,255,255,0.06)"}};color:${{i===0?"#000":"#666"}}">${{i+1}}</div><div class="summary-text" style="color:${{i===0?"#e8e4d9":"#847a68"}}">${{line}}</div></div>`).join("");
  document.getElementById("detail-tags").innerHTML=(a.tags||[]).map(t=>`<span class="detail-tag">#${{t}}</span>`).join("");
  const link=document.getElementById("source-link");
  link.href=a.url;link.style.border=`1px solid ${{c.accent}}33`;
  document.getElementById("source-link-name").style.color=c.light;
  document.getElementById("source-link-name").textContent=a.source;
  document.getElementById("source-link-icon").style.color=c.accent;
  document.getElementById("list").classList.add("hidden");
  document.getElementById("detail").classList.add("active");
  window.scrollTo(0,0);
}}
function closeDetail(){{document.getElementById("detail").classList.remove("active");document.getElementById("list").classList.remove("hidden");}}
let touchStartX=0;
document.addEventListener("touchstart",e=>{{touchStartX=e.touches[0].clientX;}},{{passive:true}});
document.addEventListener("touchend",e=>{{if(document.getElementById("detail").classList.contains("active")){{if(e.changedTouches[0].clientX-touchStartX>80)closeDetail();}}}},{{passive:true}});
renderTabs();renderContent();
</script>
</body>
</html>"""

if __name__ == "__main__":
    print("ニュースを生成中...")
    articles = generate_news()
    print(f"{len(articles)}件の記事を取得しました")
    html = build_html(articles)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html を生成しました")
