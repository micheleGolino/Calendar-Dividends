import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
from dividend_api import DividendCalendar

DOLLAR_DIVIDEND = 'Dividend ($)'
EX_DIVIDEND_DATE = 'Ex-Dividend Date'
YIELD_PERCENTAGE = 'Yield (%)'

# Page configuration
st.set_page_config(
    page_title="Dividend Calendar",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to get exchange rate
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_exchange_rate(from_currency="USD", to_currency="EUR"):
    """Gets real-time exchange rate using ExchangeRate-API"""
    if from_currency == to_currency:
        return 1.0
    
    try:
        # Free API for exchange rates
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['rates'].get(to_currency, 1.0)
    except Exception as e:
        st.warning(f"Error retrieving exchange rate: {e}. Using approximate rate.")
        # Approximate fallback rate USD -> EUR
        return 0.85 if to_currency == "EUR" else 1.0

# Function to format currency values
def format_currency(value, currency_code, symbol):
    """Formats a monetary value with the correct symbol"""
    if currency_code == "USD":
        return f"${value:.2f}"
    elif currency_code == "EUR":
        return f"€{value:.2f}"
    else:
        return f"{symbol}{value:.2f}"

# Function to convert currency values
def convert_currency_value(value, exchange_rate):
    """Converts a monetary value using the exchange rate"""
    return value * exchange_rate

# Main title
st.title("💰 World Dividend Calendar")
st.markdown("---")

# Loading data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_dividend_data():
    calendar = DividendCalendar()
    return calendar.get_dividend_data()

# Load data
with st.spinner('Loading dividend data...'):
    df = load_dividend_data()

if df.empty:
    st.error("No dividend data available.")
    st.stop()

# Sidebar for filters
st.sidebar.header("🔍 Filters")

# Currency selection
st.sidebar.subheader("💱 Currency")
currency_options = {
    "USD ($)": {"code": "USD", "symbol": "$"},
    "EUR (€)": {"code": "EUR", "symbol": "€"}
}

selected_currency_display = st.sidebar.selectbox(
    "Select currency:",
    list(currency_options.keys()),
    index=0  # USD default
)

selected_currency = currency_options[selected_currency_display]
currency_code = selected_currency["code"]
currency_symbol = selected_currency["symbol"]

# Get exchange rate
if currency_code != "USD":
    with st.spinner(f'Loading exchange rate USD → {currency_code}...'):
        exchange_rate = get_exchange_rate("USD", currency_code)
        st.sidebar.success(f"Rate USD→{currency_code}: {exchange_rate:.4f}")
else:
    exchange_rate = 1.0

# Filter by company name
company_search = st.sidebar.text_input(
    "Search by company name:",
    placeholder="Enter company name..."
)

# Filter by ex-dividend date
st.sidebar.subheader("Ex-Dividend Date Filter")
min_date = datetime.now() + timedelta(days=1)
max_date = datetime.now() + timedelta(days=365)

date_filter = st.sidebar.date_input(
    "Minimum ex-dividend date:",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

# Apply filters
filtered_df = df.copy()

# Currency conversion for display
filtered_df['Dividend_Converted'] = filtered_df[DOLLAR_DIVIDEND].apply(
    lambda x: convert_currency_value(x, exchange_rate)
)

# Filter by company name
if company_search:
    filtered_df = filtered_df[
        filtered_df['Company Name'].str.contains(company_search, case=False, na=False) |
        filtered_df['Symbol'].str.contains(company_search, case=False, na=False)
    ]

# Filter by ex-dividend date
filtered_df[EX_DIVIDEND_DATE] = pd.to_datetime(filtered_df[EX_DIVIDEND_DATE])
filtered_df = filtered_df[filtered_df[EX_DIVIDEND_DATE] >= pd.to_datetime(date_filter)]

# Convert dates back to strings for display
filtered_df[EX_DIVIDEND_DATE] = filtered_df[EX_DIVIDEND_DATE].dt.strftime('%Y-%m-%d')

# Main statistics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🏢 Total Companies", len(filtered_df))

with col2:
    avg_yield = filtered_df[YIELD_PERCENTAGE].mean()
    st.metric("📈 Average Yield", f"{avg_yield:.2f}%")

with col3:
    avg_dividend = filtered_df['Dividend_Converted'].mean()
    st.metric("💵 Average Dividend", format_currency(avg_dividend, currency_code, currency_symbol))

with col4:
    high_yield_count = len(filtered_df[filtered_df[YIELD_PERCENTAGE] > 5])
    st.metric("⭐ Yield > 5%", high_yield_count)

st.markdown("---")

# Main table
st.subheader("📊 Dividend Calendar")

if not filtered_df.empty:
    # Prepare data for display with converted currency
    display_df = filtered_df.copy()
    display_df[f'Dividend ({currency_symbol})'] = display_df['Dividend_Converted']
    
    # Remove temporary column
    display_df = display_df.drop('Dividend_Converted', axis=1)
    display_df = display_df.drop(DOLLAR_DIVIDEND, axis=1)
    
    # Configure columns for better display
    column_config = {
        "Company Name": st.column_config.TextColumn("Company Name", width="medium"),
        "Symbol": st.column_config.TextColumn("Symbol", width="small"),
        "Ex-Dividend Date": st.column_config.DateColumn("Ex-Dividend Date", width="medium"),
        f"Dividend ({currency_symbol})": st.column_config.NumberColumn(
            f"Dividend ({currency_symbol})", 
            format=f"{currency_symbol}%.4f", 
            width="small"
        ),
        "Frequency": st.column_config.TextColumn("Frequency", width="small"),
        "Payment Date": st.column_config.DateColumn("Payment Date", width="medium"),
         YIELD_PERCENTAGE: st.column_config.NumberColumn(YIELD_PERCENTAGE, format="%.2f%%", width="small"),
        "Reliability": st.column_config.TextColumn("Reliability", width="small")
    }
    
    st.dataframe(
        display_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        height=600
    )
    
    # Option to download data
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV data",
        data=csv,
        file_name=f"dividend_calendar_{currency_code}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
else:
    st.warning("No companies found with applied filters.")

# Dividend Earnings Simulator
st.markdown("---")
st.subheader("💰 Dividend Earnings Simulator")

col_sim1, col_sim2 = st.columns([1, 2])

with col_sim1:
    st.markdown("#### 📊 Investment Parameters")
    
    # Input for investment amount
    investment_amount = st.number_input(
        f"💵 Amount to invest ({currency_symbol}):",
        min_value=100.0,
        max_value=1000000.0,
        value=10000.0 * exchange_rate,
        step=100.0,
        format="%.2f"
    )
    
    # Company selection for simulation
    if not filtered_df.empty:
        company_options = filtered_df['Company Name'] + " (" + filtered_df['Symbol'] + ")"
        selected_company_idx = st.selectbox(
            "🏢 Select Company:",
            range(len(company_options)),
            format_func=lambda x: company_options.iloc[x]
        )
        
        # Get selected company data
        selected_company = filtered_df.iloc[selected_company_idx]
        
        # Calculate purchasable shares
        dividend_per_share_original = selected_company[DOLLAR_DIVIDEND]
        dividend_per_share_converted = convert_currency_value(dividend_per_share_original, exchange_rate)
        dividend_yield_decimal = selected_company[YIELD_PERCENTAGE] / 100
        
        # Estimate share price based on dividend yield (converted)
        estimated_price_usd = dividend_per_share_original / (dividend_yield_decimal / 4) if dividend_yield_decimal > 0 else 100
        estimated_price_converted = convert_currency_value(estimated_price_usd, exchange_rate)
        
        shares_buyable = investment_amount / estimated_price_converted
        
        st.markdown("#### 📈 Simulation Results")
        st.metric("🎯 Selected Company", f"{selected_company['Symbol']}")
        st.metric("💸 Estimated Price per Share", format_currency(estimated_price_converted, currency_code, currency_symbol))
        st.metric("📊 Purchasable Shares", f"{shares_buyable:.0f}")

with col_sim2:
    if not filtered_df.empty:
        st.markdown("#### 💰 Dividend Earnings Projection")
        
        # Calculate earnings for different periods
        dividend_per_payment = shares_buyable * dividend_per_share_converted
        frequency = selected_company['Frequency']
        
        # Determine payments per year
        payments_per_year = {
            'Quarterly': 4,
            'Semi-annual': 2,
            'Annual': 1,
            'Irregular': 2  # Assume 2 as default
        }.get(frequency, 4)
        
        annual_dividend = dividend_per_payment * payments_per_year
        
        # Create projection DataFrame
        projection_data = {
            'Period': ['Single Payment', '6 Months', '1 Year', '2 Years', '5 Years'],
            'Number of Payments': [1, payments_per_year//2, payments_per_year, payments_per_year*2, payments_per_year*5],
            f'Dividend Earnings ({currency_symbol})': [
                dividend_per_payment,
                dividend_per_payment * (payments_per_year//2),
                annual_dividend,
                annual_dividend * 2,
                annual_dividend * 5
            ],
            'Yield on Capital (%)': [
                (dividend_per_payment / investment_amount) * 100,
                (dividend_per_payment * (payments_per_year//2) / investment_amount) * 100,
                (annual_dividend / investment_amount) * 100,
                (annual_dividend * 2 / investment_amount) * 100,
                (annual_dividend * 5 / investment_amount) * 100
            ]
        }
        
        projection_df = pd.DataFrame(projection_data)
        
        # Earnings projection chart
        fig = px.line(
            projection_df, 
            x='Period', 
            y=f'Dividend Earnings ({currency_symbol})',
            title='📈 Earnings Projection Over Time',
            markers=True,
            labels={
                'Period': 'Time Period',
                f'Dividend Earnings ({currency_symbol})': f'Earnings in {currency_code} ({currency_symbol})'
            }
        )
        fig.update_traces(line_color='#1f77b4', marker_size=8)
        fig.update_layout(
            height=400,
            xaxis_title="Time Period",
            yaxis_title=f"Dividend Earnings ({currency_symbol})"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Projection table column configuration
        projection_config = {
            "Period": st.column_config.TextColumn("Period", width="medium"),
            "Number of Payments": st.column_config.NumberColumn("Num. Payments", width="small"),
            f"Dividend Earnings ({currency_symbol})": st.column_config.NumberColumn(
                f"Earnings ({currency_symbol})", 
                format=f"{currency_symbol}%.2f", 
                width="medium"
            ),
            "Yield on Capital (%)": st.column_config.NumberColumn("Yield (%)", format="%.2f%%", width="medium")
        }
        
        st.dataframe(
            projection_df,
            column_config=projection_config,
            hide_index=True,
            use_container_width=True
        )
        
        # Additional information
        if currency_code != "USD":
            st.info(f"""
            **📋 Simulation Details:**
            - **Company:** {selected_company['Company Name']} ({selected_company['Symbol']})
            - **Dividend Frequency:** {frequency}
            - **Next Ex-Dividend:** {selected_company['Ex-Dividend Date']}
            - **Reliability:** {selected_company['Reliability']}
            - **Annual Yield:** {selected_company[YIELD_PERCENTAGE]}%
            - **Exchange Rate USD→{currency_code}:** {exchange_rate:.4f}
            """)
        else:
            st.info(f"""
            **📋 Simulation Details:**
            - **Company:** {selected_company['Company Name']} ({selected_company['Symbol']})
            - **Dividend Frequency:** {frequency}
            - **Next Ex-Dividend:** {selected_company['Ex-Dividend Date']}
            - **Reliability:** {selected_company['Reliability']}
            - **Annual Yield:** {selected_company[YIELD_PERCENTAGE]}%
            """)
        
        # Important warning
        warning_text = """
        ⚠️ **Disclaimer:** This is a simulation based on historical data. 
        Future dividends are not guaranteed and may vary. 
        The share price is estimated and may differ from the actual market value."""
        
        if currency_code != "USD":
            warning_text += """
        Exchange rates are subject to fluctuations and can significantly affect actual returns."""
        
        warning_text += """
        Always consult a financial advisor before investing.
        """
        
        st.warning(warning_text)

# Glossary
st.markdown("---")
st.subheader("📖 Glossary of Terms")

with st.expander("🔍 Click to open the glossary", expanded=False):
    col_gloss1, col_gloss2 = st.columns(2)
    
    with col_gloss1:
        st.markdown("""
        **📊 Financial Terms:**
        
        **🏢 Symbol (Ticker)**  
        Abbreviated code that uniquely identifies a stock on the exchange (e.g., AAPL for Apple).
        
        **💰 Dividend**  
        Cash payment that a company distributes to its shareholders, usually derived from profits.
        
        **📅 Ex-Dividend Date**  
        Date after which purchasing a stock does not entitle you to the next dividend. Those who own the stock before this date will receive the dividend.
        
        **💳 Payment Date**  
        Actual date when the dividend is credited to the shareholder's account.
        
        **📈 Dividend Yield**  
        Percentage that indicates the annual dividend return relative to the current stock price. Formula: (Annual Dividend / Stock Price) × 100.
        
        **🔄 Dividend Frequency**  
        - **Quarterly:** Payment every 3 months (4 times a year)  
        - **Semi-annual:** Payment every 6 months (2 times a year)  
        - **Annual:** Payment once a year  
        - **Irregular:** Payments without a fixed frequency
        
        **💱 Currency Conversion**  
        Exchange rates are updated every 30 minutes via real-time API. All monetary values are converted from the original currency (USD) to the selected currency.
        """)
    
    with col_gloss2:
        st.markdown("""
        **⭐ Application Terms:**
        
        **🎯 Reliability**  
        Star rating system (⭐⭐⭐⭐⭐) indicating the stability and consistency of a company's dividends, based on:
        - Consistency of payments over the years
        - Company size (market cap)
        - Sustainability of the payout ratio
        
        **💸 Estimated Price per Share**  
        Approximate value of the stock calculated based on dividend yield and dividend amount, converted to the selected currency.
        
        **📊 Purchasable Shares**  
        Number of shares that can be bought with the invested amount, considering the estimated price in the selected currency.
        
        **💵 Yield on Capital**  
        Percentage return that dividends represent relative to the invested capital.
        
        **🔮 Earnings Projection**  
        Estimated calculation of dividends that could be received over different time periods, based on historical data and converted to the selected currency.
        
        **⚠️ Important:**  
        All calculations are estimates based on historical data. Financial markets are volatile and actual results may differ significantly from projections. Exchange rate fluctuations can further affect returns.
        """)

# Footer
footer_text = """
<div style='text-align: center; color: #666; font-size: 0.9em;'>
💡 Data is provided by Yahoo Finance and updated every hour.<br>
💱 Exchange rates updated every 30 minutes via ExchangeRate-API.<br>
"""

if currency_code != "USD":
    footer_text += f"🔄 Current currency: {currency_code} (Rate USD→{currency_code}: {exchange_rate:.4f})<br>"

footer_text += """
⚠️ Information is for informational purposes only and does not constitute investment advice.
</div>
"""

st.markdown("---")
st.markdown(footer_text, unsafe_allow_html=True)
