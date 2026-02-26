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
    
    try:
        api_key = st.secrets["THE_ODDS_API_KEY"]
        with st.spinner("Calculating edges..."):
            projections, odds = get_data(api_key)
        
        if odds:
            rows = []
            for game in odds:
                home = game.get('home_team')
                away = game.get('away_team')
                
                # Pulling the market price
                bookies = game.get('bookmakers', [])
                market_price = "N/A"
                if bookies:
                    m = bookies[0].get('markets', [{}])[0]
                    outcomes = m.get('outcomes', [{}, {}])
                    market_price = f"{outcomes[0].get('price', '')}"

                # Calculate a 'dummy' edge for the table display
                # (Later we will connect this to your BartTorvik math)
                edge_val = 5.4 

                rows.append({
                    "Teams": f"{away} @ {home}",
                    "Odds": market_price,
                    "Edge %": f"{edge_val}%"
                })

            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            st.success("Analysis Complete!")
    except Exception as e:
        st.error(f"Error: {e}")


if __name__ == "__main__":
    if "--mode" in sys.argv:
        run_headless_scan()
    else:
        run_streamlit_ui()
