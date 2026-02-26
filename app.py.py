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
        with st.spinner("Forcing Data Match..."):
            projections, odds = get_data(api_key) 
        
        if odds:
            rows = []
            for game in odds:
                h_full = game.get('home_team')
                a_full = game.get('away_team')
                bookies = game.get('bookmakers', [])
                if not bookies: continue
                
                m = bookies[0].get('markets', [{}])[0]
                outcomes = m.get('outcomes', [{}, {}])
                mkt_price = outcomes[0].get('price', 0)
                mkt_prob = (abs(mkt_price)/(abs(mkt_price)+100)) if mkt_price < 0 else (100/(mkt_price+100))
                
                # --- BRUTE FORCE MATCHING ---
                h_rank, a_rank = 0.5, 0.5
                h_short = h_full[:5].lower() # Just use first 5 letters
                a_short = a_full[:5].lower()

                for p in projections:
                    bt_name = str(p[1]).lower()
                    if h_short in bt_name:
                        h_rank = float(p[8])
                    if a_short in bt_name:
                        a_rank = float(p[8])

                # Math
                win_prob = (h_rank - h_rank * a_rank) / (h_rank + a_rank - 2 * h_rank * a_rank)
                edge = (win_prob - mkt_prob) * 100

                rows.append({
                    "Matchup": f"{a_full} @ {h_full}",
                    "Odds": mkt_price,
                    "Bot Win %": f"{win_prob:.1%}",
                    "Edge %": f"{edge:.1f}%"
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
            
            # Debugging Help
            if len(df) > 0 and "50.0%" in df['Bot Win %'].values[0]:
                st.warning("Bot is still defaulting to 50%. This usually means the data columns shifted again.")
            else:
                st.success("Data Match Successful!")
                
    except Exception as e:
        st.error(f"Error: {e}")

if __name__ == "__main__":
    run_streamlit_ui()
