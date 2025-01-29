import requests

# Example of a GET request using requests library
response = requests.get('https://api.github.com/users/dnair27')

# Print the response content
print(response.json())

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

        return render_template('result.html', stock_symbol=stock_symbol, sentiment_score=sentiment_score,
                               sentiment=sentiment, recommendation=recommendation)
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)


def fetch_twitter_sentiment(stock_symbol):
    # You'll need to set up Twitter API credentials
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    api = tweepy.API(auth)

    tweets = []
    try:
        # Search for tweets containing the stock symbol or company name
        search_query = f"${stock_symbol} OR {stock_symbol}"
        tweets = api.search_tweets(q=search_query, lang="en", count=100)
    except Exception as e:
        print(f"Error fetching tweets: {e}")
        return []

    return tweets


def analyze_twitter_sentiment(tweets):
    if not tweets:
        return 0

    total_sentiment = 0
    valid_tweets = 0

    for tweet in tweets:
        text = tweet.text
        # Clean the tweet text
        text = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", text).split())

        if not text:
            continue

        analysis = TextBlob(text)
        total_sentiment += analysis.sentiment.polarity
        valid_tweets += 1

    if valid_tweets == 0:
        return 0

    return total_sentiment / valid_tweets


# Modify the index route to include Twitter sentiment
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol'].upper()
        stock_data = fetch_stock_data(stock_symbol)

        if "Error Message" in stock_data:
            return f"Invalid stock symbol: {stock_symbol}"

        # Get both news and Twitter sentiment
        articles = fetch_news(stock_symbol)
        tweets = fetch_twitter_sentiment(stock_symbol)

        if not articles and not tweets:
            return f"No news or tweets found for the stock: {stock_symbol}"

        # Calculate combined sentiment score
        news_sentiment = analyze_sentiment(articles)
        twitter_sentiment = analyze_twitter_sentiment(tweets)

        # Weight the sentiments (adjust weights as needed)
        combined_sentiment = (news_sentiment * 0.6) + (twitter_sentiment * 0.4)
        sentiment_score = round(combined_sentiment, 2)

        # Rest of your existing sentiment classification logic
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

        return render_template('result.html',
                               stock_symbol=stock_symbol,
                               sentiment_score=sentiment_score,
                               sentiment=sentiment,
                               recommendation=recommendation)
    return render_template('index.html')


