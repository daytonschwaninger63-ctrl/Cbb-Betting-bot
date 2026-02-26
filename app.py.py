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
        with st.spinner("Analyzing real-time value..."):
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
                
                # Convert American Odds to Probability
                if mkt_price < 0:
                    mkt_prob = abs(mkt_price) / (abs(mkt_price) + 100)
                else:
                    mkt_prob = 100 / (mkt_price + 100)
                
                # SMARTER MATCHING: Search for the team name within the BartTorvik string
                # BartTorvik team name is usually in index [1], Win Prob in index [25]
                bot_prob_raw = 50.0 # Default
                for p in projections:
                    if home.lower() in p[1].lower() or p[1].lower() in home.lower():
                        bot_prob_raw = float(p[25])
                        break
                
                bot_prob = bot_prob_raw / 100
                edge = (bot_prob - mkt_prob) * 100

                rows.append({
                    "Matchup": f"{away} @ {home}",
                    "Odds": mkt_price,
                    "Bot %": f"{bot_prob:.1%}",
                    "Edge %": f"{edge:.1f}%"
                })

            df = pd.DataFrame(rows)
            # Use st.dataframe for a clean, error-free interactive table
            st.dataframe(df, use_container_width=True)
            st.success("Analysis Complete!")
    except Exception as e:
        st.error(f"Error: {e}")

if __name__ == "__main__":
    run_streamlit_ui()
