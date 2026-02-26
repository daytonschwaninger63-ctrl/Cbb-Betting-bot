import streamlit as st
import pandas as pd
import requests

def get_data(api_key):
    odds_url = f"https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/?apiKey={api_key}/?apiKey={api_key}&regions=us&markets=spreads"
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
        with st.spinner("Decoding 2026 Power Rankings..."):
            projections, odds = get_data(api_key) 
        
        if odds:
            rows = []
            for game in odds:
                h_full = game.get('home_team')
                a_full = game.get('away_team')
                bookies = game.get('bookmakers', [])
                if not bookies: continue
                
                # Get Market Odds & Convert to Probability
                m = bookies[0].get('markets', [{}])[0]
                outcomes = m.get('outcomes', [{}, {}])
                mkt_price = outcomes[0].get('price', 0)
                mkt_prob = (abs(mkt_price)/(abs(mkt_price)+100)) if mkt_price < 0 else (100/(mkt_price+100))
                
                # --- DYNAMIC COLUMN SEARCH ---
                h_rank, a_rank = 0.5, 0.5
                for p in projections:
                    bt_name = str(p[1]).lower()
                    # Check if the team name matches (even partially)
                    if h_full.lower() in bt_name or bt_name in h_full.lower():
                        # Find the decimal between 0 and 1 in the row (the Barthag)
                        h_rank = next((float(val) for val in p if isinstance(val, (float, int)) and 0 < float(val) < 1), 0.5)
                    if a_full.lower() in bt_name or bt_name in a_full.lower():
                        a_rank = next((float(val) for val in p if isinstance(val, (float, int)) and 0 < float(val) < 1), 0.5)

                # Log5 Win Probability Formula
                # win_prob = (Home - Home * Away) / (Home + Away - 2 * Home * Away)
                denom = (h_rank + a_rank - (2 * h_rank * a_rank))
                win_prob = (h_rank - (h_rank * a_rank)) / denom if denom != 0 else 0.5
                
                edge = (win_prob - mkt_prob) * 100

                rows.append({
                    "Matchup": f"{a_full} @ {h_full}",
                    "Market Odds": mkt_price,
                    "Bot Win %": f"{win_prob:.1%}",
                    "Edge %": f"{edge:.1f}%"
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
            
            # Check if we actually found data
            if any(row["Bot Win %"] != "50.0%" for row in rows):
                st.success("✅ Real-time data match successful!")
            else:
                st.warning("⚠️ Still showing 50%. Attempting deep-search...")

    except Exception as e:
        st.error(f"Error: {e}")

if __name__ == "__main__":
    run_streamlit_ui()
