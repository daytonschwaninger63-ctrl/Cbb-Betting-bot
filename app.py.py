import streamlit as st
import pandas as pd
import requests
import smtplib
import sys
import argparse
from email.message import EmailMessage

# --- LOGIC & MATH ---
def normalize_team(name):
    mapping = {"UConn": "Connecticut", "UNC": "North Carolina"}
    return mapping.get(name, name)

def get_data(api_key):
    t_url = "https://barttorvik.com/2026_team_results.csv"
    t_df = pd.read_csv(t_url, header=None)
    projections = dict(zip(t_df[1], t_df[6]))
    
    o_url = f'https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/?apiKey={api_key}&regions=us&markets=h2h'
    odds = requests.get(o_url).json()
    return projections, odds

def send_alert(details):
    msg = EmailMessage()
    msg.set_content(f"High EV Bet Found!\n\n{details}")
    msg['Subject'] = "CBB Betting Alert"
    msg['From'] = st.secrets["EMAIL_USER"]
    msg['To'] = st.secrets["EMAIL_USER"] # Sends to yourself
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(st.secrets["EMAIL_USER"], st.secrets["EMAIL_PASS"])
        smtp.send_message(msg)

# --- RUN MODES ---
def run_headless_scan():
    """Runs automatically via GitHub Actions."""
    api_key = st.secrets["THE_ODDS_API_KEY"]
    projections, odds = get_data(api_key)
    # Filter for EV > 10% and send_alert() here...
    print("Headless scan complete.")

def run_streamlit_ui():
                 st.set_page_config(page_title="CBB Value Finder", layout="wide")
    st.title("🏀 CBB Value Finder")

    def american_to_prob(odds):
        """Converts American odds (e.g. -110, +120) to implied probability."""
        if odds > 0:
            return 100 / (odds + 100)
        return abs(odds) / (abs(odds) + 100)

    try:
        api_key = st.secrets["THE_ODDS_API_KEY"]
        with st.spinner("Analyzing BartTorvik Projections vs Market Odds..."):
            # projections = your bot's data; odds = live sportsbook data
            projections, odds = get_data(api_key) 
        
        if odds:
            rows = []
            for game in odds:
                home = game.get('home_team')
                away = game.get('away_team')
                
                # 1. Get the Market Odds (using the first bookmaker)
                bookies = game.get('bookmakers', [])
                if not bookies: continue
                
                market_data = bookies[0].get('markets', [{}])[0]
                outcomes = market_data.get('outcomes', [])
                if len(outcomes) < 2: continue

                # 2. Extract price and calculate market probability
                mkt_price = outcomes[0].get('price')
                mkt_prob = american_to_prob(mkt_price)

                # 3. Find this game in your BartTorvik projections
                # (Assuming projections is a dict or list from get_data)
                your_prob = 0.55 # Placeholder: This will link to your projection logic
                
                # 4. Calculate Edge
                edge = (your_prob - mkt_prob) * 100

                rows.append({
                    "Matchup": f"{away} @ {home}",
                    "Market Odds": mkt_price,
                    "Market %": f"{mkt_prob:.1%}",
                    "Bot %": f"{your_prob:.1%}",
                    "Edge": f"{edge:.1f}%"
                })

            # Create and style the table
            df = pd.DataFrame(rows)
            st.dataframe(df.style.background_gradient(subset=['Edge'], cmap='Greens'), use_container_width=True)
            st.success(f"Found {len(df)} live value opportunities!")

    except Exception as e:
        st.error(f"Error updating dashboard: {e}")

if __name__ == "__main__":
    if "--mode" in sys.argv:
        run_headless_scan()
    else:
        run_streamlit_ui()
