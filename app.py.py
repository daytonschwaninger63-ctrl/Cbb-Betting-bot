import streamlit as st
import pandas as pd
import requests

def get_data(api_key):
    # Odds API Call
    odds_url = f"https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/?apiKey={api_key}&regions=us&markets=spreads"
    odds_resp = requests.get(odds_url).json()
    
    # BartTorvik Call
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
        with st.spinner("Decoding 2026 Power Rankings..."):
            projections, odds = get_data(api_key) 
        
        # FIX FOR 'STR' OBJECT ERROR: Check if 'odds' is actually a list
        if isinstance(odds, dict) and "errmsg" in str(odds).lower():
            st.error(f"API Error: {odds.get('message', 'Check your API Key/Quota')}")
            return

        if isinstance(odds, list) and len(odds) > 0:
            rows = []
            for game in odds:
                # Double check this is a dictionary before calling .get()
                if not isinstance(game, dict): continue
                
                h_full = game.get('home_team', 'Unknown')
                a_full = game.get('away_team', 'Unknown')
                bookies = game.get('bookmakers', [])
                if not bookies: continue
                
                m = bookies[0].get('markets', [{}])[0]
                outcomes = m.get('outcomes', [{}, {}])
                mkt_price = outcomes[0].get('price', 0)
                mkt_prob = (abs(mkt_price)/(abs(mkt_price)+100)) if mkt_price < 0 else (100/(mkt_price+100))
                
                # Dynamic matching for 2026 Data
                h_rank, a_rank = 0.5, 0.5
                for p in projections:
                    bt_name = str(p[1]).lower()
                    if h_full.lower() in bt_name or bt_name in h_full.lower():
                        h_rank = float(p[8]) # Index 8 for 2026 Barthag
                    if a_full.lower() in bt_name or bt_name in a_full.lower():
                        a_rank = float(p[8])

                # Log5 Math
                denom = (h_rank + a_rank - (2 * h_rank * a_rank))
                win_prob = (h_rank - (h_rank * a_rank)) / denom if denom != 0 else 0.5
                edge = (win_prob - mkt_prob) * 100

                rows.append({
                    "Matchup": f"{a_full} @ {h_full}",
                    "Odds": mkt_price,
                    "Bot Win %": f"{win_prob:.1%}",
                    "Edge %": f"{edge:.1f}%"
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
            st.success("Analysis Live!")
        else:
            st.info("No live games found at the moment.")

    except Exception as e:
        st.error(f"App Error: {e}")

if __name__ == "__main__":
    run_streamlit_ui()
