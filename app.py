import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dividend_api import DividendCalendar

# Configurazione della pagina
st.set_page_config(
    page_title="Calendario Dividendi",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    avg_dividend = filtered_df['Dividendo ($)'].mean()
    st.metric("💵 Dividendo Medio", f"${avg_dividend:.3f}")

with col4:
    high_yield_count = len(filtered_df[filtered_df['Yield (%)'] > 5])
    st.metric("⭐ Yield > 5%", high_yield_count)

st.markdown("---")

# Tabella principale
st.subheader("📊 Calendario Dividendi")

if not filtered_df.empty:
    # Configurazione delle colonne per una migliore visualizzazione
    column_config = {
        "Nome Azienda": st.column_config.TextColumn("Nome Azienda", width="medium"),
        "Simbolo": st.column_config.TextColumn("Simbolo", width="small"),
        "Ex-Dividend Date": st.column_config.DateColumn("Ex-Dividend Date", width="medium"),
        "Dividendo ($)": st.column_config.NumberColumn("Dividendo ($)", format="$%.4f", width="small"),
        "Frequenza": st.column_config.TextColumn("Frequenza", width="small"),
        "Data Pagamento": st.column_config.DateColumn("Data Pagamento", width="medium"),
        "Yield (%)": st.column_config.NumberColumn("Yield (%)", format="%.2f%%", width="small"),
        "Affidabilità": st.column_config.TextColumn("Affidabilità", width="small")
    }
    
    st.dataframe(
        filtered_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        height=600
    )
    
    # Opzione per scaricare i dati
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Scarica dati CSV",
        data=csv,
        file_name=f"calendario_dividendi_{datetime.now().strftime('%Y%m%d')}.csv",
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
        "💵 Importo da investire ($):",
        min_value=100.0,
        max_value=1000000.0,
        value=10000.0,
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
        # Per semplicità, usiamo un prezzo stimato basato sul dividend yield
        dividend_per_share = selected_company['Dividendo ($)']
        dividend_yield_decimal = selected_company['Yield (%)'] / 100
        
        # Stima del prezzo dell'azione basato su dividend yield
        estimated_price = dividend_per_share / (dividend_yield_decimal / 4) if dividend_yield_decimal > 0 else 100
        
        shares_buyable = investment_amount / estimated_price
        
        st.markdown("#### 📈 Risultati Simulazione")
        st.metric("🎯 Azienda Selezionata", f"{selected_company['Simbolo']}")
        st.metric("💸 Prezzo Stimato per Azione", f"${estimated_price:.2f}")
        st.metric("📊 Azioni Acquistabili", f"{shares_buyable:.0f}")

with col_sim2:
    if not filtered_df.empty:
        st.markdown("#### 💰 Proiezione Guadagni Dividendi")
        
        # Calcola i guadagni per diversi periodi
        dividend_per_payment = shares_buyable * dividend_per_share
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
            'Guadagno Dividendi ($)': [
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
        
        # Configurazione colonne per la tabella di proiezione
        projection_config = {
            "Periodo": st.column_config.TextColumn("Periodo", width="medium"),
            "Numero Pagamenti": st.column_config.NumberColumn("N° Pagamenti", width="small"),
            "Guadagno Dividendi ($)": st.column_config.NumberColumn("Guadagno ($)", format="$%.2f", width="medium"),
            "Yield sul Capitale (%)": st.column_config.NumberColumn("Yield (%)", format="%.2f%%", width="medium")
        }
        
        st.dataframe(
            projection_df,
            column_config=projection_config,
            hide_index=True,
            use_container_width=True
        )
        
        # Informazioni aggiuntive
        st.info(f"""
        **📋 Dettagli Simulazione:**
        - **Azienda:** {selected_company['Nome Azienda']} ({selected_company['Simbolo']})
        - **Frequenza Dividendi:** {frequency}
        - **Prossima Ex-Dividend:** {selected_company['Ex-Dividend Date']}
        - **Affidabilità:** {selected_company['Affidabilità']}
        - **Yield Annuale:** {selected_company['Yield (%)']}%
        """)
        
        # Warning importante
        st.warning("""
        ⚠️ **Disclaimer:** Questa è una simulazione basata sui dati storici. 
        I dividendi futuri non sono garantiti e possono variare. 
        Il prezzo delle azioni è stimato e può differire dal valore reale di mercato.
        Consultare sempre un consulente finanziario prima di investire.
        """)

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
        Valore approssimativo dell'azione calcolato in base al dividend yield e all'importo del dividendo.
        
        **📊 Azioni Acquistabili**  
        Numero di azioni che si possono comprare con l'importo investito, considerando il prezzo stimato.
        
        **💵 Yield sul Capitale**  
        Percentuale di rendimento che i dividendi rappresentano rispetto al capitale investito.
        
        **🔮 Proiezione Guadagni**  
        Calcolo stimato dei dividendi che si potrebbero ricevere in diversi periodi di tempo, basato sui dati storici.
        
        **⚠️ Importante:**  
        Tutti i calcoli sono stime basate su dati storici. I mercati finanziari sono volatili e i risultati effettivi possono differire significativamente dalle proiezioni.
        """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
    💡 I dati sono forniti da Yahoo Finance e vengono aggiornati ogni ora.<br>
    ⚠️ Le informazioni sono solo a scopo informativo e non costituiscono consigli di investimento.
    </div>
    """, 
    unsafe_allow_html=True
)
