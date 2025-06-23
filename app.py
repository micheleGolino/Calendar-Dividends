import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
from dividend_api import DividendCalendar

# Configurazione della pagina
st.set_page_config(
    page_title="Calendario Dividendi",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Funzione per ottenere il tasso di cambio
@st.cache_data(ttl=1800)  # Cache per 30 minuti
def get_exchange_rate(from_currency="USD", to_currency="EUR"):
    """Ottiene il tasso di cambio in tempo reale usando l'API di ExchangeRate-API"""
    if from_currency == to_currency:
        return 1.0
    
    try:
        # API gratuita per tassi di cambio
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['rates'].get(to_currency, 1.0)
    except Exception as e:
        st.warning(f"Errore nel recupero del tasso di cambio: {e}. Usando tasso approssimativo.")
        # Tasso di fallback approssimativo USD -> EUR
        return 0.85 if to_currency == "EUR" else 1.0

# Funzione per formattare valori monetari
def format_currency(value, currency_code, symbol):
    """Formatta un valore monetario con il simbolo corretto"""
    if currency_code == "USD":
        return f"${value:.2f}"
    elif currency_code == "EUR":
        return f"€{value:.2f}"
    else:
        return f"{symbol}{value:.2f}"

# Funzione per convertire valori monetari
def convert_currency_value(value, exchange_rate):
    """Converte un valore monetario usando il tasso di cambio"""
    return value * exchange_rate

# Titolo principale
st.title("💰 Calendario Dividendi Mondiale")
st.markdown("---")

# Caricamento dati
@st.cache_data(ttl=3600)  # Cache per 1 ora
def load_dividend_data():
    calendar = DividendCalendar()
    return calendar.get_dividend_data()

# Carica i dati
with st.spinner('Caricamento dati sui dividendi...'):
    df = load_dividend_data()

if df.empty:
    st.error("Nessun dato sui dividendi disponibile.")
    st.stop()

# Sidebar per i filtri
st.sidebar.header("🔍 Filtri")

# Selezione valuta
st.sidebar.subheader("💱 Valuta")
currency_options = {
    "USD ($)": {"code": "USD", "symbol": "$"},
    "EUR (€)": {"code": "EUR", "symbol": "€"}
}

selected_currency_display = st.sidebar.selectbox(
    "Seleziona valuta:",
    list(currency_options.keys()),
    index=0  # USD di default
)

selected_currency = currency_options[selected_currency_display]
currency_code = selected_currency["code"]
currency_symbol = selected_currency["symbol"]

# Ottieni il tasso di cambio
if currency_code != "USD":
    with st.spinner(f'Caricamento tasso di cambio USD → {currency_code}...'):
        exchange_rate = get_exchange_rate("USD", currency_code)
        st.sidebar.success(f"Tasso USD→{currency_code}: {exchange_rate:.4f}")
else:
    exchange_rate = 1.0

# Filtro per nome azienda
company_search = st.sidebar.text_input(
    "Cerca per nome azienda:",
    placeholder="Inserisci il nome dell'azienda..."
)

# Filtro per data ex-dividend
st.sidebar.subheader("Filtro Data Ex-Dividend")
min_date = datetime.now() + timedelta(days=1)
max_date = datetime.now() + timedelta(days=365)

date_filter = st.sidebar.date_input(
    "Data minima ex-dividend:",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

# Applicazione filtri
filtered_df = df.copy()

# Conversione valuta per la visualizzazione
filtered_df['Dividendo_Convertito'] = filtered_df['Dividendo ($)'].apply(
    lambda x: convert_currency_value(x, exchange_rate)
)

# Filtro per nome azienda
if company_search:
    filtered_df = filtered_df[
        filtered_df['Nome Azienda'].str.contains(company_search, case=False, na=False) |
        filtered_df['Simbolo'].str.contains(company_search, case=False, na=False)
    ]

# Filtro per data
filtered_df['Ex-Dividend Date'] = pd.to_datetime(filtered_df['Ex-Dividend Date'])
filtered_df = filtered_df[filtered_df['Ex-Dividend Date'] >= pd.to_datetime(date_filter)]

# Riconverti le date in stringhe per la visualizzazione
filtered_df['Ex-Dividend Date'] = filtered_df['Ex-Dividend Date'].dt.strftime('%Y-%m-%d')

# Statistiche principali
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🏢 Aziende Totali", len(filtered_df))

with col2:
    avg_yield = filtered_df['Yield (%)'].mean()
    st.metric("📈 Yield Medio", f"{avg_yield:.2f}%")

with col3:
    avg_dividend = filtered_df['Dividendo_Convertito'].mean()
    st.metric("💵 Dividendo Medio", format_currency(avg_dividend, currency_code, currency_symbol))

with col4:
    high_yield_count = len(filtered_df[filtered_df['Yield (%)'] > 5])
    st.metric("⭐ Yield > 5%", high_yield_count)

st.markdown("---")

# Tabella principale
st.subheader("📊 Calendario Dividendi")

if not filtered_df.empty:
    # Prepara i dati per la visualizzazione con la valuta convertita
    display_df = filtered_df.copy()
    display_df[f'Dividendo ({currency_symbol})'] = display_df['Dividendo_Convertito']
    
    # Rimuovi la colonna temporanea
    display_df = display_df.drop('Dividendo_Convertito', axis=1)
    display_df = display_df.drop('Dividendo ($)', axis=1)
    
    # Configurazione delle colonne per una migliore visualizzazione
    column_config = {
        "Nome Azienda": st.column_config.TextColumn("Nome Azienda", width="medium"),
        "Simbolo": st.column_config.TextColumn("Simbolo", width="small"),
        "Ex-Dividend Date": st.column_config.DateColumn("Ex-Dividend Date", width="medium"),
        f"Dividendo ({currency_symbol})": st.column_config.NumberColumn(
            f"Dividendo ({currency_symbol})", 
            format=f"{currency_symbol}%.4f", 
            width="small"
        ),
        "Frequenza": st.column_config.TextColumn("Frequenza", width="small"),
        "Data Pagamento": st.column_config.DateColumn("Data Pagamento", width="medium"),
        "Yield (%)": st.column_config.NumberColumn("Yield (%)", format="%.2f%%", width="small"),
        "Affidabilità": st.column_config.TextColumn("Affidabilità", width="small")
    }
    
    st.dataframe(
        display_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        height=600
    )
    
    # Opzione per scaricare i dati
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Scarica dati CSV",
        data=csv,
        file_name=f"calendario_dividendi_{currency_code}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
else:
    st.warning("Nessuna azienda trovata con i filtri applicati.")

# Simulatore di Guadagni da Dividendi
st.markdown("---")
st.subheader("💰 Simulatore Guadagni Dividendi")

col_sim1, col_sim2 = st.columns([1, 2])

with col_sim1:
    st.markdown("#### 📊 Parametri Investimento")
    
    # Input per l'importo da investire
    investment_amount = st.number_input(
        f"💵 Importo da investire ({currency_symbol}):",
        min_value=100.0,
        max_value=1000000.0,
        value=10000.0 * exchange_rate,
        step=100.0,
        format="%.2f"
    )
    
    # Selezione dell'azienda per la simulazione
    if not filtered_df.empty:
        company_options = filtered_df['Nome Azienda'] + " (" + filtered_df['Simbolo'] + ")"
        selected_company_idx = st.selectbox(
            "🏢 Seleziona Azienda:",
            range(len(company_options)),
            format_func=lambda x: company_options.iloc[x]
        )
        
        # Ottieni i dati dell'azienda selezionata
        selected_company = filtered_df.iloc[selected_company_idx]
        
        # Calcola il numero di azioni acquistabili
        dividend_per_share_original = selected_company['Dividendo ($)']
        dividend_per_share_converted = convert_currency_value(dividend_per_share_original, exchange_rate)
        dividend_yield_decimal = selected_company['Yield (%)'] / 100
        
        # Stima del prezzo dell'azione basato su dividend yield (convertito)
        estimated_price_usd = dividend_per_share_original / (dividend_yield_decimal / 4) if dividend_yield_decimal > 0 else 100
        estimated_price_converted = convert_currency_value(estimated_price_usd, exchange_rate)
        
        shares_buyable = investment_amount / estimated_price_converted
        
        st.markdown("#### 📈 Risultati Simulazione")
        st.metric("🎯 Azienda Selezionata", f"{selected_company['Simbolo']}")
        st.metric("💸 Prezzo Stimato per Azione", format_currency(estimated_price_converted, currency_code, currency_symbol))
        st.metric("📊 Azioni Acquistabili", f"{shares_buyable:.0f}")

with col_sim2:
    if not filtered_df.empty:
        st.markdown("#### 💰 Proiezione Guadagni Dividendi")
        
        # Calcola i guadagni per diversi periodi
        dividend_per_payment = shares_buyable * dividend_per_share_converted
        frequency = selected_company['Frequenza']
        
        # Determina quanti pagamenti all'anno
        payments_per_year = {
            'Trimestrale': 4,
            'Semestrale': 2,
            'Annuale': 1,
            'Irregolare': 2  # Assumiamo 2 come default
        }.get(frequency, 4)
        
        annual_dividend = dividend_per_payment * payments_per_year
        
        # Crea un DataFrame per la proiezione
        projection_data = {
            'Periodo': ['Singolo Pagamento', '6 Mesi', '1 Anno', '2 Anni', '5 Anni'],
            'Numero Pagamenti': [1, payments_per_year//2, payments_per_year, payments_per_year*2, payments_per_year*5],
            f'Guadagno Dividendi ({currency_symbol})': [
                dividend_per_payment,
                dividend_per_payment * (payments_per_year//2),
                annual_dividend,
                annual_dividend * 2,
                annual_dividend * 5
            ],
            'Yield sul Capitale (%)': [
                (dividend_per_payment / investment_amount) * 100,
                (dividend_per_payment * (payments_per_year//2) / investment_amount) * 100,
                (annual_dividend / investment_amount) * 100,
                (annual_dividend * 2 / investment_amount) * 100,
                (annual_dividend * 5 / investment_amount) * 100
            ]
        }
        
        projection_df = pd.DataFrame(projection_data)
        
        # Grafico della proiezione guadagni nel tempo
        fig = px.line(
            projection_df, 
            x='Periodo', 
            y=f'Guadagno Dividendi ({currency_symbol})',
            title='📈 Proiezione Guadagni nel Tempo',
            markers=True,
            labels={
                'Periodo': 'Periodo di Tempo',
                f'Guadagno Dividendi ({currency_symbol})': f'Guadagno in {currency_code} ({currency_symbol})'
            }
        )
        fig.update_traces(line_color='#1f77b4', marker_size=8)
        fig.update_layout(
            height=400,
            xaxis_title="Periodo di Tempo",
            yaxis_title=f"Guadagno Dividendi ({currency_symbol})"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Configurazione colonne per la tabella di proiezione
        projection_config = {
            "Periodo": st.column_config.TextColumn("Periodo", width="medium"),
            "Numero Pagamenti": st.column_config.NumberColumn("N° Pagamenti", width="small"),
            f"Guadagno Dividendi ({currency_symbol})": st.column_config.NumberColumn(
                f"Guadagno ({currency_symbol})", 
                format=f"{currency_symbol}%.2f", 
                width="medium"
            ),
            "Yield sul Capitale (%)": st.column_config.NumberColumn("Yield (%)", format="%.2f%%", width="medium")
        }
        
        st.dataframe(
            projection_df,
            column_config=projection_config,
            hide_index=True,
            use_container_width=True
        )
        
        # Informazioni aggiuntive
        if currency_code != "USD":
            st.info(f"""
            **📋 Dettagli Simulazione:**
            - **Azienda:** {selected_company['Nome Azienda']} ({selected_company['Simbolo']})
            - **Frequenza Dividendi:** {frequency}
            - **Prossima Ex-Dividend:** {selected_company['Ex-Dividend Date']}
            - **Affidabilità:** {selected_company['Affidabilità']}
            - **Yield Annuale:** {selected_company['Yield (%)']}%
            - **Tasso di Cambio USD→{currency_code}:** {exchange_rate:.4f}
            """)
        else:
            st.info(f"""
            **📋 Dettagli Simulazione:**
            - **Azienda:** {selected_company['Nome Azienda']} ({selected_company['Simbolo']})
            - **Frequenza Dividendi:** {frequency}
            - **Prossima Ex-Dividend:** {selected_company['Ex-Dividend Date']}
            - **Affidabilità:** {selected_company['Affidabilità']}
            - **Yield Annuale:** {selected_company['Yield (%)']}%
            """)
        
        # Warning importante
        warning_text = """
        ⚠️ **Disclaimer:** Questa è una simulazione basata sui dati storici. 
        I dividendi futuri non sono garantiti e possono variare. 
        Il prezzo delle azioni è stimato e può differire dal valore reale di mercato."""
        
        if currency_code != "USD":
            warning_text += f"""
        I tassi di cambio sono soggetti a fluttuazioni e possono influenzare significativamente i rendimenti effettivi."""
        
        warning_text += """
        Consultare sempre un consulente finanziario prima di investire.
        """
        
        st.warning(warning_text)

# Glossario
st.markdown("---")
st.subheader("📖 Glossario dei Termini")

with st.expander("🔍 Clicca per aprire il glossario", expanded=False):
    col_gloss1, col_gloss2 = st.columns(2)
    
    with col_gloss1:
        st.markdown("""
        **📊 Termini Finanziari:**
        
        **🏢 Simbolo (Ticker)**  
        Codice abbreviato che identifica univocamente un'azione in borsa (es. AAPL per Apple).
        
        **💰 Dividendo**  
        Pagamento in denaro che una società distribuisce ai suoi azionisti, solitamente derivante dai profitti.
        
        **📅 Ex-Dividend Date**  
        Data dopo la quale l'acquisto di un'azione non dà diritto al prossimo dividendo. Chi possiede l'azione prima di questa data riceverà il dividendo.
        
        **💳 Data di Pagamento**  
        Data effettiva in cui il dividendo viene accreditato sul conto dell'azionista.
        
        **📈 Dividend Yield**  
        Percentuale che indica il rendimento annuale del dividendo rispetto al prezzo corrente dell'azione. Formula: (Dividendo Annuale / Prezzo Azione) × 100.
        
        **🔄 Frequenza Dividendi**  
        - **Trimestrale:** Pagamento ogni 3 mesi (4 volte l'anno)  
        - **Semestrale:** Pagamento ogni 6 mesi (2 volte l'anno)  
        - **Annuale:** Pagamento una volta l'anno  
        - **Irregolare:** Pagamenti senza una frequenza fissa
        
        **💱 Conversione Valuta**  
        I tassi di cambio vengono aggiornati ogni 30 minuti tramite API in tempo reale. Tutti i valori monetari vengono convertiti dalla valuta originale (USD) alla valuta selezionata.
        """)
    
    with col_gloss2:
        st.markdown("""
        **⭐ Termini dell'Applicazione:**
        
        **🎯 Affidabilità**  
        Sistema di valutazione a stelle (⭐⭐⭐⭐⭐) che indica la stabilità e consistenza dei dividendi di un'azienda, basato su:
        - Consistenza dei pagamenti negli anni
        - Dimensione dell'azienda (market cap)
        - Sostenibilità del payout ratio
        
        **💸 Prezzo Stimato per Azione**  
        Valore approssimativo dell'azione calcolato in base al dividend yield e all'importo del dividendo, convertito nella valuta selezionata.
        
        **📊 Azioni Acquistabili**  
        Numero di azioni che si possono comprare con l'importo investito, considerando il prezzo stimato nella valuta selezionata.
        
        **💵 Yield sul Capitale**  
        Percentuale di rendimento che i dividendi rappresentano rispetto al capitale investito.
        
        **🔮 Proiezione Guadagni**  
        Calcolo stimato dei dividendi che si potrebbero ricevere in diversi periodi di tempo, basato sui dati storici e convertito nella valuta selezionata.
        
        **⚠️ Importante:**  
        Tutti i calcoli sono stime basate su dati storici. I mercati finanziari sono volatili e i risultati effettivi possono differire significativamente dalle proiezioni. Le fluttuazioni del tasso di cambio possono influenzare ulteriormente i rendimenti.
        """)

# Footer
footer_text = f"""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
💡 I dati sono forniti da Yahoo Finance e vengono aggiornati ogni ora.<br>
💱 Tassi di cambio aggiornati ogni 30 minuti tramite ExchangeRate-API.<br>
"""

if currency_code != "USD":
    footer_text += f"🔄 Valuta corrente: {currency_code} (Tasso USD→{currency_code}: {exchange_rate:.4f})<br>"

footer_text += """
⚠️ Le informazioni sono solo a scopo informativo e non costituiscono consigli di investimento.
</div>
"""

st.markdown("---")
st.markdown(footer_text, unsafe_allow_html=True)
