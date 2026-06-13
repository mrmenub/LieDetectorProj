# CLAUDE.md

Project context for Claude Code. Keep this accurate as the code changes.

## What this is

**TruthLens AI** (a.k.a. "AI Credibility Detector") — a single-page Flask web app
that rates how trustworthy a news article or image is. The user either pastes an
article URL or uploads an image (screenshot / tweet / meme), and the app returns a
credibility score, a subjectivity metric, a clickbait-flag count, and a short
written verdict.

It is a small demo / teaching project — one route, one template, no database.

## How it works

- **URL path:** scrape the page with `requests` + `BeautifulSoup`, strip
  script/style, run `TextBlob` for a subjectivity score, dock points for
  "clickbait" red-flag words, then ask **Google Gemini** (`gemini-2.5-flash`) for a
  2–3 sentence verdict.
- **Image path:** send the uploaded image bytes straight to Gemini and parse a
  `SCORE:` / `VERDICT:` response.

The rule-based score (0–100) is the source of truth for the gauge; Gemini only
provides the prose verdict (and the score itself, for the image path).

## Layout

| File | Role |
|------|------|
| `app.py` | Flask app — the real entry point. All routes, scraping, scoring, Gemini calls. |
| `detector.py` | Standalone CLI version of the URL analyzer (`python detector.py`). Not imported by `app.py` — the scoring logic is duplicated there. |
| `templates/index.html` | The entire UI (inline CSS). Landing page + analyzer form + results dashboard, toggled by `show_analyzer`. |
| `requirements.txt` | Python deps. |
| `Procfile` | `web: gunicorn app:app` — for Heroku-style deploys. |

## Running it

The app reads `GEMINI_API_KEY` from the environment. Without it, scraping and
scoring still work but the Gemini verdict falls back to an offline message.

```bash
# uses the checked-in virtualenv
export GEMINI_API_KEY=your-key-here      # or put it in a .env (see .env.example)
.venv/bin/python app.py                  # serves on http://localhost:5001
```

Press F5 in VS Code to run/debug it (see `.vscode/launch.json`).

## Gotchas

- **`app.py` and `detector.py` duplicate `extract_article_text` /
  `analyze_truthfulness`.** If you change scoring, change it in both or refactor
  the shared logic into `detector.py` and import it.
- `app.py` pins `google-genai==0.1.1` in `requirements.txt`, but the code uses the
  modern `genai.Client(...)` API (installed: 2.x). The pin is stale — bump it if
  you touch deps.
- The bare `except:` in `app.py`'s `extract_article_text` swallows all errors.
- The gauge marker in `index.html` carries a `data-score` attribute but there is no
  JS positioning it, so the marker doesn't currently move with the score.
- Default port is **5001** (not 5000), to dodge macOS AirPlay.
