import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Top 25 Stock Picks Potensial", layout="wide")

@st.cache_data

def load_data():
    url = "https://storage.googleapis.com/stock-csvku/hasil_gabungan.csv"
    df = pd.read_csv(url)
    df['Last Trading Date'] = pd.to_datetime(df['Last Trading Date'])
    return df

def analyze_stock_group(group, last_date, days):
    recent = group[group['Last Trading Date'] >= last_date - pd.Timedelta(days=days)]
    recent_5 = group[group['Last Trading Date'] >= last_date - pd.Timedelta(days=5)]

    total_days = len(recent)
    if total_days == 0:
        return None

    akumulasi_signals = ['Akumulasi', 'Strong Akumulasi']
    akumulasi_ratio = (recent['Final Signal'].isin(akumulasi_signals).sum()) / total_days
    unusual_volume_5d = recent_5['Unusual Volume'].sum()
    avg_bid_offer = recent['Bid/Offer Imbalance'].mean()
    inflow_ratio = (recent['Foreign Flow'] == 'Inflow').sum() / total_days
    price_above_vwap = (recent_5['Close'] > recent_5['VWAP']).sum()

    score = 0
    score += 3 if akumulasi_ratio > 0.6 else 0
    score += 2 if unusual_volume_5d >= 2 else 0
    score += 2 if inflow_ratio > 0.5 else 0
    score += min(3, avg_bid_offer * 10) if avg_bid_offer > 0 else 0
    score += 1 if price_above_vwap >= 2 else 0

    latest_close = group[group['Last Trading Date'] == last_date]['Close'].values[0] if last_date in group['Last Trading Date'].values else np.nan

    return pd.Series({
        'Stock Code': group['Stock Code'].iloc[0],
        'Company Name': group['Company Name'].iloc[0],
        'Sector': group['Sector'].iloc[0],
        'Akumulasi Ratio': round(akumulasi_ratio, 2),
        'Inflow Ratio': round(inflow_ratio, 2),
        'Unusual Volume (5d)': unusual_volume_5d,
        'Avg Bid/Offer Imbalance': round(avg_bid_offer, 2),
        'Harga > VWAP (5d)': price_above_vwap,
        'Last Close Price': latest_close,
        'Score': round(score, 2)
    })

# Load data
df = load_data()
last_date = df['Last Trading Date'].max()

st.title("📈 Top 25 Stock Picks Potensial")
st.markdown("Saring saham berdasarkan fase akumulasi dominan dan sinyal volume mencurigakan terbaru.")

tabs = st.tabs(["Analisis 30 Hari", "Analisis 60 Hari", "Analisis 90 Hari"])

day_ranges = [30, 60, 90]

for i, tab in enumerate(tabs):
    with tab:
        top_stocks_df = df.groupby('Stock Code').apply(analyze_stock_group, last_date=last_date, days=day_ranges[i]).dropna()
        top_25 = top_stocks_df.sort_values(by='Score', ascending=False).head(25).reset_index(drop=True)

        all_sectors = sorted(top_25['Sector'].dropna().unique())
        selected_sector = st.selectbox(f"Filter sektor untuk {day_ranges[i]} hari:", ["All"] + all_sectors, key=f"sector_{i}")

        if selected_sector != "All":
            filtered_data = top_25[top_25['Sector'] == selected_sector]
        else:
            filtered_data = top_25

        st.dataframe(filtered_data, use_container_width=True)

        csv = filtered_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download sebagai CSV",
            data=csv,
            file_name=f'top25_stock_picks_{day_ranges[i]}d.csv',
            mime='text/csv',
            key=f'dl_{i}'
        )
