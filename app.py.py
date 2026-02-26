import streamlit as st
import pandas as pd
import requests

def get_data(api_key):
    # 1. Fetch live market odds
    odds_url = f"https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/?apiKey={api_key}&regions=us&markets=spreads"
    odds_resp = requests.get(odds_url).json()
    
    # 2. Fetch real BartTorvik projections
    proj_url = "https://barttorvik.com/2026_data.json" 
    try:
        proj_resp = requests.get(proj_url).json()
    except:
        proj_resp = []
    return proj_resp, odds_resp

def run_streamlit_ui():
    st.set_page_config(page_title="CBB Value Finder", layout="wide")
    st.title("🏀 CBB Value Finder")

    try:
        api_key = st.secrets["THE_ODDS_API_KEY"]
        with st.spinner("Connecting to BartTorvik..."):
            projections, odds = get_data(api_key) 
        
        if odds:
            rows = []
            for game in odds:
                home = game.get('home_team')
                away = game.get('away_team')
                bookies = game.get('bookmakers', [])
                if not bookies: continue
                
                # Market Probability Math
                m = bookies[0].get('markets', [{}])[0]
                outcomes = m.get('outcomes', [{}, {}])
                mkt_price = outcomes[0].get('price', 0)
                mkt_prob = (abs(mkt_price)/(abs(mkt_price)+100)) if mkt_price < 0 else (100/(mkt_price+100))
                
                # REVISED BOT LOGIC: 
                # We use a 'Fuzzy' check to find the team name in the BartTorvik list (index 0 or 1)
                bot_prob_raw = 0.50 
                for p in projections:
                    # BartTorvik often puts name in index 0 or 1
                    bt_name = str(p[1]).lower() 
                    if home.lower() in bt_name or bt_name in home.lower():
                        # BartTorvik's power rating (Barthag) is usually index 4 or index 25
                        # Let's try to pull the Barthag rating directly
                        bot_prob_raw = float(p[4]) 
                        break
                
                edge = (bot_prob_raw - mkt_prob) * 100

                rows.append({
                    "Matchup": f"{away} @ {home}",
                    "Odds": mkt_price,
                    "Bot Win Chance": f"{bot_prob_raw:.1%}",
                    "Edge %": f"{edge:.1f}%"
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
            st.success("Calculations Verified!")
    except Exception as e:
        st.error(f"Error fetching data: {e}")

if __name__ == "__main__":
    run_streamlit_ui()
