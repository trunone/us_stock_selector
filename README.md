# US Stock Selection Algorithm

This project implements an algorithm to select potential US stocks to invest in from the S&P 500 index. It uses Python and standard data analysis libraries to fetch market data, calculate technical indicators, and filter stocks based on a specific strategy.

## Strategy

The algorithm screens stocks based on the following criteria:
1.  **Trend**: The stock price is above its 200-day Simple Moving Average (SMA), indicating a long-term uptrend.
2.  **Momentum**: A "Golden Cross" condition where the 50-day SMA is above the 200-day SMA.
3.  **Valuation/Overbought**: The Relative Strength Index (RSI) is below 70, suggesting the stock is not currently overbought.

## Files

*   `stock_analysis.ipynb`: A Jupyter Notebook containing the code and explanation. This is the recommended way to explore the project.
*   `stock_analysis.py`: A Python script version of the algorithm for running in a terminal or local environment.
*   `requirements.txt`: List of dependencies.

## How to Run in Google Colab

1.  Download `stock_analysis.ipynb` to your computer.
2.  Go to [Google Colab](https://colab.research.google.com/).
3.  Click "File" -> "Upload notebook".
4.  Select the `stock_analysis.ipynb` file you downloaded.
5.  Once opened, run the first cell to install the necessary libraries (`yfinance`, etc.).
6.  Run the subsequent cells to execute the analysis.

## How to Run Locally

1.  Ensure you have Python installed.
2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the script:
    ```bash
    python stock_analysis.py
    ```
    This will print the selected stocks to the console and save a chart as `top_stock_chart.png`.

## Disclaimer

This is for educational purposes only and does not constitute financial advice. Always do your own research before investing.
