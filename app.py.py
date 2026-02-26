import streamlit as st
import pandas as pd
import requests
import sys

# The Mapper: Fixes names like "Ole Miss" vs "Mississippi"
TEAM_MAP = {
    "California Golden Bears": "California",
    "Saint Mary's Gaels": "St. Mary's",
    "Oregon St Beavers": "Oregon St.",
    "Loyola Marymount Lions": "Loyola Marymount",
    "Wisconsin Badgers": "Wisconsin",
    "San Diego St Aztecs": "San Diego St.",
    "Ole Miss Rebels": "Mississippi",
    "UConn Huskies": "Connecticut",
    "NC State Wolfpack": "N.C. State"
}

def get_data(api_key):
    # 1. Fetch live odds
    odds_url = f"https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/?apiKey={api_key}&regions=us&markets=spreads"
    odds_resp = requests.get(odds_url).json()
    
    # 2. Fetch BartTorvik projections
    # We use this URL to get the latest power rankings and win probabilities
    proj_url = "https://barttorvik.com/2026_data.json" 
    try:
        proj_resp = requests.get(proj_url).json()
    except:
        # Fallback if the site is down
        proj_resp = []
        
    return proj_resp, odds_resp

def run_streamlit_ui():
    st.set_page_config(page_title="CBB Value Finder", layout="wide")
    st.title("🏀 CBB Value Finder")

    try:
        api_key = st.secrets["THE_ODDS_API_KEY"]
        with st.spinner("Calculating live edges..."):
            projections, odds = get_data(api_key) 
        
        if odds:
            rows = []
            for game in odds:
                home = game.get('home_team')
                away = game.get('away_team')
                bookies = game.get('bookmakers', [])
                if not bookies: continue
                
                # Get Market Probability
                m = bookies[0].get('markets', [{}])[0]
                outcomes = m.get('outcomes', [{}, {}])
                mkt_price = outcomes[0].get('price', 0)
                mkt_prob = (abs(mkt_price)/(abs(mkt_price)+100)) if mkt_price < 0 else (100/(mkt_price+100))
                
                # Look up Bot Probability using Mapper
                mapped_name = TEAM_MAP.get(home, home)
                # This searches the real BartTorvik data for a matching team name
                bot_prob = next((float(p[25])/100 for p in projections if mapped_name in p[1]), 0.50)
                
                edge = (bot_prob - mkt_prob) * 100

                rows.append({
                    "Matchup": f"{away} @ {home}",
                    "Odds": mkt_price,
                    "Bot %": f"{bot_prob:.1%}",
                    "Edge %": round(edge, 1)
                })

            df = pd.DataFrame(rows)
            # This color-codes the Edge column
            st.dataframe(df.style.background_gradient(subset=['Edge %'], cmap='RdYlGn'), use_container_width=True)
            st.success("Calculations Complete!")
            
    except Exception as e:
        st.error(f"Error: {e}")

if __name__ == "__main__":
    run_streamlit_ui()
