# Adsgram Landing Service

A tiny standalone Flask app that serves the Adsgram ad page used by the
Campus Post Bot's button links. Deploy it as its own Render web service,
separate from the bot itself.

It exposes:

- `GET /ads` — the branded landing page. Loads inside Telegram as a Mini
  App, reads the click token, resolves it, shows the Adsgram ad, then
  redirects to the real link.
- `GET /resolve/<token>` — looks up a token in MongoDB and returns
  `{ target_url, block_id }`. Used by the page itself via `fetch`.
- `GET /healthz` — plain health check for Render.

It does **not** run the bot. It only needs read access to the same
MongoDB database the bot writes `adredirects` tokens into.

## Why a separate service?

The bot already serves an equivalent `/ads` route by default — you don't
strictly need this. Use this standalone service instead if you'd rather:

- keep the ad-landing page on its own URL/branding, independent of the bot
- scale or restart it without touching the bot process
- customize the page's look without editing the bot's code

## 1. Deploy to Render

1. Push this folder to its own GitHub repo (or a subfolder of a repo — Render
   lets you set a "Root Directory" if it's a monorepo).
2. On Render: **New → Web Service** → connect the repo → set **Root
   Directory** to this folder if needed → Render should auto-detect Python.
   (Or use **New → Blueprint** with the included `render.yaml`.)
3. Build command: `pip install -r requirements.txt`
   Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Set environment variables:
   - `MONGO_URI` — **the exact same connection string** used by the bot
     service, so it can see the tokens the bot creates.
   - `DB_NAME` — must match the bot's `DB_NAME` (defaults to
     `campus_post_bot` on both sides — leave both default and it just
     works).
   - `BRAND_NAME` — optional, text shown on the page (defaults to
     "Campus Post").
5. Deploy. Once live, your page is reachable at:
   `https://<this-service>.onrender.com/ads`

## 2. Point BotFather's Mini App at it

1. Talk to [@BotFather](https://t.me/BotFather) → `/newapp` → select your
   bot → give it a short name (e.g. `ads`) → for the Web App URL, paste
   `https://<this-service>.onrender.com/ads`.
2. BotFather returns a direct link like `https://t.me/YourBot/ads`.

## 3. Wire it into the bot

On the **bot's** Render service, set:

```
ADSGRAM_MINIAPP_LINK=https://t.me/YourBot/ads
```

and redeploy the bot. From then on, posts with buttons will route through
this landing service when Adsgram is turned on for a channel.

## Local testing

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in MONGO_URI
python app.py           # serves on http://localhost:8080
```

Visit `http://localhost:8080/ads?startapp=<a real token from your DB>` in a
browser to preview the page outside of Telegram (the Adsgram ad itself only
renders inside a real Telegram Mini App context, but the redirect logic and
styling can be checked this way).
