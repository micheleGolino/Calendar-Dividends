import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class DividendCalendar:
    def __init__(self):
        # Lista di simboli azionari popolari con dividendi
        self.symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'JNJ', 'JPM', 'PG',
            'KO', 'PFE', 'DIS', 'WMT', 'V', 'MA', 'HD', 'BAC', 'XOM', 'CVX',
            'INTC', 'IBM', 'GE', 'T', 'VZ', 'MRK', 'ABBV', 'NKE', 'MCD', 'MMM',
            'UNH', 'CVS', 'WBA', 'COST', 'TGT', 'LOW', 'SBUX', 'PYPL', 'NFLX', 'CRM'
        ]
    
    def calculate_frequency(self, dividends):
        """Calcola la frequenza dei dividendi basata sui dati storici"""
        if len(dividends) < 2:
            return "N/A"
        
        # Calcola la differenza media tra i pagamenti
        dates = dividends.index.to_list()
        differences = []
        for i in range(1, len(dates)):
            diff = (dates[i] - dates[i-1]).days
            differences.append(diff)
        
        if not differences:
            return "N/A"
        
        avg_diff = np.mean(differences)
        
        if avg_diff <= 100:  # ~3 mesi
            return "Trimestrale"
        elif avg_diff <= 200:  # ~6 mesi
            return "Semestrale"
        elif avg_diff <= 400:  # ~1 anno
            return "Annuale"
        else:
            return "Irregolare"
    
    def calculate_reliability_score(self, dividends, info):
        """Calcola un punteggio di affidabilità basato su vari fattori"""
        score = 0
        
        # Consistenza dei dividendi negli ultimi 5 anni
        if len(dividends) >= 20:  # Almeno 5 anni di dividendi trimestrali
            score += 3
        elif len(dividends) >= 10:
            score += 2
        elif len(dividends) >= 4:
            score += 1
        
        # Market cap (maggiore = più affidabile)
        market_cap = info.get('marketCap', 0)
        if market_cap > 100_000_000_000:  # >100B
            score += 2
        elif market_cap > 10_000_000_000:  # >10B
            score += 1
        
        # Payout ratio (più basso = più sostenibile)
        payout_ratio = info.get('payoutRatio', 1)
        if payout_ratio and payout_ratio < 0.6:
            score += 2
        elif payout_ratio and payout_ratio < 0.8:
            score += 1
        
        return min(score, 5)  # Max 5 stelle
    
    def get_dividend_data(self):
        """Recupera i dati sui dividendi per tutti i simboli"""
        dividend_data = []
        
        for symbol in self.symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                dividends = ticker.dividends
                
                if dividends.empty:
                    continue
                
                # Prendi gli ultimi dividendi
                recent_dividends = dividends.tail(10)
                last_dividend = recent_dividends.iloc[-1]
                
                # Stima la prossima ex-dividend date
                frequency = self.calculate_frequency(recent_dividends)
                last_date = recent_dividends.index[-1]
                
                if frequency == "Trimestrale":
                    next_ex_date = last_date + timedelta(days=90)
                elif frequency == "Semestrale":
                    next_ex_date = last_date + timedelta(days=180)
                elif frequency == "Annuale":
                    next_ex_date = last_date + timedelta(days=365)
                else:
                    next_ex_date = last_date + timedelta(days=90)  # Default
                
                # Calcola il yield
                current_price = info.get('currentPrice', info.get('previousClose', 0))
                if current_price > 0:
                    annual_dividend = last_dividend * (4 if frequency == "Trimestrale" else 
                                                     2 if frequency == "Semestrale" else 1)
                    dividend_yield = (annual_dividend / current_price) * 100
                else:
                    dividend_yield = 0
                
                # Data di pagamento stimata (solitamente ~3 settimane dopo ex-date)
                payment_date = next_ex_date + timedelta(days=21)
                
                # Affidabilità
                reliability = self.calculate_reliability_score(dividends, info)
                
                dividend_data.append({
                    'Nome Azienda': info.get('longName', symbol),
                    'Simbolo': symbol,
                    'Ex-Dividend Date': next_ex_date.strftime('%Y-%m-%d'),
                    'Dividendo ($)': round(last_dividend, 4),
                    'Frequenza': frequency,
                    'Data Pagamento': payment_date.strftime('%Y-%m-%d'),
                    'Yield (%)': round(dividend_yield, 2),
                    'Affidabilità': '⭐' * reliability + '☆' * (5 - reliability)
                })
                
            except Exception as e:
                print(f"Errore nel recuperare dati per {symbol}: {e}")
                continue
        
        return pd.DataFrame(dividend_data)
