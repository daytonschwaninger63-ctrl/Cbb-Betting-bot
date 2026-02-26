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
    """Runs as a web dashboard."""
    st.title("🏀 CBB Value Finder")
    # ... (Insert the Dashboard UI code provided in previous steps here)

if __name__ == "__main__":
    if "--mode" in sys.argv:
        run_headless_scan()
    else:
        run_streamlit_ui()
