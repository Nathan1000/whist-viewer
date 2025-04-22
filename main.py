import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh
import copy

st.set_page_config(page_title="Whist Game Viewer", layout="wide")
st.title("Whist Game Viewer")

st.write("Updates every 10 seconds :material/update:")
if st.button("Update now :material/update:"):
    st.rerun()

# Auto-refresh every 20 seconds
st_autorefresh(interval=10 * 1000, limit=None, key="datarefresh")

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
        st.warning("Welcome to the game, contender.\nWaiting for scores...")
        st.stop()
    elif res.status_code != 200:
        st.error(f"Error fetching game data: {res.text}")
        st.stop()
    data = res.json()
except Exception as e:
    st.error("Failed to fetch data.")
    st.exception(e)
    st.stop()

#st.write(data) #for debugging

ROUNDS = list(range(7, 0, -1)) + list(range(2, 8))
SUITS = ["Hearts ♥️", "Clubs ♣️", "Diamonds ♦️", "Spades ♠️", "No Trumps 🙅🏻"]
PLAYERS = ["Campbell", "Russell", "Nathan", "Dave"]

# Determine score data

round_num = data.get("round_num", 0)



# Preserve or initialize scores_by_round
if "cached_scores" not in st.session_state:
    st.session_state.cached_scores = []

incoming = data.get("scores_by_round")
if incoming:
    scores_by_round = incoming
    st.session_state.cached_scores = incoming  # update cache
else:
    scores_by_round = copy.deepcopy(st.session_state.cached_scores)

# Only process guesses if present and round_num is valid
if data.get("guesses") and round_num >= 0:
    # Pad if necessary
    while len(scores_by_round) <= round_num:
        scores_by_round.append({player: {"guess": None, "score": None} for player in PLAYERS})

    for player in PLAYERS:
        if scores_by_round[round_num][player].get("score") is None:
            scores_by_round[round_num][player]["guess"] = data["guesses"].get(player, None)

rounds = [f"{ROUNDS[i]} {SUITS[i % len(SUITS)]}" for i in range(len(scores_by_round))]
df = pd.DataFrame(index=rounds)
for p in PLAYERS:
    df[(p, "Guess")] = [r[p].get("guess", "—") for r in scores_by_round]
    df[(p, "Score")] = [r[p].get("score", "") for r in scores_by_round]

df.columns = pd.MultiIndex.from_product([PLAYERS, ["Guess", "Score"]])


# Totals
totals = {(p, "Guess"): "" for p in PLAYERS}
final_scores = {}
for p in PLAYERS:
    total = sum(r.get(p, {}).get("score", 0) or 0 for r in scores_by_round)
    totals[(p, "Score")] = total
    final_scores[p] = total
df.loc["Total"] = totals

if isinstance(data, dict):
    round_num = data.get("round_num", 0)
    dealer = data.get("dealer", "")
    guesses = data.get("guesses", {})

    if round_num < len(ROUNDS):
        cards_this_round = ROUNDS[round_num]
        suit_this_round = SUITS[round_num % len(SUITS)]
    else:
        cards_this_round = "—"
        suit_this_round = "—"

    if round_num == 9:
        st.subheader(f"Round {round_num + 1} | {cards_this_round} Cards | {suit_this_round}")
        st.info("Ian's Favourite Round!", icon=":material/info:")
    elif round_num == 4:
        st.subheader(f"Round {round_num + 1} | {cards_this_round} Cards | {suit_this_round}")
        st.info("Ian's second Favourite Round!", icon=":material/info:")
    elif round_num == 13:
        st.subheader("🏁 Game Over!")
    else:
        st.subheader(f"Round {round_num + 1} | {cards_this_round} Cards | {suit_this_round}")

    if suit_this_round.startswith("Diamonds") and dealer == "Dave":
        dealer_display = "It's...♦️Diamond♦️ Dave!"
    else:
        dealer_display = dealer
    if round_num < 13:
        st.badge(f"Dealer: {dealer_display}", icon=":material/hand_gesture:", color="green")

# Show guesses if present and scores not yet submitted for this round
with st.expander("Guesses", expanded=True, icon=":material/psychology_alt:"):
    if round_num < len(scores_by_round):
        pending_round = scores_by_round[round_num]
        if any(p.get("guess") is not None for p in pending_round.values()) and all(p.get("score") is None for p in pending_round.values()):

            cols = st.columns(4)
            for i, player in enumerate(PLAYERS):
                guess = pending_round[player].get("guess")
                if guess is not None:
                    cols[i].metric(label=player, value=guess)


# Show final rankings if game is over
if len(scores_by_round) >= len(ROUNDS):
    winner = max(final_scores, key=final_scores.get)
    st.subheader(f"{winner} wins with {final_scores[winner]} points!")

    st.subheader("🏆 Final Rankings")
    sorted_scores = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    rankings, last_score, current_rank, offset = [], None, 0, 1
    for player, score in sorted_scores:
        if score != last_score:
            current_rank = offset
        rankings.append((current_rank, player, score))
        last_score = score
        offset += 1
    for rank, player, score in rankings:
        st.markdown(f"**{rank}. {player}** – {score} points")
st.dataframe(df, use_container_width=True, height=560)








if game_id:
    st.markdown(
        f"<footer style='text-align: center; font-size: 0.75rem; color: gray;'>"
        f"Game ID: {game_id}</footer>",
        unsafe_allow_html=True
    )