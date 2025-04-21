import streamlit as st
import pandas as pd
import requests
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Whist Game Viewer", layout="wide")
st.title("Whist Game Viewer")


st.subheader("Refreshes every minute :material/update:")
if st.button("Refresh now :material/update:"):
    st.rerun()

# Auto-refresh every 60 seconds
st_autorefresh(interval=60 * 1000, limit=None, key="datarefresh")


# Get game ID from URL
query_params = st.query_params
game_id = query_params.get("game_id", [None])

if not game_id:
    st.error("No game ID provided in the URL.")
    st.stop()

# Fetch game data
url = f"https://gameviewer.nathanamery.workers.dev?game_id={game_id}"
try:
    res = requests.get(url)
    if res.status_code == 404:
        st.warning("Game not found yet. Waiting for scores...")
        st.stop()
    elif res.status_code != 200:
        st.error(f"Error fetching game data: {res.text}")
        st.stop()
    data = res.json()
except Exception as e:
    st.error("Failed to fetch data.")
    st.exception(e)
    st.stop()

ROUNDS = list(range(7, 0, -1)) + list(range(2, 8))
SUITS = ["Hearts ♥️", "Clubs ♣️", "Diamonds ♦️", "Spades ♠️", "No Trumps 🙅🏻"]
PLAYERS = ["Campbell", "Russell", "Nathan", "Dave"]

rounds = [f"{ROUNDS[i]} {SUITS[i % len(SUITS)]}" for i in range(len(data))]
df = pd.DataFrame(index=rounds)
for p in PLAYERS:
    df[(p, "Guess")] = [r[p]["guess"] for r in data]
    df[(p, "Score")] = [r[p]["score"] for r in data]

df.columns = pd.MultiIndex.from_product([PLAYERS, ["Guess", "Score"]])

# Add total row
totals = {(p, "Guess"): "" for p in PLAYERS}
final_scores = {}
for p in PLAYERS:
    total = df[(p, "Score")].sum()
    totals[(p, "Score")] = total
    final_scores[p] = total
df.loc["Total"] = totals

st.dataframe(df, use_container_width=True, height=560)