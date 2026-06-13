# TruthLens AI — Team Task Board

Three independent tracks so we don't edit the same files. Pick a track, make a
branch (`git checkout -b track-a-backend`), open a PR when done.

## ✅ Already done (don't redo)
- Project runs locally: `.venv/bin/python app.py` → http://localhost:5001
- Dependencies installed & fixed for Python 3.14 (`google-genai`, `pillow` pins).
- `.env` loading wired up (`load_dotenv(override=True)`) — Gemini key works.
- URL scraper rewritten: real browser headers, auto-adds `https://`, and reports
  the *actual* error (403 / timeout / bad URL) instead of one vague message.
- VS Code config (`.vscode/`) + project notes (`CLAUDE.md`).

---

## Track A — Backend & scoring  (owner: __________)
Files: `app.py`, `detector.py`
- [ ] **De-duplicate logic.** `extract_article_text` / `analyze_truthfulness` live in
      BOTH `app.py` and `detector.py` and have drifted. Make `detector.py` the single
      source of truth and have `app.py` import from it (or delete `detector.py` if we
      don't need the CLI). Pick one.
- [ ] **Fix the image error handling.** `analyze_image_with_gemini` in `app.py` uses a
      bare `except` that hides real errors. Return a specific message like the scraper does.
- [ ] **Validate image uploads.** Add `app.config['MAX_CONTENT_LENGTH']` (e.g. 8 MB) and
      reject non-image files before sending to Gemini.
- [ ] *(stretch)* Improve article extraction — target `<article>`/`<p>` tags instead of
      grabbing the whole page (nav/ads/footer) so scores are more accurate.

## Track B — Frontend & UX  (owner: __________)
File: `templates/index.html`
- [ ] **Fix the broken trust gauge.** The marker has a `data-score` attribute but no JS
      moves it — the needle never points at the score. Add a small `<script>` that sets
      the marker's `left:` to the score %.
- [ ] **Add a loading state.** Scraping + Gemini takes several seconds; the page just
      hangs. Show a spinner / "Analyzing…" after the user clicks submit.
- [ ] **Show what was analyzed** (URL vs image) in the results card.
- [ ] **Add an "Analyze another" reset button** after a result appears.

## Track C — Docs, tests & deployment  (owner: __________)
Files: `README.md`, `tests/` (new), `.gitignore`, deploy config
- [ ] **Write a real README** (it currently just says "hi"): what it does, screenshot,
      setup steps, the `GEMINI_API_KEY` requirement, how to run.
- [ ] **Add `.venv/` to `.gitignore`** so the virtualenv isn't committed.
- [ ] **Write unit tests** for `analyze_truthfulness` (score stays 0–100, red-flag words
      lower the score) and the scraper's error paths. Use `pytest`.
- [ ] **Deploy it.** The `Procfile` (`gunicorn app:app`) targets Render/Railway/Heroku.
      Set `GEMINI_API_KEY` as a host env var (NOT the .env file). Verify TextBlob's NLTK
      data loads on the host. Confirm `requirements.txt` installs on the host's Python.

---

## Ground rules
- Branch per track; small PRs.
- Never commit `.env` or real API keys (already gitignored).
- After pulling, re-run `.venv/bin/pip install -r requirements.txt` if deps changed.
