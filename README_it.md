# 💰 Calendario Dividendi Mondiale

Un'applicazione web interattiva costruita con **Streamlit** per monitorare, analizzare e simulare i dividendi delle azioni più importanti del mercato mondiale.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.41.0-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 📋 Descrizione

Il **Calendario Dividendi Mondiale** è uno strumento completo per investitori che vogliono:

- 📊 **Monitorare i dividendi** di oltre 140 aziende quotate
- 🔍 **Filtrare e cercare** aziende per nome o simbolo ticker
- 💱 **Convertire valute** in tempo reale (USD ↔ EUR)
- 💰 **Simulare guadagni** da investimenti in dividendi
- 📈 **Visualizzare proiezioni** di rendimento nel tempo
- 📥 **Esportare dati** in formato CSV

## ✨ Funzionalità Principali

### 🎯 Dashboard Principale
- **Statistiche in tempo reale**: Numero totale aziende, yield medio, dividendo medio
- **Tabella interattiva**: Calendario completo con tutte le informazioni sui dividendi
- **Filtri avanzati**: Per data ex-dividend e ricerca per nome/simbolo

### 💱 Conversione Valuta
- **Supporto multi-valuta**: USD (dollaro) ed EUR (euro)
- **Tassi di cambio in tempo reale**: Aggiornati ogni 30 minuti via API
- **Conversione automatica**: Tutti i valori monetari vengono convertiti dinamicamente

### 💰 Simulatore di Investimenti
- **Calcolo rendimenti**: Stima guadagni basata su importo investito
- **Proiezioni temporali**: Visualizza rendimenti a 6 mesi, 1 anno, 2 anni, 5 anni
- **Grafici interattivi**: Visualizzazione dell'andamento nel tempo
- **Analisi dettagliata**: Informazioni complete sull'azienda selezionata

### 📊 Copertura del Mercato
L'applicazione monitora oltre **140 simboli azionari** suddivisi per settore:

- 🖥️ **Technology**: AAPL, MSFT, GOOGL, NVDA, META, ORCL, ADBE, AMD...
- 🏥 **Healthcare**: JNJ, PFE, UNH, ABBV, LLY, TMO, ABT...
- 🏦 **Financial**: JPM, BAC, V, MA, GS, MS, BLK...
- 🛒 **Consumer**: PG, KO, WMT, COST, MCD, NKE, DIS...
- ⛽ **Energy**: XOM, CVX, COP, EOG, SLB...
- ⚡ **Utilities**: NEE, DUK, SO, AEP...
- 🏭 **Industrial**: GE, MMM, HON, CAT, BA...
- 🏢 **REITs**: AMT, PLD, CCI, EQIX, SPG...

## 🚀 Come Avviare il Progetto

### Prerequisiti

- **Python 3.8+** installato sul sistema
- **pip** (gestore pacchetti Python)
- Connessione internet (per API di dati finanziari e tassi di cambio)

### 1. Clona il Repository

```bash
git clone https://github.com/tuo-username/Calendar-Dividends.git
cd Calendar-Dividends
```

### 2. Installa le Dipendenze

```bash
pip install -r requirements.txt
```

### 3. Avvia l'Applicazione

```bash
streamlit run app.py
```

### 4. Accedi all'Applicazione

L'applicazione si aprirà automaticamente nel browser all'indirizzo:
```
http://localhost:8501
```

## 📦 Dipendenze

Il progetto utilizza le seguenti librerie principali:

```
streamlit==1.41.0      # Framework web per l'interfaccia
yfinance>=0.2.18       # API per dati finanziari Yahoo Finance
pandas>=2.1.0          # Manipolazione e analisi dati
numpy>=1.25.0          # Calcoli numerici
plotly>=5.0.0          # Grafici interattivi
requests==2.31.0       # Richieste HTTP per API di cambio valuta
watchdog>=3.0.0        # Monitoraggio file system
```

## 🔧 Struttura del Progetto

```
Calendar-Dividends/
│
├── app.py                 # Applicazione principale Streamlit
├── dividend_api.py        # Classe per recupero dati dividendi
├── requirements.txt       # Dipendenze Python
├── README.md             # Documentazione progetto
│
└── (file generati automaticamente da Streamlit)
```

## 📊 Fonti Dati

- **🔢 Dati Finanziari**: [Yahoo Finance](https://finance.yahoo.com/) via libreria `yfinance`
- **💱 Tassi di Cambio**: [ExchangeRate-API](https://exchangerate-api.com/) - API gratuita
- **⏰ Aggiornamento**: 
  - Dati dividendi: ogni ora (cache)
  - Tassi di cambio: ogni 30 minuti (cache)

## 🎯 Come Utilizzare l'Applicazione

### 1. **Esplora il Calendario**
- Visualizza la tabella principale con tutti i dividendi
- Usa i filtri nella sidebar per personalizzare la vista
- Ordina le colonne cliccando sui headers

### 2. **Cambia Valuta**
- Seleziona EUR dalla dropdown "Valuta" nella sidebar
- Tutti i valori si convertiranno automaticamente

### 3. **Simula un Investimento**
- Scorri verso il basso fino al "Simulatore Guadagni Dividendi"
- Inserisci l'importo che vuoi investire
- Seleziona un'azienda dalla dropdown
- Visualizza le proiezioni di guadagno nel tempo

### 4. **Esporta i Dati**
- Clicca su "📥 Scarica dati CSV" per esportare la tabella filtrata
- Il file includerà tutti i dati nella valuta selezionata

## ⚠️ Limitazioni e Disclaimer

- **📊 Dati Storici**: Le proiezioni sono basate su dati storici e non garantiscono risultati futuri
- **💱 Fluttuazioni Valutarie**: I tassi di cambio possono influenzare significativamente i rendimenti
- **🎯 Stime dei Prezzi**: I prezzi delle azioni sono stimati basandosi sul dividend yield
- **⚖️ Non è Consulenza Finanziaria**: L'applicazione è solo a scopo informativo

## 🛠️ Sviluppo e Contributi

### Estendere l'Applicazione

Per aggiungere nuovi simboli azionari, modifica la lista `self.symbols` in `dividend_api.py`:

```python
self.symbols = [
    'AAPL', 'MSFT', # ... simboli esistenti
    'NUOVO_SIMBOLO'  # Aggiungi qui
]
```

### Aggiungere Nuove Valute

Per supportare nuove valute, modifica il dizionario `currency_options` in `app.py`:

```python
currency_options = {
    "USD ($)": {"code": "USD", "symbol": "$"},
    "EUR (€)": {"code": "EUR", "symbol": "€"},
    "GBP (£)": {"code": "GBP", "symbol": "£"}  # Nuova valuta
}
```

## 📄 Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi il file `LICENSE` per i dettagli.

## 🤝 Supporto

Per domande, problemi o suggerimenti:

1. **Issues**: Apri una issue su GitHub
2. **Documentation**: Consulta il glossario integrato nell'app
3. **Updates**: Controlla regolarmente per aggiornamenti

---

**🎯 Buon investimento e monitoraggio dividendi!** 💰📈
