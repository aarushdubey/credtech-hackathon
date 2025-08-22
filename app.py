from dotenv import load_dotenv
load_dotenv()
import os
import requests
import time
from flask import Flask, jsonify, render_template
import yfinance as yf
from datetime import datetime, timedelta

# --- CONFIGURATION ---
GUARDIAN_API_KEY = os.environ.get("GUARDIAN_API_KEY")

TOP_COMPANIES = [
    {'name': 'Apple', 'ticker': 'AAPL'}, {'name': 'Microsoft', 'ticker': 'MSFT'},
    {'name': 'Google', 'ticker': 'GOOGL'}, {'name': 'Amazon', 'ticker': 'AMZN'},
    {'name': 'NVIDIA', 'ticker': 'NVDA'}, {'name': 'Tesla', 'ticker': 'TSLA'},
    {'name': 'Meta', 'ticker': 'META'}, {'name': 'Berkshire Hathaway', 'ticker': 'BRK-B'},
    {'name': 'JPMorgan Chase', 'ticker': 'JPM'}, {'name': 'Exxon Mobil', 'ticker': 'XOM'},
    {'name': 'UnitedHealth', 'ticker': 'UNH'}, {'name': 'Visa', 'ticker': 'V'},
    {'name': 'Johnson & Johnson', 'ticker': 'JNJ'}, {'name': 'Walmart', 'ticker': 'WMT'},
    {'name': 'Procter & Gamble', 'ticker': 'PG'}, {'name': 'Mastercard', 'ticker': 'MA'},
    {'name': 'Home Depot', 'ticker': 'HD'}, {'name': 'Chevron', 'ticker': 'CVX'},
    {'name': 'Pfizer', 'ticker': 'PFE'}, {'name': 'Coca-Cola', 'ticker': 'KO'}
]

app = Flask(__name__)

POSITIVE_KEYWORDS = [
    'profit', 'growth', 'earnings beat', 'upgrade', 'launches', 'successful', 'expansion',
    'record high', 'breakthrough', 'positive outlook', 'strong demand', 'innovation'
]
NEGATIVE_KEYWORDS = [
    'loss', 'downgrade', 'investigation', 'lawsuit', 'recall', 'declines', 'slump',
    'misses estimates', 'fined', 'restructuring', 'layoffs', 'concerns'
]

PEER_GROUPS = {
    'AAPL': ['MSFT', 'GOOGL', 'QCOM'], 'TSLA': ['F', 'GM', 'RIVN'],
    'GOOGL': ['AAPL', 'MSFT', 'META'], 'MSFT': ['AAPL', 'GOOGL', 'AMZN']
}

