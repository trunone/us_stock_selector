import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io
import os
import sys
import re
import argparse
from bs4 import BeautifulSoup
from textblob import TextBlob

def get_news_sentiment(ticker):
    """Fetches news and calculates average sentiment polarity."""
    try:
        asset = yf.Ticker(ticker)
        news = asset.news
        if not news:
            return 0, 0

        sentiments = []
        for item in news:
            title = item.get('title')
            if not title:
                # Try nested content structure which yfinance sometimes returns
                content = item.get('content', {})
                title = content.get('title')

            if title:
                blob = TextBlob(title)
                sentiments.append(blob.sentiment.polarity)

        if not sentiments:
            return 0, 0

        avg_sentiment = sum(sentiments) / len(sentiments)

        return avg_sentiment, len(sentiments)

    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return 0, 0

def get_industries():
    """Fetches a list of industries from StockAnalysis.com."""
    url = "https://stockanalysis.com/stocks/industry/"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch industries: {response.status_code}")
            return []

        # Extract industries using regex from the embedded script
        # The data is in a structure like: industry_name:"Name",url:"slug"
        matches = re.findall(r'industry_name:"([^"]+)",url:"([^"]+)"', response.text)

        industries = []
        seen_urls = set()

        for name, slug in matches:
            if slug not in seen_urls:
                industries.append({'name': name, 'url': slug})
                seen_urls.add(slug)

        industries.sort(key=lambda x: x['name'])
        return industries

    except Exception as e:
        print(f"Error fetching industries: {e}")
        return []

def get_tickers_by_industry(industry_url):
    """Fetches tickers for a specific industry from StockAnalysis.com."""
    url = f"https://stockanalysis.com/stocks/industry/{industry_url}/"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch tickers for {industry_url}: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        tickers = []

        # Reserved words to exclude if they appear as links
        reserved = {
            'industry', 'sector', 'stocks', 'screener', 'compare',
            'etf', 'ipo', 'news', 'lists', 'analysts', 'about',
            'contact', 'login', 'pro', 'subscribe', 'blog', 'privacy-policy',
            'terms-of-use', 'sitemap', 'faq'
        }

        for link in soup.find_all('a', href=True):
            href = link['href']
            # Ticker links are usually /stocks/ticker/
            if href.startswith('/stocks/') and href.count('/') >= 3:
                parts = href.strip('/').split('/')
                if len(parts) >= 2:
                    slug = parts[1]

                    if slug in reserved:
                        continue

                    text = link.text.strip()

                    # Heuristic: The link text should match the slug (case-insensitive)
                    # or allow for dot/dash difference (e.g. BRK-B vs BRK.B)
                    if (slug.lower() == text.lower() or
                        slug.lower() == text.lower().replace('.', '-')):

                        # Convert dot to dash for yfinance compatibility if needed
                        ticker = text.upper().replace('.', '-')
                        if ticker not in tickers:
                            tickers.append(ticker)

        return tickers

    except Exception as e:
        print(f"Error fetching tickers for {industry_url}: {e}")
        return []

def get_all_tickers():
    """Fetches a comprehensive list of US tickers from NASDAQ Trader."""
    url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
    try:
        df = pd.read_csv(url, sep='|')
        # Filter out test issues and the file creation time footer
        df = df[df['Test Issue'] == 'N']
        if 'Symbol' in df.columns:
            tickers = df['Symbol'].tolist()
            # Clean tickers (remove nan if any, though unlikely with read_csv filtering)
            tickers = [str(t) for t in tickers if isinstance(t, str)]
            return tickers
        else:
            print("Could not find 'Symbol' column in the retrieved data.")
            return []
    except Exception as e:
        print(f"Error fetching all tickers: {e}")
        return []

