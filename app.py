import requests
import streamlit as st

# =============================
# CONFIG
# =============================
API_BASE = "https://movie-rec-466x.onrender.com"
# API_BASE = "http://127.0.0.1:8000"

TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# =============================
# RED + BLUE PRODUCTION UI
# =============================
st.markdown("""
<style>

/* ===== GLOBAL ===== */
html, body, [class*="css"] {
    background-color: #0f0f0f !important;
    color: #ffffff !important;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

/* ===== Animated Title ===== */
h1 {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(90deg, #ff0000, #0066ff, #ff0000);
    background-size: 200% auto;
    -webkit-background-clip: text;
    color: transparent;
    animation: shine 6s linear infinite;
}

@keyframes shine {
    to { background-position: 200% center; }
}

/* ===== Sidebar ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#1a1a1a,#111);
    border-right: 2px solid #0066ff;
}

/* ===== Card ===== */
.card {
    background: rgba(255,255,255,0.04);
    border-radius: 18px;
    padding: 12px;
    border: 1px solid rgba(0,102,255,0.25);
    transition: all 0.35s ease;
}

.card:hover {
    transform: translateY(-6px) scale(1.03);
    box-shadow: 0 15px 35px rgba(0,102,255,0.35);
    border: 1px solid #0066ff;
}

.movie-title {
    font-size: 0.9rem;
    line-height: 1.15rem;
    height: 2.3rem;
    overflow: hidden;
    margin-top: 6px;
    font-weight: 500;
}

.small-muted {
    color:#3399ff;
    font-size: 0.92rem;
}

/* ===== Buttons ===== */
.stButton>button {
    background: linear-gradient(90deg,#ff0000,#0066ff);
    color: white;
    font-weight: 700;
    border-radius: 30px;
    border: none;
    transition: 0.3s ease;
}

.stButton>button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 18px rgba(0,102,255,0.7);
}

/* ===== Inputs ===== */
div[data-baseweb="select"] > div,
input {
    background-color: #1c1c1c !important;
    color: white !important;
    border-radius: 12px !important;
    border: 1px solid rgba(0,102,255,0.3) !important;
}

/* ===== Divider ===== */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(to right, transparent, #0066ff, transparent);
    margin: 1.5rem 0;
}

</style>
""", unsafe_allow_html=True)

# =============================
# STATE + ROUTING
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

qp_view = st.query_params.get("view")
qp_id = st.query_params.get("id")

if qp_view in ("home", "details"):
    st.session_state.view = qp_view

if qp_id:
    try:
        st.session_state.selected_tmdb_id = int(qp_id)
        st.session_state.view = "details"
    except:
        pass


def goto_home():
    st.session_state.view = "home"
    st.query_params.clear()
    st.query_params["view"] = "home"
    st.rerun()


def goto_details(tmdb_id: int):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = int(tmdb_id)
    st.query_params["view"] = "details"
    st.query_params["id"] = str(int(tmdb_id))
    st.rerun()

# =============================
# API
# =============================
@st.cache_data(ttl=30)
def api_get_json(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}"
        return r.json(), None
    except Exception as e:
        return None, f"Request failed: {e}"

# =============================
# TFIDF FIX FUNCTION (IMPORTANT)
# =============================
def to_cards_from_tfidf_items(tfidf_items):
    cards = []

    for x in tfidf_items or []:

        # CASE 1: nested format (old backend)
        if "tmdb" in x:
            tmdb = x.get("tmdb") or {}
            if tmdb.get("tmdb_id"):
                cards.append({
                    "tmdb_id": tmdb["tmdb_id"],
                    "title": tmdb.get("title") or x.get("title") or "Untitled",
                    "poster_url": tmdb.get("poster_url"),
                })

        # CASE 2: flat format (new backend)
        elif x.get("tmdb_id"):
            cards.append({
                "tmdb_id": x.get("tmdb_id"),
                "title": x.get("title") or "Untitled",
                "poster_url": x.get("poster_url"),
            })

    return cards

# =============================
# GRID
# =============================
def poster_grid(cards, cols=6, key_prefix="grid"):
    if not cards:
        st.info("No movies to show.")
        return

    rows = (len(cards) + cols - 1) // cols
    idx = 0

    for r in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards):
                break

            m = cards[idx]
            idx += 1

            tmdb_id = m.get("tmdb_id")
            title = m.get("title", "Untitled")
            poster = m.get("poster_url")

            with colset[c]:
                st.markdown("<div class='card'>", unsafe_allow_html=True)

                if poster:
                    st.image(poster, width="stretch")
                else:
                    st.write("🖼️ No poster")

                if st.button("Open", key=f"{key_prefix}_{r}_{c}_{idx}_{tmdb_id}"):
                    if tmdb_id:
                        goto_details(tmdb_id)

                st.markdown(
                    f"<div class='movie-title'>{title}</div>",
                    unsafe_allow_html=True
                )

                st.markdown("</div>", unsafe_allow_html=True)

