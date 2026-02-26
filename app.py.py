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
         if odds:
            st.success("Analysis Complete!")
            
            rows = []
            for game in odds:
                # 1. Get Team Names
                home = game.get('home_team')
                away = game.get('away_team')
            
                # 2. Get Market Odds (e.g., FanDuel/DraftKings)
                bookies = game.get('bookmakers', [])
                if not bookies: continue
                
                # We'll look at the first bookmaker for the 'spreads' market
                market_line = "N/A"
                implied_prob = 0.524  # Default for -110 odds
                
                markets = bookies[0].get('markets', [])
                for m in markets:
                    if m['key'] == 'spreads':
                        outcome = m['outcomes'][0]
                        market_line = f"{outcome['name']} {outcome['point']}"
                        # Convert American Odds (like -110) to Implied %
                        price = outcome['price']
                        if price > 0:
                            implied_prob = 100 / (price + 100)
                        else:
                            implied_prob = abs(price) / (abs(price) + 100)

                # 3. Get Your Bot's Projection (Dummy logic for now)
                # In a real setup, this pulls from your 'projections' data
                projected_win_prob = 0.58  # Let's assume bot thinks 58%
                
                # 4. Calculate the Edge
                edge = (projected_win_prob - implied_prob) * 100
                
                rows.append({
                    "Game": f"{away} @ {home}",
                    "Market Line": market_line,
                    "Our Win %": f"{projected_win_prob:.1%}",
                    "Market %": f"{implied_prob:.1%}",
                    "Edge": f"{edge:.1f}%"
                })

            # Create a styled dataframe
            df = pd.DataFrame(rows)
            
            # Highlight high edge games in green
            def color_edge(val):
                color = 'green' if float(val.strip('%')) > 5 else 'white'
                return f'color: {color}'

            st.dataframe(df.style.applymap(color_edge, subset=['Edge']), use_container_width=True)

if __name__ == "__main__":
    if "--mode" in sys.argv:
        run_headless_scan()
    else:
        run_streamlit_ui()
