import streamlit as st
import pandas as pd
import requests
import sys

# Line 5: The Team Name Mapper
TEAM_MAP = {
    "California Golden Bears": "California",
    "Saint Mary's Gaels": "St. Mary's",
    "Oregon St Beavers": "Oregon St.",
    "Loyola Marymount Lions": "Loyola Marymount",
    "Wisconsin Badgers": "Wisconsin",
    "San Diego St Aztecs": "San Diego St.",
    "St. Bonaventure Bonnies": "St. Bonaventure",
    "Ole Miss Rebels": "Mississippi",
    "UConn Huskies": "Connecticut",
    "NC State Wolfpack": "N.C. State",
    "Miami (FL) Hurricanes": "Miami FL",
    "Texas A&M Aggies": "Texas A&M",
    "Saint Joseph's Hawks": "St. Joseph's",
    "Florida Intl Golden Panthers": "FIU",
    "UL Monroe Warhawks": "ULM"
}

def get_data(api_key):
    # Fetch Live Odds
    odds_url = f"https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/?apiKey={api_key}&regions=us&markets=spreads"
    odds_resp = requests.get(odds_url).json()
    
    # Placeholder for BartTorvik Data (to be expanded in next phase)
    sample_projections = [
        {"team": "Oregon", "win_prob": 62.5}, 
        {"team": "Wisconsin", "win_prob": 45.0},
        {"team": "St. Mary's", "win_prob": 58.0}
    ]
    return sample_projections, odds_resp

def run_streamlit_ui():
    st.set_page_config(page_title="CBB Value Finder", layout="wide")
    st.title("🏀 CBB Value Finder")

    try:
        api_key = st.secrets["THE_ODDS_API_KEY"]
        with st.spinner("Analyzing Market Edges..."):
            projections, odds = get_data(api_key) 
        
        if odds:
            rows = []
            for game in odds:
                home, away = game.get('home_team'), game.get('away_team')
                bookies = game.get('bookmakers', [])
                if not bookies: continue
                
                # Market Probability Math
                outcomes = bookies[0].get('markets', [{}])[0].get('outcomes', [{}, {}])
                mkt_price = outcomes[0].get('price', 0)
                mkt_prob = (abs(mkt_price)/(abs(mkt_price)+100)) if mkt_price < 0 else (100/(mkt_price+100))
                
                # Step 2 Logic: Match names and calculate real Edge
                mapped_name = TEAM_MAP.get(home, home)
                bot_prob = next((p['win_prob']/100 for p in projections if p['team'] in mapped_name), 0.50)
                edge = (bot_prob - mkt_prob) * 100

                rows.append({
                    "Matchup": f"{away} @ {home}", 
                    "Odds": mkt_price, 
                    "Edge %": f"{edge:.1f}%"
                })

            df = pd.DataFrame(rows)
            # Styling the dataframe with a green gradient for positive edges
            st.dataframe(df.style.background_gradient(subset=['Edge %'], cmap='Greens'), use_container_width=True)
            st.success("Analysis Complete!")
    except Exception as e:
        st.error(f"Error: {e}")

if __name__ == "__main__":
    run_streamlit_ui()
