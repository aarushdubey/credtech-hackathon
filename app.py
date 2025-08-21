import os
import requests
import time
from flask import Flask, jsonify, render_template
import yfinance as yf
from datetime import datetime, timedelta

# --- CONFIGURATION ---
NEWS_API_KEY = os.environ.get("c7d5ac09f57b4508ab5f83dbb1b00076")

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

    current_price = info.get('regularMarketPrice')
    previous_close = info.get('previousClose')
    debt_to_equity = info.get('debtToEquity')
    news_sentiment, headlines = get_news_sentiment(company_name)
    base_score = 50
    explanation = {}

    if current_price and previous_close:
        if current_price >= previous_close:
            base_score += 5
            explanation['price_impact'] = f"Positive: Stock price ({current_price}) is at or above its previous close."
        else:
            base_score -= 5
            explanation['price_impact'] = f"Negative: Stock price ({current_price}) is below its previous close."
    else: explanation['price_impact'] = "Neutral: Could not retrieve real-time price data."

    base_score += (news_sentiment * 10)
    if news_sentiment > 0: explanation['news_impact'] = f"Positive: Recent news sentiment is favorable (Sentiment: {news_sentiment})."
    elif news_sentiment < 0: explanation['news_impact'] = f"Negative: Recent news sentiment is cautious (Sentiment: {news_sentiment})."
    else: explanation['news_impact'] = "Neutral: Recent news sentiment is balanced."

    if debt_to_equity:
        if debt_to_equity > 1.5:
            base_score -= 10
            explanation['financial_impact'] = f"High Risk: Debt-to-Equity ratio is high ({round(debt_to_equity, 2)})."
        else:
            base_score += 5
            explanation['financial_impact'] = f"Healthy: Debt-to-Equity ratio is good ({round(debt_to_equity, 2)})."

    if True: # is_recession_looming
        base_score -= 5
        explanation['macro_impact'] = "Negative: Score adjusted down for negative macroeconomic outlook."

    peer_scores = []
    if get_peers and ticker in PEER_GROUPS:
        for peer_ticker in PEER_GROUPS[ticker]:
            peer_score_data = calculate_single_ticker_score(peer_ticker)
            peer_scores.append({
                'ticker': peer_ticker, 'name': peer_score_data.get('company_name', peer_ticker),
                'score': peer_score_data.get('credit_score')
            })

    return {
        'company_name': company_name, 'ticker': ticker,
        'credit_score': max(0, min(100, base_score)), 'explanation': explanation,
        'recent_headlines': headlines, 'peer_scores': peer_scores
    }

def get_news_sentiment(company_name):
    url = (f"https://newsapi.org/v2/everything?q={company_name}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&language=en")
    try:
        response = requests.get(url); response.raise_for_status()
        articles = response.json().get('articles', [])
        sentiment_score = 0; latest_headlines = []
        for article in articles[:5]:
            headline = article['title'].lower()
            # --- UPDATE: INCLUDE THE URL WITH THE TITLE ---
            latest_headlines.append({'title': article['title'], 'url': article['url']})
            if any(word in headline for word in POSITIVE_KEYWORDS): sentiment_score += 1
            if any(word in headline for word in NEGATIVE_KEYWORDS): sentiment_score -= 1
        return sentiment_score, latest_headlines
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}"); return 0, []

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