def calculate_single_ticker_score(ticker, get_peers=False):
    company = yf.Ticker(ticker)
    info = company.info
    company_name = info.get('longName')
    if not company_name: return {"error": f"Invalid ticker symbol: {ticker}"}

    # --- 1. DEFINE WEIGHTS for a more robust model ---
    WEIGHTS = {
        'financials': 0.40, # 40%
        'news': 0.35,       # 35%
        'price': 0.20,      # 20%
        'macro': 0.05       # 5%
    }

    # --- 2. GATHER ALL DATA POINTS ---
    # Price Data
    current_price = info.get('regularMarketPrice')
    previous_close = info.get('previousClose')
    # Financial Ratios
    debt_to_equity = info.get('debtToEquity')
    profit_margin = info.get('profitMargins')
    current_ratio = info.get('currentRatio')
    # Unstructured Data
    news_sentiment, headlines = get_news_sentiment(company_name)
    
    explanation = {}
    
    # --- 3. CALCULATE SUB-SCORES (0-100) FOR EACH CATEGORY ---
    
    # Price Sub-Score
    price_sub_score = 50 # Start neutral
    if current_price and previous_close and previous_close > 0:
        percent_change = ((current_price - previous_close) / previous_close) * 100
        # Scale the impact: a 2% change equals a 10 point swing. Cap at +/- 40 points.
        score_adjustment = max(-40, min(40, percent_change * 5))
        price_sub_score += score_adjustment
        explanation['price_impact'] = f"Price changed by {round(percent_change, 2)}%, adjusting score by {round(score_adjustment)} pts."
    else:
        explanation['price_impact'] = "Neutral: Real-time price data unavailable."

    # News Sub-Score
    news_sub_score = 50 + (news_sentiment * 10) # Each sentiment point is worth 10 score points
    explanation['news_impact'] = f"News sentiment score is {news_sentiment}, resulting in a sub-score of {news_sub_score}."

    # Financials Sub-Score
    financials_sub_score = 0
    factors_count = 0
    if debt_to_equity is not None:
        # Lower D/E is better. Score is 100 if D/E is 0, and 0 if D/E is 200+.
        financials_sub_score += max(0, 100 - (debt_to_equity / 2))
        factors_count += 1
    if profit_margin is not None:
        # Higher margin is better. A 10% margin gives 50 points. A 20%+ margin gives 100.
        financials_sub_score += min(100, (profit_margin * 500))
        factors_count += 1
    if current_ratio is not None:
        # Higher ratio is better. A ratio of 2.0 gives 100 points.
        financials_sub_score += min(100, current_ratio * 50)
        factors_count += 1
    
    if factors_count > 0:
        financials_sub_score /= factors_count # Average the scores from available factors
        explanation['financial_impact'] = f"Financial health sub-score is {round(financials_sub_score)} based on {factors_count} key ratios."
    else:
        financials_sub_score = 50 # Default to neutral if no data
        explanation['financial_impact'] = "Neutral: Financial ratios unavailable."

    # Macro Sub-Score
    macro_sub_score = 20 # A low score reflecting poor outlook
    explanation['macro_impact'] = f"Macroeconomic outlook is cautious, setting a base score of {macro_sub_score}."

    # --- 4. CALCULATE FINAL WEIGHTED SCORE ---
    final_score = (
        financials_sub_score * WEIGHTS['financials'] +
        news_sub_score * WEIGHTS['news'] +
        price_sub_score * WEIGHTS['price'] +
        macro_sub_score * WEIGHTS['macro']
    )
    
    # --- Peer Comparison Logic (remains the same) ---
    peer_scores = []
    if get_peers and ticker in PEER_GROUPS:
        for peer_ticker in PEER_GROUPS[ticker]:
            peer_score_data = calculate_single_ticker_score(peer_ticker, get_peers=False)
            peer_scores.append({
                'ticker': peer_ticker, 'name': peer_score_data.get('company_name', peer_ticker),
                'score': peer_score_data.get('credit_score')
            })

    return {
        'company_name': company_name, 'ticker': ticker,
        'credit_score': round(final_score),
        'explanation': explanation,
        'recent_headlines': headlines,
        'peer_scores': peer_scores
    }

def get_news_sentiment(company_name):
    """Fetches news from The Guardian API and performs sentiment analysis."""
    if not GUARDIAN_API_KEY:
        return 0, [{'title': 'Guardian API Key is not configured.', 'url': '#'}]

    url = (f"https://content.guardianapis.com/search?"
           f"q={company_name}&"
           f"api-key={GUARDIAN_API_KEY}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get('response', {}).get('results', [])
        sentiment_score = 0
        latest_headlines = []
        for article in articles[:10]: # Get up to 10 articles
            headline = article.get('webTitle', '').lower()
            latest_headlines.append({
                'title': article.get('webTitle', 'No Title'),
                'url': article.get('webUrl', '#')
            })
            if any(word in headline for word in POSITIVE_KEYWORDS): sentiment_score += 1
            if any(word in headline for word in NEGATIVE_KEYWORDS): sentiment_score -= 1
        return sentiment_score, latest_headlines
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news from The Guardian: {e}")
        return 0, [{'title': f'Guardian API Error: {e}', 'url': '#'}]

@app.route('/')
def home():
    return render_template('index.html', recommendations=TOP_COMPANIES)

@app.route('/score/<string:ticker>')
def get_score(ticker):
    score_data = calculate_single_ticker_score(ticker, get_peers=True)
    if "error" in score_data: return jsonify(score_data), 404
    return jsonify(score_data)

# --- UPDATE: ENDPOINT NOW ACCEPTS A PERIOD ---
@app.route('/history/<string:ticker>/<string:period>')
def get_history(ticker, period):
    try:
        period_map = {'1m': '1mo', '3m': '3mo', '6m': '6mo', '1y': '1y'}
        yf_period = period_map.get(period, '1mo')
        company = yf.Ticker(ticker)
        hist = company.history(period=yf_period)
        hist.index = hist.index.strftime('%Y-%m-%d')
        return jsonify(hist['Close'].to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)