def calculate_rsi(data, window=14):
    """Calculates the Relative Strength Index (RSI)."""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analyze_batch(tickers):
    """Fetches data and calculates indicators for a batch of assets."""
    if not tickers:
        return []

    try:
        # Download data for the last 2 years in bulk
        # group_by='ticker' ensures we have a hierarchy: Ticker -> Open, High, Low, Close...
        data = yf.download(tickers, period="2y", group_by='ticker', threads=True, progress=False)

        if data.empty:
            return []

        results = []

        # If only one ticker was downloaded, the dataframe structure is flat (Index=Date, Columns=OHLC)
        # We need to handle that case.
        if len(tickers) == 1:
            # Reformat to match the multiindex structure or just process directly
            ticker = tickers[0]
            # Create a mock multiindex or just process
            # But yfinance usually returns flattened for single ticker unless auto_adjust is tricky
            # Let's simplify: loop is safer if we ensure structure
            # However, if we requested multiple, and only 1 valid returned, it might be flat or multi?
            # It's usually safe to assume MultiIndex if len(tickers) > 1 request, but let's check columns
            pass # Logic handled below

        # Get list of tickers actually returned (columns level 0)
        if isinstance(data.columns, pd.MultiIndex):
            downloaded_tickers = data.columns.levels[0].unique()
        else:
            # Single ticker result
            downloaded_tickers = tickers # Should be just one
            # Wrap data to look like multiindex for the loop or process single
            # Easier to process single here
            ticker = tickers[0]
            df = data
            res = process_single_df(df, ticker)
            if res:
                results.append(res)
            return results

        for ticker in downloaded_tickers:
            try:
                df = data[ticker]
                res = process_single_df(df, ticker)
                if res:
                    results.append(res)
            except Exception as e:
                # print(f"Error processing {ticker}: {e}")
                continue

        return results

    except Exception as e:
        print(f"Error analyzing batch: {e}")
        return []

def process_single_df(df, ticker):
    """Helper to process a single asset dataframe."""
    if df.empty:
        return None

    # Check for 'Close' column
    if 'Close' not in df.columns:
        return None

    close = df['Close']

    # Ensure enough data points
    if len(close) < 200:
        return None

    # Calculate indicators
    sma_50 = close.rolling(window=50).mean()
    sma_200 = close.rolling(window=200).mean()
    rsi = calculate_rsi(close)

    last_close = close.iloc[-1]
    last_sma_50 = sma_50.iloc[-1]
    last_sma_200 = sma_200.iloc[-1]
    last_rsi = rsi.iloc[-1]

    # Check for NaN (recent IPOs might have < 200 data points even if history exists?)
    if pd.isna(last_sma_200) or pd.isna(last_rsi):
        return None

    # Strategy Logic
    if (last_close > last_sma_200 and
        last_rsi < 70 and
        last_sma_50 > last_sma_200):

        return {
            'Ticker': ticker,
            'Close': last_close,
            'SMA_50': last_sma_50,
            'SMA_200': last_sma_200,
            'RSI': last_rsi
        }
    return None

