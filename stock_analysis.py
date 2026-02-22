import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io
import os

def get_sp500_tickers():
    """Scrapes S&P 500 tickers from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Use pandas to read tables from the HTML content
        tables = pd.read_html(io.StringIO(response.text))

        # The first table is usually the S&P 500 components
        # Verify by checking columns
        df = tables[0]
        if 'Symbol' in df.columns:
            tickers = df['Symbol'].tolist()
            # Replace dots with hyphens for yfinance (e.g. BRK.B -> BRK-B)
            tickers = [ticker.replace('.', '-') for ticker in tickers]
            return tickers
        else:
            print("Could not find the expected table structure.")
            return []

    except Exception as e:
        print(f"Error scraping tickers: {e}")
        return []

def calculate_rsi(data, window=14):
    """Calculates the Relative Strength Index (RSI)."""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analyze_stock(ticker):
    """Fetches data and calculates indicators for a single stock."""
    try:
        # Download data for the last 2 years
        # yfinance download with progress=False to reduce clutter
        df = yf.download(ticker, period="2y", progress=False)

        if df.empty:
            return None

        # Handle MultiIndex columns if present (yfinance update)
        if isinstance(df.columns, pd.MultiIndex):
             # Depending on yfinance version, columns might be (Price, Ticker)
             # We want to flatten or access 'Close' properly
             try:
                 close = df['Close'][ticker]
             except KeyError:
                 close = df['Close'] # Fallback
        else:
            close = df['Close']

        # Ensure close is a Series
        if isinstance(close, pd.DataFrame):
             close = close.iloc[:, 0]

        # Calculate Moving Averages
        sma_50 = close.rolling(window=50).mean()
        sma_200 = close.rolling(window=200).mean()

        # Calculate RSI
        rsi = calculate_rsi(close)

        # Create a new DataFrame with the calculated values
        result_df = pd.DataFrame(index=df.index)
        result_df['Close'] = close
        result_df['SMA_50'] = sma_50
        result_df['SMA_200'] = sma_200
        result_df['RSI'] = rsi

        return result_df
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None

def main():
    print("Fetching S&P 500 tickers...")
    all_tickers = get_sp500_tickers()

    if not all_tickers:
        print("Failed to get tickers. Exiting.")
        return

    print(f"Found {len(all_tickers)} tickers.")

    # For testing purposes, limit to first 20 tickers
    test_tickers = all_tickers[:20]
    print(f"Analyzing {len(test_tickers)} tickers for demonstration...")

    selected_stocks = []

    for ticker in test_tickers:
        print(f"Processing {ticker}...", end=" ", flush=True)
        df = analyze_stock(ticker)

        if df is not None and len(df) > 200:
            last_row = df.iloc[-1]

            # Simple Selection Logic:
            # 1. Price above SMA 200 (Long term trend is up)
            # 2. RSI < 70 (Not extremely overbought)
            # 3. SMA 50 > SMA 200 (Golden Cross condition active)

            if (last_row['Close'] > last_row['SMA_200'] and
                last_row['RSI'] < 70 and
                last_row['SMA_50'] > last_row['SMA_200']):

                selected_stocks.append({
                    'Ticker': ticker,
                    'Close': last_row['Close'],
                    'SMA_50': last_row['SMA_50'],
                    'SMA_200': last_row['SMA_200'],
                    'RSI': last_row['RSI']
                })
                print("Selected!")
            else:
                print("Skipped.")
        else:
            print("Insufficient data.")

    print("\nAnalysis complete.")

    results_df = pd.DataFrame(selected_stocks)

    if not results_df.empty:
        print("\nPotential Investment Candidates (Sorted by RSI):")
        # Format the output
        print(results_df.sort_values(by='RSI').round(2).to_string(index=False))

        # Plot the first candidate
        top_pick = results_df.sort_values(by='RSI').iloc[0]['Ticker']
        print(f"\nGenerating chart for top pick: {top_pick}")

        df = analyze_stock(top_pick)

        plt.figure(figsize=(12, 8))
        plt.plot(df.index, df['Close'], label='Close Price', alpha=0.5)
        plt.plot(df.index, df['SMA_50'], label='SMA 50', color='orange')
        plt.plot(df.index, df['SMA_200'], label='SMA 200', color='red')
        plt.title(f'{top_pick} Price Analysis')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)

        plt.savefig('top_stock_chart.png')
        print("Chart saved as 'top_stock_chart.png'")

    else:
        print("No stocks matched the criteria in this subset.")

if __name__ == "__main__":
    main()
