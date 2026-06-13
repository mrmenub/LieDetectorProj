import os
from dotenv import load_dotenv
from flask import Flask, render_template, request

# Load environment variables from a local .env file (e.g. GEMINI_API_KEY).
# override=True so the .env value wins over any stale/invalid var already in the shell.
load_dotenv(override=True)
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from google import genai
from google.genai import types

app = Flask(__name__)

# --- CENTRAL CONFIGURATION ---
GEMINI_MODEL = "gemini-2.5-flash"
print(f"\n[BOOT CHECK] System is actively running model: {GEMINI_MODEL}\n")

# Pull key from system environment variables securely
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("[WARN] GEMINI_API_KEY is not set. Add it to a .env file or your environment "
          "(see .env.example). Gemini verdicts and image scans will fail until you do.\n")
client = genai.Client(api_key=GEMINI_API_KEY)

def extract_article_text(url):
    """Fetch a page and return (text, error). On success error is None;
    on failure text is None and error explains why (so the UI can be specific)."""
    # Be forgiving if the user pastes "example.com" without a scheme.
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # A fuller, browser-like header set so fewer sites reject us outright.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Upgrade-Insecure-Requests': '1',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
    except requests.exceptions.Timeout:
        return None, "The site took too long to respond (timed out). Try a different page."
    except requests.exceptions.RequestException as e:
        return None, f"Couldn't reach that URL ({type(e).__name__}). Check the link and try again."

    if response.status_code != 200:
        return None, (f"The site returned HTTP {response.status_code} "
                      f"({'blocking scrapers' if response.status_code in (401, 403, 429) else 'not reachable'}). "
                      "Many news sites block automated tools — try a different article.")

    soup = BeautifulSoup(response.text, 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()

    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return '\n'.join(chunk for chunk in chunks if chunk), None

def analyze_truthfulness(text):
    blob = TextBlob(text)
    subjectivity = blob.sentiment.subjectivity
    truth_score = (1 - subjectivity) * 100
    
    red_flags = ["shocking", "unbelievable", "secret", "miracle", "conspiracy", "proved them wrong", "gullible"]
    flag_count = 0
    words = text.lower().split()
    for flag in red_flags:
        if flag in words:
            flag_count += 1
            truth_score -= 8
            
    truth_score = max(0, min(100, truth_score))
    return f"{truth_score:.1f}", f"{subjectivity * 100:.1f}", flag_count

def get_gemini_verdict(article_text, score):
    try:
        prompt = f"""
        You are an expert AI fact-checker built into a credibility dashboard application. 
        Analyze this article content and provide a concise, witty, 2-to-3 sentence verdict on its reliability.
        The algorithm gave it a rule-based credibility score of {score}%.
        
        Keep your tone objective but engaging, acting like a direct peer. Do not include introductory filler.
        
        Article snippet:
        {article_text[:2500]}
        """
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"AI evaluation offline. Local rules score: {score}%."

def analyze_image_with_gemini(image_file):
    try:
        # Reset byte stream pointer to read data safely
        image_file.stream.seek(0)
        image_bytes = image_file.stream.read()
        mime_type = image_file.mimetype or "image/jpeg"
        
        prompt = """
        Analyze this image, which could be a news screenshot, a tweet, a headline, or a meme.
        Format your response EXACTLY like this:
        SCORE: [number]%
        VERDICT: [2-to-3 sentence verdict]
        """
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
                prompt,
            ],
        )
        res_text = response.text.strip()
        
        score = "50.0"
        verdict = res_text
        if "SCORE:" in res_text and "VERDICT:" in res_text:
            parts = res_text.split("VERDICT:", 1)
            score = parts[0].replace("SCORE:", "").replace("%", "").strip()
            verdict = parts[1].strip()
            
        return score, "N/A (Image Scan)", "N/A (Image Scan)", verdict
    except Exception as e:
        return None, None, None, f"Failed to analyze image: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def home():
    score, subjectivity, flags, verdict = None, None, None, None
    error_msg = None  
    
    show_analyzer = request.args.get('start') == 'true' or request.method == 'POST'
    
    if request.method == 'POST':
        if 'image_file' in request.files and request.files['image_file'].filename != '':
            file = request.files['image_file']
            score, subjectivity, flags, verdict = analyze_image_with_gemini(file)
            if not score:
                error_msg = verdict
                verdict = None
        else:
            user_url = request.form.get('url', '').strip()
            if user_url:
                article_text, scrape_error = extract_article_text(user_url)
                if scrape_error:
                    error_msg = scrape_error
                elif len(article_text) >= 100:
                    score, subjectivity, flags = analyze_truthfulness(article_text)
                    verdict = get_gemini_verdict(article_text, score)
                else:
                    error_msg = "The website didn't have enough readable text. Try a different page."
            else:
                error_msg = "Please provide a valid article link or upload an image file."

    return render_template('index.html', score=score, subjectivity=subjectivity, flags=flags, verdict=verdict, error=error_msg, show_analyzer=show_analyzer)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)