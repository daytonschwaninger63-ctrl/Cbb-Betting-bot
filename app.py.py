import streamlit as st
import pandas as pd
import requests

# This helps the bot find teams even if the names are slightly different
TEAM_MAP = {
    "Saint Mary's Gaels": "St. Mary's",
    "Ole Miss Rebels": "Mississippi",
    "UConn Huskies": "Connecticut",
    "NC State Wolfpack": "N.C. State",
    "Miami (FL) Hurricanes": "Miami FL",
    "Saint Joseph's Hawks": "St. Joseph's"
}

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
                mkt_prob = (abs(mkt_price)/(abs(mkt_price)+100)) if mkt_price < 0 else (100/(mkt_price+100))
                
                # Real Bot Probability Logic
                mapped_name = TEAM_MAP.get(home, home)
                # This searches the BartTorvik data (column 1 is team name, column 25 is win prob)
                bot_prob_raw = next((p[25] for p in projections if mapped_name.lower() in p[1].lower()), 50.0)
                bot_prob = float(bot_prob_raw) / 100
                
                edge = (bot_prob - mkt_prob) * 100

                rows.append({
                    "Matchup": f"{away} @ {home}",
                    "Odds": mkt_price,
                    "Bot %": f"{bot_prob:.1%}",
                    "Edge %": f"{edge:.1f}%"
                })

            df = pd.DataFrame(rows)
            # Using st.dataframe for a clean, sortable table
            st.dataframe(df, use_container_width=True)
            st.success("Analysis Complete!")
    except Exception as e:
        st.error(f"Error: {e}")

if __name__ == "__main__":
    run_streamlit_ui()
