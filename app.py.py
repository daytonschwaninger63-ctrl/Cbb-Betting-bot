import streamlit as st
import pandas as pd
import requests

def get_data(api_key):
    odds_url = f"https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/?apiKey={api_key}&regions=us&markets=spreads"
    odds_resp = requests.get(odds_url).json()
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
        with st.spinner("Calculating Real-Time Value..."):
            projections, odds = get_data(api_key) 
        
        if odds:
            rows = []
            for game in odds:
                home_name = game.get('home_team')
                away_name = game.get('away_team')
                bookies = game.get('bookmakers', [])
                if not bookies: continue
                
                # Get Market Odds
                m = bookies[0].get('markets', [{}])[0]
                outcomes = m.get('outcomes', [{}, {}])
                mkt_price = outcomes[0].get('price', 0)
                mkt_prob = (abs(mkt_price)/(abs(mkt_price)+100)) if mkt_price < 0 else (100/(mkt_price+100))
                
                # FIND BOTH TEAMS IN BARTTORVIK DATA
                home_rank = next((float(p[4]) for p in projections if home_name.lower() in str(p[1]).lower() or str(p[1]).lower() in home_name.lower()), 0.5)
                away_rank = next((float(p[4]) for p in projections if away_name.lower() in str(p[1]).lower() or str(p[1]).lower() in away_name.lower()), 0.5)
                
                # THE FORMULA: Log5 win probability (Home vs Away)
                # This is the actual math used by Vegas and BartTorvik
                win_prob = (home_rank - home_rank * away_rank) / (home_rank + away_rank - 2 * home_rank * away_rank)
                
                edge = (win_prob - mkt_prob) * 100

                rows.append({
                    "Matchup": f"{away_name} @ {home_name}",
                    "Market Odds": mkt_price,
                    "Bot Win %": f"{win_prob:.1%}",
                    "Edge %": f"{edge:.1f}%"
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
            st.success("Analysis Live!")
    except Exception as e:
        st.error(f"Error: {e}")

if __name__ == "__main__":
    run_streamlit_ui()
