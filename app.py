import os
from flask import Flask, jsonify, Response
from pymongo import MongoClient

MONGO_URI = os.environ["MONGO_URL"]
# Must match the DB_NAME used by the bot service, so tokens created by the
# bot are visible here.
DB_NAME = os.environ.get("DB_NAME", "campus_post_bot")
BRAND_NAME = os.environ.get("BRAND_NAME", "Campus Post")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
adredirects_col = db["adredirects"]

app = Flask(__name__)

PAGE_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
<title>{brand} — Sponsored</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<script src="https://sad.adsgram.ai/js/sad.min.js"></script>
<style>
  :root {{
    color-scheme: dark;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0; padding: 0; height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: radial-gradient(circle at top, #1c1c2b 0%, #0b0b12 70%);
    color: #f2f2f6;
  }}
  .wrap {{
    min-height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px 20px;
    text-align: center;
  }}
  .card {{
    max-width: 360px;
    width: 100%;
  }}
  .badge {{
    display: inline-block;
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #9a9ab0;
    background: rgba(255,255,255,0.06);
    padding: 4px 12px;
    border-radius: 999px;
    margin-bottom: 20px;
  }}
  .spinner {{
    width: 44px; height: 44px;
    margin: 0 auto 24px;
    border-radius: 50%;
    border: 3px solid rgba(255,255,255,0.12);
    border-top-color: #6c8cff;
    animation: spin 0.9s linear infinite;
  }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  h1 {{
    font-size: 17px;
    font-weight: 600;
    margin: 0 0 8px;
  }}
  p.sub {{
    font-size: 14px;
    color: #a3a3b8;
    margin: 0;
    line-height: 1.5;
  }}
  .brand {{
    margin-top: 40px;
    font-size: 12px;
    color: #55556a;
  }}
  .fallback {{
    margin-top: 24px;
    display: none;
  }}
  .fallback a {{
    display: inline-block;
    padding: 10px 22px;
    border-radius: 10px;
    background: #6c8cff;
    color: #0b0b12;
    font-weight: 600;
    text-decoration: none;
    font-size: 14px;
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <div class="badge">Sponsored</div>
    <div class="spinner" id="spinner"></div>
    <h1 id="title">Loading your link…</h1>
    <p class="sub" id="subtitle">This will only take a moment.</p>
    <div class="fallback" id="fallback">
      <a href="#" id="fallback-link">Continue</a>
    </div>
  </div>
  <div class="brand">{brand}</div>
</div>

<script>
function getToken() {{
  try {{
    if (window.Telegram && window.Telegram.WebApp) {{
      window.Telegram.WebApp.ready();
      var sp = window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.start_param;
      if (sp) return sp;
    }}
  }} catch (e) {{}}
  var params = new URLSearchParams(window.location.search || window.location.hash.replace('#', '?'));
  return params.get('startapp') || params.get('tgWebAppStartParam') || params.get('token');
}}

function showError(msg) {{
  document.getElementById('spinner').style.display = 'none';
  document.getElementById('title').innerText = msg;
  document.getElementById('subtitle').innerText = '';
}}

function goTo(url) {{
  if (!url) {{ showError('This link has expired.'); return; }}
  document.getElementById('fallback-link').href = url;
  document.getElementById('fallback').style.display = 'block';
  window.location.href = url;
}}

(async function () {{
  var token = getToken();
  if (!token) {{ showError('Invalid link.'); return; }}

  var target = null, blockId = null;
  try {{
    var res = await fetch('/resolve/' + encodeURIComponent(token));
    if (res.ok) {{
      var data = await res.json();
      target = data.target_url;
      blockId = data.block_id;
    }}
  }} catch (e) {{}}

  if (!target) {{ showError('This link has expired.'); return; }}

  document.getElementById('title').innerText = 'Showing a quick ad…';

  if (blockId && window.Adsgram) {{
    try {{
      await window.Adsgram.init({{ blockId: blockId }}).show();
    }} catch (e) {{
      // no ad available or user closed it early — continue to the real link anyway
    }}
  }}

  document.getElementById('title').innerText = 'Redirecting…';
  goTo(target);
}})();
</script>
</body>
</html>
""".format(brand=BRAND_NAME)


@app.get("/ads")
def ads_page():
    return Response(PAGE_HTML, mimetype="text/html")


@app.get("/resolve/<token>")
def resolve(token):
    doc = adredirects_col.find_one({"token": token})
    if not doc:
        return jsonify({"error": "not found"}), 404
    return jsonify({"target_url": doc["target_url"], "block_id": doc.get("block_id")})


@app.get("/healthz")
def health():
    return "ok"


@app.get("/")
def index():
    return Response(
        f"<h1>{BRAND_NAME} — Adsgram landing service</h1>"
        f"<p>This service resolves ad-wrapped links for the Campus Post Bot. "
        f"Nothing to see here directly — links look like <code>/ads?startapp=&lt;token&gt;</code>.</p>",
        mimetype="text/html",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