# =============================
# SEARCH PARSER (UNCHANGED)
# =============================
def parse_tmdb_search_to_cards(data, keyword: str, limit: int = 24):
    keyword_l = keyword.strip().lower()

    if isinstance(data, dict) and "results" in data:
        raw = data.get("results") or []
        raw_items = []
        for m in raw:
            title = (m.get("title") or "").strip()
            tmdb_id = m.get("id")
            poster_path = m.get("poster_path")
            if not title or not tmdb_id:
                continue
            raw_items.append({
                "tmdb_id": int(tmdb_id),
                "title": title,
                "poster_url": f"{TMDB_IMG}{poster_path}" if poster_path else None,
                "release_date": m.get("release_date", "")
            })

    elif isinstance(data, list):
        raw_items = []
        for m in data:
            tmdb_id = m.get("tmdb_id") or m.get("id")
            title = (m.get("title") or "").strip()
            poster_url = m.get("poster_url")
            if not title or not tmdb_id:
                continue
            raw_items.append({
                "tmdb_id": int(tmdb_id),
                "title": title,
                "poster_url": poster_url,
                "release_date": m.get("release_date", "")
            })
    else:
        return [], []

    matched = [x for x in raw_items if keyword_l in x["title"].lower()]
    final_list = matched if matched else raw_items

    suggestions = []
    for x in final_list[:10]:
        year = (x.get("release_date") or "")[:4]
        label = f"{x['title']} ({year})" if year else x["title"]
        suggestions.append((label, x["tmdb_id"]))

    cards = [
        {"tmdb_id": x["tmdb_id"], "title": x["title"], "poster_url": x["poster_url"]}
        for x in final_list[:limit]
    ]

    return suggestions, cards

# =============================
# SIDEBAR (UNCHANGED)
# =============================
with st.sidebar:
    st.markdown("## 🎬 Menu")
    if st.button("🏠 Home"):
        goto_home()

    st.markdown("---")
    st.markdown("### 🏠 Home Feed (only home)")
    home_category = st.selectbox(
        "Category",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"],
        index=0,
    )
    grid_cols = st.slider("Grid columns", 4, 8, 6)

# =============================
# HEADER
# =============================
st.title("🎬 Movie Recommender")
st.markdown(
    "<div class='small-muted'>Type keyword → dropdown suggestions + matching results → open → details + recommendations</div>",
    unsafe_allow_html=True,
)
st.divider()

# ==========================================================
# HOME VIEW
# ==========================================================
if st.session_state.view == "home":

    typed = st.text_input(
        "Search by movie title (keyword)",
        placeholder="Type: avenger, batman, love..."
    )

    st.divider()

    if typed.strip():
        if len(typed.strip()) < 2:
            st.caption("Type at least 2 characters for suggestions.")
        else:
            data, err = api_get_json("/tmdb/search", params={"query": typed.strip()})

            if err or data is None:
                st.error(f"Search failed: {err}")
            else:
                suggestions, cards = parse_tmdb_search_to_cards(
                    data, typed.strip(), limit=24
                )

                if suggestions:
                    labels = ["-- Select a movie --"] + [s[0] for s in suggestions]
                    selected = st.selectbox("Suggestions", labels, index=0)

                    if selected != "-- Select a movie --":
                        label_to_id = {s[0]: s[1] for s in suggestions}
                        goto_details(label_to_id[selected])

                st.markdown("### Results")
                poster_grid(cards, cols=grid_cols, key_prefix="search_results")

        st.stop()

    st.markdown(f"### 🏠 Home — {home_category.replace('_',' ').title()}")

    home_cards, err = api_get_json(
        "/home",
        params={"category": home_category, "limit": 24}
    )

    if err or not home_cards:
        st.error(f"Home feed failed: {err or 'Unknown error'}")
        st.stop()

    poster_grid(home_cards, cols=grid_cols, key_prefix="home_feed")

# ==========================================================
# DETAILS VIEW
# ==========================================================
elif st.session_state.view == "details":

    tmdb_id = st.session_state.selected_tmdb_id

    if not tmdb_id:
        st.warning("No movie selected.")
        if st.button("← Back to Home"):
            goto_home()
        st.stop()

    a, b = st.columns([3, 1])
    with a:
        st.markdown("### 📄 Movie Details")
    with b:
        if st.button("← Back to Home"):
            goto_home()

    data, err = api_get_json(f"/movie/id/{tmdb_id}")

    if err or not data:
        st.error(f"Could not load details: {err or 'Unknown error'}")
        st.stop()

    left, right = st.columns([1, 2.4], gap="large")

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        if data.get("poster_url"):
            st.image(data["poster_url"], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"## {data.get('title','')}")
        release = data.get("release_date") or "-"
        genres = ", ".join([g["name"] for g in data.get("genres", [])]) or "-"
        st.markdown(f"<div class='small-muted'>Release: {release}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='small-muted'>Genres: {genres}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### Overview")
        st.write(data.get("overview") or "No overview available.")
        st.markdown("</div>", unsafe_allow_html=True)

    if data.get("backdrop_url"):
        st.markdown("#### Backdrop")
        st.image(data["backdrop_url"], use_container_width=True)

    st.divider()
    st.markdown("### ✅ Recommendations")

    title = (data.get("title") or "").strip()

    if title:
        bundle, err2 = api_get_json(
            "/movie/search",
            params={"query": title, "tfidf_top_n": 12, "genre_limit": 12},
        )

        if not err2 and bundle:

            st.markdown("#### 🔎 Similar Movies")

            tfidf_cards = to_cards_from_tfidf_items(
                bundle.get("tfidf_recommendations")
            )

            poster_grid(
                tfidf_cards,
                cols=grid_cols,
                key_prefix="details_tfidf"
            )

            st.markdown("#### 🎭 More Like This")

            poster_grid(
                bundle.get("genre_recommendations", []),
                cols=grid_cols,
                key_prefix="details_genre"
            )