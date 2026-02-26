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
        with st.spinner("Bot is scouting teams..."):
            projections, odds = get_data(api_key) 
        
        # Guard against API error strings (the 'str' error fix)
        if not isinstance(odds, list):
            st.error("API Error: Check your key or quota in Streamlit Secrets.")
            return

        rows = []
        for game in odds:
            h_full = game.get('home_team', '')
            a_full = game.get('away_team', '')
            bookies = game.get('bookmakers', [])
            if not bookies: continue
            
            m = bookies[0].get('markets', [{}])[0]
            outcomes = m.get('outcomes', [{}, {}])
            mkt_price = outcomes[0].get('price', 0)
            mkt_prob = (abs(mkt_price)/(abs(mkt_price)+100)) if mkt_price < 0 else (100/(mkt_price+100))
            
            # --- THE SUPER MATCHER ---
            h_rank, a_rank = 0.5, 0.5
            # Clean names (remove "Tigers", "Bulldogs", etc. to find core school)
            h_core = h_full.split(' ')[0].lower() 
            a_core = a_full.split(' ')[0].lower()

            for p in projections:
                bt_name = str(p[1]).lower()
                if h_core in bt_name or bt_name in h_full.lower():
                    # Scan row for the Barthag decimal (usually index 8 for 2026)
                    h_rank = next((float(x) for x in p if isinstance(x, (int, float)) and 0.1 < float(x) < 0.99), 0.5)
                if a_core in bt_name or bt_name in a_full.lower():
                    a_rank = next((float(x) for x in p if isinstance(x, (int, float)) and 0.1 < float(x) < 0.99), 0.5)

            # Log5 Win Probability
            denom = (h_rank + a_rank - (2 * h_rank * a_rank))
            win_prob = (h_rank - (h_rank * a_rank)) / denom if denom != 0 else 0.5
            edge = (win_prob - mkt_prob) * 100

            rows.append({
                "Matchup": f"{a_full} @ {h_full}",
                "Odds": mkt_price,
                "Bot Win %": f"{win_prob:.1%}",
                "Edge %": f"{edge:.1f}%"
            })

        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            st.success(f"Successfully matched {len(rows)} games!")
        else:
            st.info("No games found. The API might be empty for tonight.")

    except Exception as e:
        st.error(f"Critical Error: {e}")

if __name__ == "__main__":
    run_streamlit_ui()
