# US Asset Selection Algorithm

This project implements an algorithm to select potential US assets to invest in from the **entire US asset universe** (NASDAQ, NYSE, AMEX). It uses Python and standard data analysis libraries to fetch trading data, calculate technical indicators, and filter assets based on a specific strategy.

## Strategy

The algorithm screens assets based on the following criteria:
1.  **Trend**: The asset price is above its 200-day Simple Moving Average (SMA), indicating a long-term uptrend.
2.  **Momentum**: A "Golden Cross" condition where the 50-day SMA is above the 200-day SMA.
3.  **Valuation/Overbought**: The Relative Strength Index (RSI) is below 70, suggesting the asset is not currently overbought.

## Files

*   `asset_analysis.ipynb`: A Jupyter Notebook containing the code and explanation. **Recommended for Google Colab.**
*   `asset_analysis.py`: A Python script version of the algorithm for running in a terminal or local environment.
*   `requirements.txt`: List of dependencies.

## Key Features

*   **Comprehensive Ticker List**: Fetches over 10,000+ tickers from NASDAQ Trader, covering all major US exchanges.
*   **Batch Processing**: Efficiently downloads trading data in chunks to handle large datasets without overwhelming API limits or memory.
*   **Robust Error Handling**: Skips invalid tickers or failed downloads gracefully.

## How to Run in Google Colab

1.  Download `asset_analysis.ipynb` to your computer.
2.  Go to [Google Colab](https://colab.research.google.com/).
3.  Click "File" -> "Upload notebook".
4.  Select the `asset_analysis.ipynb` file.
5.  Run the cells sequentially.
    *   *Note*: The script is set to process a subset (first 500 tickers) by default for demonstration speed. Uncomment the line `tickers_to_process = all_tickers` in the "Run Analysis" cell to scan the entire universe (this may take 10-20 minutes).

## How to Run Locally

1.  Ensure you have Python installed.
2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the script:
    ```bash
    python asset_analysis.py
    ```
    *   This will print the selected assets to the console and save a chart of the top candidate as `top_asset_chart.png`.
    *   To scan the full universe, edit `asset_analysis.py` and change `LIMIT = 500` to a higher number or comment it out.

## Disclaimer

This is for educational purposes only and does not constitute financial advice. Always do your own research before investing.