def main():
    parser = argparse.ArgumentParser(description="US Asset Analysis Tool")
    parser.add_argument("--all", action="store_true", help="Process all US tickers")
    parser.add_argument("--industry", type=str, help="Process a specific industry (by name or slug)")
    args = parser.parse_args()

    all_tickers = []

    if args.all:
        print("Fetching all US asset tickers...")
        all_tickers = get_all_tickers()
    elif args.industry:
        print("Fetching industries to validate selection...")
        industries = get_industries()
        if not industries:
            print("Failed to fetch industries.")
            return

        target = args.industry.lower()
        selected = None
        for ind in industries:
            if ind['url'] == target or ind['name'].lower() == target:
                selected = ind
                break

        if selected:
            print(f"Fetching tickers for {selected['name']} ({selected['url']})...")
            all_tickers = get_tickers_by_industry(selected['url'])
        else:
            print(f"Industry '{args.industry}' not found.")
            return
    else:
        # Interactive Mode
        print("Select ticker source:")
        print("1. All US Tickers (NASDAQ Trader)")
        print("2. Select by Industry (StockAnalysis.com)")

        choice = input("Enter choice (1 or 2): ").strip()

        if choice == '1':
            print("Fetching all US asset tickers...")
            all_tickers = get_all_tickers()
        elif choice == '2':
            print("Fetching industries...")
            industries = get_industries()
            if not industries:
                print("No industries found.")
                return

            print("\nAvailable Industries:")
            for i, ind in enumerate(industries):
                print(f"{i + 1}. {ind['name']}")

            try:
                ind_choice = int(input("\nEnter industry number: "))
                if 1 <= ind_choice <= len(industries):
                    selected = industries[ind_choice - 1]
                    print(f"Fetching tickers for {selected['name']}...")
                    all_tickers = get_tickers_by_industry(selected['url'])
                else:
                    print("Invalid selection.")
                    return
            except ValueError:
                print("Invalid input.")
                return
        else:
            print("Invalid choice.")
            return

    if not all_tickers:
        print("Failed to get tickers or no tickers found. Exiting.")
        return

    print(f"Found {len(all_tickers)} tickers.")

    # Batch processing
    BATCH_SIZE = 100
    # For demonstration/testing, limit total processed. Remove slice for full run.
    LIMIT = 500
    tickers_to_process = all_tickers[:LIMIT]
    # tickers_to_process = all_tickers # Uncomment for full run

    print(f"Processing {len(tickers_to_process)} tickers in batches of {BATCH_SIZE}...")

    selected_assets = []

    for i in range(0, len(tickers_to_process), BATCH_SIZE):
        batch = tickers_to_process[i:i + BATCH_SIZE]
        print(f"Processing batch {i // BATCH_SIZE + 1} ({len(batch)} tickers)...", flush=True)
        results = analyze_batch(batch)
        selected_assets.extend(results)

    print("\nAnalysis complete.")

    if selected_assets:
        print(f"Found {len(selected_assets)} technical candidates. Analyzing news sentiment...")
        for asset in selected_assets:
            ticker = asset['Ticker']
            sentiment, count = get_news_sentiment(ticker)
            asset['News Sentiment'] = sentiment
            asset['News Count'] = count

    results_df = pd.DataFrame(selected_assets)

    if not results_df.empty:
        print("\nPotential Investment Candidates (Sorted by RSI):")
        # Format the output
        columns_to_show = ['Ticker', 'Close', 'SMA_50', 'SMA_200', 'RSI', 'News Sentiment', 'News Count']
        # Reorder columns if they exist, otherwise fallback to default behavior (though they should exist now)
        cols = [c for c in columns_to_show if c in results_df.columns]
        print(results_df[cols].sort_values(by='RSI').round(2).to_string(index=False))

        # Plot the first candidate
        top_pick = results_df.sort_values(by='RSI').iloc[0]['Ticker']
        print(f"\nGenerating chart for top pick: {top_pick}")

        try:
            # Re-download single for plotting to be safe/simple
            df = yf.download(top_pick, period="2y", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                 try:
                     close = df['Close'][top_pick]
                 except KeyError:
                     close = df['Close']
            else:
                close = df['Close']

            sma_50 = close.rolling(window=50).mean()
            sma_200 = close.rolling(window=200).mean()

            plt.figure(figsize=(12, 8))
            plt.plot(df.index, close, label='Close Price', alpha=0.5)
            plt.plot(df.index, sma_50, label='SMA 50', color='orange')
            plt.plot(df.index, sma_200, label='SMA 200', color='red')
            plt.title(f'{top_pick} Price Analysis')
            plt.xlabel('Date')
            plt.ylabel('Price')
            plt.legend()
            plt.grid(True)

            plt.savefig('top_asset_chart.png')
            print("Chart saved as 'top_asset_chart.png'")
        except Exception as e:
            print(f"Error generating chart: {e}")

    else:
        print("No assets matched the criteria in this subset.")

if __name__ == "__main__":
    main()
