import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import re
from duckduckgo_search import DDGS
from ddgs import DDGS
import json
from datetime import datetime
import os

# Step 1: Fetch and clean website content
def fetch_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
            tag.decompose()
        
        article = soup.find('article') or soup.find('main') or soup.body
        if article:
            text = ' '.join(article.get_text(strip=True).split())
        else:
            text = ' '.join(p.get_text(strip=True) for p in soup.find_all('p'))
        
        # Aggressive cleaning
        text = re.sub(r'\d+ of \d+\|?', '', text)
        text = re.sub(r'Read More.*?(of \d+\|?)?', '', text)
        text = re.sub(r'\(AP Photo[^)]*\)', '', text)
        text = re.sub(r'THIS IS A BREAKING NEWS UPDATE\.?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Smoke raises? at .*?Saturday, Jan\.?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text[:6000]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [403, 401]:
            return "Error: Site blocked automated access (403/401 Forbidden)."
        return f"HTTP Error: {e}"
    except Exception as e:
        return f"Error fetching: {e}"

# Step 2: AI Generation Detection
detector = pipeline("text-classification", model="openai-community/roberta-base-openai-detector")

def is_ai_generated(text):
    result = detector(text[:512])[0]
    label = result['label']
    score = result['score']
    return (label == 'LABEL_1', score)

# Step 3: Stricter Claim Extraction
def extract_claims(text):
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    claims = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 70 or len(sent) > 300:
            continue
        if sent.endswith('?'):
            continue
        if any(phrase in sent.lower() for phrase in ['read more', 'ap photo', 'breaking news', 'photo', 'smoke raises']):
            continue
        words = sent.split()
        if len(words) > 6:
            caps_ratio = sum(1 for w in words if w and w[0].isupper()) / len(words)
            if caps_ratio > 0.65:
                continue
        if re.search(r'\d+|is |was |has |have |are |were |said |says |claimed |according to|reported|announced|stated|confirmed|denied|captured|strike', sent, re.IGNORECASE):
            claims.append(sent)
    return claims[:4]

# Step 4: Fact-Check
def fact_check_claim(claim):
    with DDGS() as ddgs:
        support_results = list(ddgs.text(f'"{claim}" evidence OR confirmed OR true', max_results=3))
        challenge_results = list(ddgs.text(f'"{claim}" debunked OR false OR hoax OR misinformation', max_results=3))
    
    support_links = [r['href'] for r in support_results]
    challenge_links = [r['href'] for r in challenge_results]
    
    total_support = len(support_links)
    total_challenge = len(challenge_links)
    
    if total_support == 0 and total_challenge == 0:
        verdict = "No evidence found"
    elif total_challenge >= 2 and total_support <= 1:
        verdict = "Likely False/Misleading"
    elif total_support >= 2 and total_challenge <= 1:
        verdict = "Likely True"
    elif total_challenge > total_support:
        verdict = "More evidence against than for"
    elif total_support > total_challenge:
        verdict = "More evidence supporting than against"
    else:
        verdict = "Mixed / Inconclusive evidence"
    
    return {
        "claim": claim,
        "supporting": support_links,
        "challenging": challenge_links,
        "verdict": verdict
    }

# Main Function with JSON Export
def detect_misinfo(url):
    print(f"Analyzing: {url}\n")
    content = fetch_content(url)
    if "Error" in content:
        print(content)
        return None
    
    print(f"Extracted Text Snippet: {content[:300]}...\n")
    
    ai_likely, ai_score = is_ai_generated(content)
    print(f"AI-Generated Probability: {ai_score:.2f} ({'Likely AI' if ai_likely else 'Likely Human'})\n")
    
    claims = extract_claims(content)
    print(f"Extracted Claims ({len(claims)}):\n" + "\n".join(claims) + "\n")
    
    report_data = {
        "url": url,
        "analysis_date": datetime.now().isoformat(),
        "ai_detection": {
            "probability_ai": ai_score,
            "verdict": "Likely AI" if ai_likely else "Likely Human"
        },
        "claims": [],
        "overall_verdict": "",
        "methodology": "Content fetched via scraping; AI detection via Hugging Face RoBERTa model (~80-90% accuracy); Strict claim filtering; Balanced DuckDuckGo searches. Human verification recommended."
    }
    
    has_false = False
    for claim in claims:
        check = fact_check_claim(claim)
        report_data["claims"].append(check)
        if "False" in check['verdict'] or "against" in check['verdict']:
            has_false = True
        
        print(f"Claim: {check['claim']}")
        print(f"Verdict: {check['verdict']}")
        print(f"Supporting: {check['supporting']}")
        print(f"Challenging: {check['challenging']}\n")
    
    if ai_likely and has_false:
        overall = "Potential AI-Generated Misinformation Detected"
    elif has_false:
        overall = "Potential Misinformation (Not necessarily AI-generated)"
    elif ai_likely:
        overall = "Likely AI-Generated (But claims appear supported)"
    else:
        overall = "No strong indicators of fake/misinformation"
    
    report_data["overall_verdict"] = overall
    
    print("=== IFCN-Aligned Report ===")
    print(f"Overall: {overall}")
    print("Sources: Listed in JSON report below.")
    print("Human verification strongly recommended for breaking news.")
    
    # Save JSON report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"misinfo_report_{timestamp}.json"
    filepath = os.path.join(os.path.expanduser("~/Downloads"), filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=4, ensure_ascii=False)
    
    print(f"\nFull report saved as JSON: {filepath}")
    
    return report_data

if __name__ == "__main__":
    url = input("Enter website URL: ").strip()
    if url:
        detect_misinfo(url)
