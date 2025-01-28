import requests
from flask import Flask, render_template, request
from textblob import TextBlob

# API keys
STOCK_API_KEY = "T9SG6FW8FRZYW0TT"
NEWS_API_KEY = "a7ef57de54a444188822162a8b2240e0"

app = Flask(__name__)

def fetch_stock_data(stock_symbol):
    """Fetch stock data from a stock API."""
    url = f"https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": stock_symbol,
        "interval": "60min",
        "apikey": STOCK_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data

def fetch_news(stock_symbol):
    """Fetch recent news articles for the stock."""
    url = f"https://newsapi.org/v2/everything"
    params = {
        "q": stock_symbol,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY
    }
    response = requests.get(url, params=params)
    articles = response.json().get("articles", [])

    sanitized_articles = [
        article for article in articles
        if isinstance(article, dict) and ("title" in article or "description" in article)
    ]
    return sanitized_articles

def analyze_sentiment(articles):
    total_sentiment = 0
    valid_articles = 0

    for article in articles:
        title = article.get("title", "") or ""
        description = article.get("description", "") or ""
        text = f"{title}. {description}".strip()

        if not text:
            continue

        analysis = TextBlob(text)
        total_sentiment += analysis.sentiment.polarity
        valid_articles += 1

    if valid_articles == 0:
        return 0

    return total_sentiment / valid_articles

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol'].upper()
        stock_data = fetch_stock_data(stock_symbol)

        if "Error Message" in stock_data:
            return f"Invalid stock symbol: {stock_symbol}"

        articles = fetch_news(stock_symbol)
        if not articles:
            return f"No news found for the stock: {stock_symbol}"

        sentiment_score = analyze_sentiment(articles)
        sentiment_score = round(sentiment_score, 2)

        # Adjusted thresholds for recommendation
        if sentiment_score > 0.3:
            sentiment = "Positive"
            recommendation = "Strong buy"
        elif sentiment_score > 0.1:
            sentiment = "Positive"
            recommendation = "Moderate Buy"
        elif sentiment_score < -0.3:
            sentiment = "Negative"
            recommendation = "Strong Caution"
        elif sentiment_score < -0.1:
            sentiment = "Negative"
            recommendation = "Moderate Caution"
        else:
            sentiment = "Neutral"
            recommendation = "Hold"

        return render_template('result.html', stock_symbol=stock_symbol, sentiment_score=sentiment_score, sentiment=sentiment, recommendation=recommendation)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)