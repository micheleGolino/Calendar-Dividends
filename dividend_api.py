import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class DividendCalendar:
    def __init__(self):
        # Extended list of popular stock symbols with dividends
        self.symbols = [
            # Tech Giants
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'ORCL', 'CRM', 'ADBE',
            'INTC', 'IBM', 'CSCO', 'PYPL', 'NFLX', 'AMD', 'QCOM', 'TXN', 'AVGO', 'NOW',
            
            # Healthcare & Pharma
            'JNJ', 'PFE', 'MRK', 'ABBV', 'UNH', 'CVS', 'WBA', 'BMY', 'LLY', 'TMO',
            'ABT', 'MDT', 'GILD', 'AMGN', 'DHR', 'SYK', 'ZTS', 'BDX', 'BSX', 'EW',
            
            # Financial Services
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'TFC', 'COF',
            'AXP', 'BLK', 'SCHW', 'CB', 'MMC', 'AIG', 'PRU', 'MET', 'AFL', 'ALL',
            
            # Consumer Goods & Retail
            'PG', 'KO', 'PEP', 'WMT', 'COST', 'TGT', 'HD', 'LOW', 'MCD', 'SBUX',
            'NKE', 'DIS', 'CL', 'KMB', 'GIS', 'K', 'HSY', 'MKC', 'CPB', 'CAG',
            
            # Energy
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO', 'MPC', 'KMI', 'OKE',
            'EPD', 'ET', 'WMB', 'ENB', 'TRP', 'SU', 'CNQ', 'IMO', 'CVE', 'HES',
            
            # Utilities
            'NEE', 'DUK', 'SO', 'D', 'EXC', 'SRE', 'AEP', 'XEL', 'PEG', 'ED',
            'ES', 'FE', 'ETR', 'WEC', 'DTE', 'PPL', 'CMS', 'NI', 'LNT', 'ATO',
            
            # Industrial & Manufacturing
            'GE', 'MMM', 'HON', 'UPS', 'CAT', 'DE', 'BA', 'LMT', 'RTX', 'GD',
            'NOC', 'EMR', 'ITW', 'PH', 'ROK', 'DOV', 'ETN', 'CMI', 'IR', 'JCI',
            
            # Telecom
            'T', 'VZ', 'TMUS', 'CHTR', 'CMCSA',
            
            # Payment & FinTech
            'V', 'MA', 'PYPL', 'SQ', 'FIS', 'FISV',
            
            # REITs
            'AMT', 'PLD', 'CCI', 'EQIX', 'SPG', 'O', 'WELL', 'EXR', 'AVB', 'EQR',
            
            # Materials & Chemicals
            'LIN', 'APD', 'ECL', 'SHW', 'DD', 'DOW', 'PPG', 'NEM', 'FCX', 'NUE',
            
            # Food & Beverage
            'MDLZ', 'KHC', 'STZ', 'TAP', 'TSN', 'HRL', 'SJM', 'BF.B',
            
            # Aerospace & Defense
            'LHX', 'TDG', 'HWM', 'TXT', 'CW', 'WWD'
        ]
    
    def calculate_frequency(self, dividends):
        """Calculates the dividend frequency based on historical data"""
        if len(dividends) < 2:
            return "N/A"
        
        # Calculate the average difference between payments
        dates = dividends.index.to_list()
        differences = []
        for i in range(1, len(dates)):
            diff = (dates[i] - dates[i-1]).days
            differences.append(diff)
        
        if not differences:
            return "N/A"
        
        avg_diff = np.mean(differences)
        
        if avg_diff <= 100:  # ~3 months
            return "Quarterly"
        elif avg_diff <= 200:  # ~6 months
            return "Semi-annual"
        elif avg_diff <= 400:  # ~1 year
            return "Annual"
        else:
            return "Irregular"
    
    def calculate_reliability_score(self, dividends, info):
        """Calculates a reliability score based on various factors"""
        score = 0
        
        # Consistency of dividends over the last 5 years
        if len(dividends) >= 20:  # At least 5 years of quarterly dividends
            score += 3
        elif len(dividends) >= 10:
            score += 2
        elif len(dividends) >= 4:
            score += 1
        
        # Market cap (higher = more reliable)
        market_cap = info.get('marketCap', 0)
        if market_cap > 100_000_000_000:  # >100B
            score += 2
        elif market_cap > 10_000_000_000:  # >10B
            score += 1
        
        # Payout ratio (lower = more sustainable)
        payout_ratio = info.get('payoutRatio', 1)
        if payout_ratio and payout_ratio < 0.6:
            score += 2
        elif payout_ratio and payout_ratio < 0.8:
            score += 1
        
        return min(score, 5)  # Max 5 stars
    
    def estimate_next_ex_date(self, last_date, frequency):
        """Estimates the next ex-dividend date based on frequency"""
        if frequency == "Quarterly":
            return last_date + timedelta(days=90)
        elif frequency == "Semi-annual":
            return last_date + timedelta(days=180)
        elif frequency == "Annual":
            return last_date + timedelta(days=365)
        else:
            return last_date + timedelta(days=90)  # Default
    
    def calculate_dividend_yield(self, last_dividend, frequency, current_price):
        """Calculates the dividend yield"""
        if current_price <= 0:
            return 0
            
        if frequency == "Quarterly":
            multiplier = 4
        elif frequency == "Semi-annual":
            multiplier = 2
        else:
            multiplier = 1
            
        annual_dividend = last_dividend * multiplier
        return (annual_dividend / current_price) * 100
    
    def process_symbol(self, symbol):
        """Processes a single symbol and returns dividend data"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        dividends = ticker.dividends
        
        if dividends.empty:
            return None
        
        # Get the latest dividends
        recent_dividends = dividends.tail(10)
        last_dividend = recent_dividends.iloc[-1]
        
        # Calculate frequency and dates
        frequency = self.calculate_frequency(recent_dividends)
        last_date = recent_dividends.index[-1]
        next_ex_date = self.estimate_next_ex_date(last_date, frequency)
        payment_date = next_ex_date + timedelta(days=21)
        
        # Calculate the yield
        current_price = info.get('currentPrice', info.get('previousClose', 0))
        dividend_yield = self.calculate_dividend_yield(last_dividend, frequency, current_price)
        
        # Reliability
        reliability = self.calculate_reliability_score(dividends, info)
        
        return {
            'Company Name': info.get('longName', symbol),
            'Symbol': symbol,
            'Ex-Dividend Date': next_ex_date.strftime('%Y-%m-%d'),
            'Dividend ($)': round(last_dividend, 4),
            'Frequency': frequency,
            'Payment Date': payment_date.strftime('%Y-%m-%d'),
            'Yield (%)': round(dividend_yield, 2),
            'Reliability': '⭐' * reliability + '☆' * (5 - reliability)
        }
    
    def get_dividend_data(self):
        """Retrieves dividend data for all symbols"""
        dividend_data = []
        
        for symbol in self.symbols:
            try:
                result = self.process_symbol(symbol)
                if result:
                    dividend_data.append(result)
            except Exception as e:
                print(f"Error retrieving data for {symbol}: {e}")
                continue
        
        return pd.DataFrame(dividend_data)