def analyze_fundamentals(stock_symbol):
    try:
        # Get company overview data from Alpha Vantage
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={stock_symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if not data or "Error Message" in data:
            return 0

        # Initialize score components
        profitability_score = 0
        growth_score = 0
        valuation_score = 0

        # Analyze profitability metrics
        if float(data.get('ProfitMargin', 0)) > 0.1:
            profitability_score += 0.2
        if float(data.get('ReturnOnEquityTTM', 0)) > 0.15:
            profitability_score += 0.2

        # Analyze growth metrics
        if float(data.get('QuarterlyEarningsGrowthYOY', 0)) > 0:
            growth_score += 0.2
        if float(data.get('QuarterlyRevenueGrowthYOY', 0)) > 0:
            growth_score += 0.2

        # Analyze valuation metrics
        pe_ratio = float(data.get('PERatio', 100))
        if 0 < pe_ratio < 25:  # Reasonable P/E ratio
            valuation_score += 0.2

        # Calculate final fundamental score (-1 to 1 scale)
        fundamental_score = (profitability_score + growth_score + valuation_score) - 0.5
        return fundamental_score

    except Exception as e:
        print(f"Error analyzing fundamentals: {e}")
        return 0


# Modify the index route to include fundamentals
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol'].upper()
        stock_data = fetch_stock_data(stock_symbol)

        if "Error Message" in stock_data:
            return f"Invalid stock symbol: {stock_symbol}"

        # Get news, Twitter sentiment, and fundamentals
        articles = fetch_news(stock_symbol)
        tweets = fetch_twitter_sentiment(stock_symbol)
        fundamental_score = analyze_fundamentals(stock_symbol)

        if not articles and not tweets:
            return f"No news or tweets found for the stock: {stock_symbol}"

        # Calculate combined sentiment score
        news_sentiment = analyze_sentiment(articles)
        twitter_sentiment = analyze_twitter_sentiment(tweets)

        # Weight the sentiments (adjust weights as needed)
        combined_sentiment = (news_sentiment * 0.4) + (twitter_sentiment * 0.3) + (fundamental_score * 0.3)
        sentiment_score = round(combined_sentiment, 2)

        # Rest of your existing sentiment classification logic
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

        return render_template('result.html',
                               stock_symbol=stock_symbol,
                               sentiment_score=sentiment_score,
                               sentiment=sentiment,
                               recommendation=recommendation)
    return render_template('index.html')

    # Get technical analysis indicators
    def get_technical_indicators(symbol):
        try:
            # Get historical data for technical analysis
            url = f"https://www.alphavantage.co/query?function=RSI&symbol={symbol}&interval=daily&time_period=14&series_type=close&apikey={API_KEY}"
            r = requests.get(url)
            data = r.json()

            if "Technical Analysis: RSI" not in data:
                return 0

            # Get latest RSI value
            latest_date = list(data["Technical Analysis: RSI"].keys())[0]
            rsi = float(data["Technical Analysis: RSI"][latest_date]["RSI"])

            # Get MACD
            url = f"https://www.alphavantage.co/query?function=MACD&symbol={symbol}&interval=daily&series_type=close&apikey={API_KEY}"
            r = requests.get(url)
            data = r.json()

            if "Technical Analysis: MACD" not in data:
                return 0

            latest_date = list(data["Technical Analysis: MACD"].keys())[0]
            macd = float(data["Technical Analysis: MACD"][latest_date]["MACD"])
            macd_signal = float(data["Technical Analysis: MACD"][latest_date]["MACD_Signal"])

            # Calculate technical score
            tech_score = 0

            # RSI analysis (0-100 scale)
            if rsi < 30:  # Oversold
                tech_score += 0.3
            elif rsi > 70:  # Overbought
                tech_score -= 0.3

            # MACD analysis
            if macd > macd_signal:  # Bullish
                tech_score += 0.2
            else:  # Bearish
                tech_score -= 0.2

            return tech_score

        except Exception as e:
            print(f"Error getting technical indicators: {e}")
            return 0

    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol'].upper()
        stock_data = fetch_stock_data(stock_symbol)

        if "Error Message" in stock_data:
            return f"Invalid stock symbol: {stock_symbol}"

        # Get news, Twitter sentiment, fundamentals and technical analysis
        articles = fetch_news(stock_symbol)
        tweets = fetch_twitter_sentiment(stock_symbol)
        fundamental_score = analyze_fundamentals(stock_symbol)
        technical_score = get_technical_indicators(stock_symbol)

        if not articles and not tweets:
            return f"No news or tweets found for the stock: {stock_symbol}"

        # Calculate combined sentiment score
        news_sentiment = analyze_sentiment(articles)
        twitter_sentiment = analyze_twitter_sentiment(tweets)

        # Weight the sentiments (adjust weights as needed)
        combined_sentiment = (news_sentiment * 0.3) + (twitter_sentiment * 0.2) + \
                             (fundamental_score * 0.25) + (technical_score * 0.25)
        sentiment_score = round(combined_sentiment, 2)
        # Get macroeconomic indicators
        try:
            # Get GDP growth rate
            gdp_response = requests.get(
                f"https://www.alphavantage.co/query?function=REAL_GDP&interval=quarterly&apikey={API_KEY}")
            gdp_data = gdp_response.json()
            latest_gdp = float(gdp_data["data"][0]["value"])
            prev_gdp = float(gdp_data["data"][1]["value"])
            gdp_growth = (latest_gdp - prev_gdp) / prev_gdp

            # Get inflation rate
            cpi_response = requests.get(
                f"https://www.alphavantage.co/query?function=CPI&interval=monthly&apikey={API_KEY}")
            cpi_data = cpi_response.json()
            latest_cpi = float(cpi_data["data"][0]["value"])
            prev_cpi = float(cpi_data["data"][1]["value"])
            inflation = (latest_cpi - prev_cpi) / prev_cpi

            # Get unemployment rate
            unemployment_response = requests.get(
                f"https://www.alphavantage.co/query?function=UNEMPLOYMENT&apikey={API_KEY}")
            unemployment_data = unemployment_response.json()
            unemployment = float(unemployment_data["data"][0]["value"])

            # Calculate macro score
            macro_score = 0

            # GDP growth analysis
            if gdp_growth > 0.02:  # Strong growth
                macro_score += 0.2
            elif gdp_growth < 0:  # Negative growth
                macro_score -= 0.2

            # Inflation analysis
            if inflation > 0.05:  # High inflation
                macro_score -= 0.15
            elif inflation < 0.02:  # Low inflation
                macro_score += 0.15

            # Unemployment analysis
            if unemployment > 6:  # High unemployment
                macro_score -= 0.15
            elif unemployment < 4:  # Low unemployment
                macro_score += 0.15

        except Exception as e:
            print(f"Error getting macroeconomic indicators: {e}")
            macro_score = 0

        # Recalculate combined sentiment with macro factors
        combined_sentiment = (news_sentiment * 0.25) + (twitter_sentiment * 0.15) + \
                             (fundamental_score * 0.2) + (technical_score * 0.2) + \
                             (macro_score * 0.2)
        sentiment_score = round(combined_sentiment, 2)
        # Return the sentiment score and analysis details
        return render_template('result.html',
            stock_symbol=stock_symbol,
            sentiment_score=sentiment_score
        )
