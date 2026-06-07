import requests
from bs4 import BeautifulSoup
from textblob import TextBlob

def extract_article_text(url):
    """Fetches the webpage and extracts the main text content."""
    try:
        # Headers mimic a real browser so websites don't block the request
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements so we don't analyze raw website code
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get the text and clean up whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return clean_text
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return None

def analyze_truthfulness(text):
    """Analyzes text subjectivity, sentiment, and red-flag words."""
    blob = TextBlob(text)
    
    # Subjectivity ranges from 0.0 (highly factual) to 1.0 (highly opinionated)
    subjectivity = blob.sentiment.subjectivity
    
    # Calculate a base score from the text's objectivity
    truth_score = (1 - subjectivity) * 100
    
    # Look for sensationalized "clickbait" words
    red_flags = ["shocking", "unbelievable", "secret", "miracle", "conspiracy", "proved them wrong", "gullible"]
    flag_count = 0
    
    words = text.lower().split()
    for flag in red_flags:
        if flag in words:
            flag_count += 1
            truth_score -= 8  # Penalize the score for each red flag found
            
    # Keep the score bound between 0 and 100
    truth_score = max(0, min(100, truth_score))
    
    return truth_score, subjectivity, flag_count

def main():
    print("=== AI URL Credibility Analyzer ===")
    user_url = input("Please enter the URL to test: ").strip()
    
    print("\nFetching and scraping the webpage...")
    article_text = extract_article_text(user_url)
    
    if not article_text or len(article_text) < 100:
        print("Could not retrieve enough text from that link. Try a different article.")
        return
        
    print("Analyzing text structure and tone...")
    score, sub_val, flags = analyze_truthfulness(article_text)
    
    print("\n--- RESULTS ---")
    print(f"Credibility/Truth Score: {score:.1f}%")
    print(f"Subjectivity Level: {sub_val * 100:.1f}% (High subjectivity means more opinion, less factual reporting)")
    print(f"Sensationalist Red-Flag Words Found: {flags}")
    
    if score > 70:
        print("Verdict: Likely Reliable. The text relies mostly on objective language.")
    elif score > 40:
        print("Verdict: Uncertain. Mix of facts and strong opinions/biases.")
    else:
        print("Verdict: High Risk. Highly opinionated language or loaded keywords detected.")

if __name__ == "__main__":
    main()