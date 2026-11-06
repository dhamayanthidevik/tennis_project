import os
from turtle import width
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import base64
from pathlib import Path

load_dotenv()


@st.cache_resource
def get_engine():
    """Create the database connection once and reuse it."""
    pw = quote_plus(os.getenv("DB_PASSWORD"))
    return create_engine(
        f"mysql+pymysql://{os.getenv('DB_USER')}:{pw}"
        f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )


@st.cache_data(ttl=600)
def run_query(sql,params=None):
    """Run a SQL query and return a DataFrame (cached for 10 minutes)."""
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)
    
# st.set_page_config(page_title="Tennis Rankings Explorer", layout="wide")
# 1. Page config
st.set_page_config(page_title="Tennis Rankings Explorer", page_icon="🎾", layout="wide")
BASE_DIR = Path(__file__).parent

@st.cache_data
def get_base64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()

def set_background(image_path):
    encoded = get_base64(image_path)
    css = (BASE_DIR / "styles.css").read_text(encoding="utf-8")
    css = css.replace("__BG_IMAGE__", encoded)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

set_background(BASE_DIR.parent / "image" / "bgblue.jpg")
PAGES = [
    "Home Dashboard",
    "Competitor Explorer",
    "Competitor Details",
    "Country Analysis",
    "Leaderboards",
    "Competitions & Venues",
    "SQL Insights",
]

def get_metric(query, default=0):
    """Run a query that returns one value and return that value."""
    df = run_query(query)  # your helper that returns a DataFrame
    if df.empty or df.iloc[0, 0] is None:
        return default
    return df.iloc[0, 0]

def show_home():
    """Home dashboard: summary metrics and a quick overview."""
    st.title("Tennis Rankings Explorer")
    st.write("Explore doubles rankings, countries, competitions and venues.")
    try:
        total_competitors = get_metric("SELECT COUNT(*) FROM competitors")
        total_competitions = get_metric("SELECT COUNT(*) FROM competitions")
        total_venues = get_metric("SELECT COUNT(*) FROM venues")
        total_countries = get_metric("SELECT COUNT(DISTINCT country_code) FROM competitors")
    except Exception as e:
        st.error(f"Could not load summary metrics: {e}")
        return  
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Competitors", total_competitors)
    col2.metric("Total Competitions", total_competitions)
    col3.metric("Total Venues", total_venues)
    col4.metric("Total Countries", total_countries)
    
    left, right = st.columns(2)
    with left:
        show_top_countries_chart()
    with right:
        show_competition_types_chart()
    
    show_top_competitors_table()

def show_top_countries_chart():
    """Bar chart of the top 10 countries by number of competitors."""
    st.subheader("Top 10 countries")

    query = """
        SELECT country, COUNT(*) AS competitors
        FROM Competitors
        WHERE country IS NOT NULL
        GROUP BY country
        ORDER BY competitors DESC
        LIMIT 10
    """

    try:
        df = run_query(query)
    except Exception as e:
        st.error(f"Could not load country data: {e}")
        return

    if df.empty:
        st.info("No country data available.")
        return

    st.bar_chart(df, x="country", y="competitors")
def show_top_competitors_table():
    """Table of the top 5 ranked competitors."""
    st.subheader("Top 5 ranked competitors")

    query = """
        SELECT r.`rank` AS 'Rank',
               c.name AS 'Name',
               c.country AS 'Country',
               r.points AS 'Points'
        FROM competitor_rankings r
        JOIN competitors c ON r.competitor_id = c.competitor_id
        ORDER BY r.`rank` ASC, r.points DESC
        LIMIT 5
    """

    try:
        df = run_query(query)
    except Exception as e:
        st.error(f"Could not load top competitors: {e}")
        return

    if df.empty:
        st.info("No ranking data available.")
        return

    # st.dataframe(df, hide_index=True, use_container_width=True)
    st.table(df.style.hide(axis="index"))
    st.caption("Full list on the Leaderboards page.")
    

def show_competition_types_chart():
    """Bar chart of the number of competitions by type."""
    st.subheader("Competitions by type")

    query = """
        SELECT type, COUNT(*) AS total
        FROM competitions
        WHERE type IS NOT NULL
        GROUP BY type
        ORDER BY total DESC
    """

    try:
        df = run_query(query)
    except Exception as e:
        st.error(f"Could not load competition types: {e}")
        return

    if df.empty:
        st.info("No competition data available.")
        return

    st.bar_chart(df, x="type", y="total")

@st.cache_data
def get_filter_options():
    """Return countries, genders and the min/max values for the sliders."""
    countries = run_query(
        "SELECT DISTINCT country FROM competitors ORDER BY country"
    )["country"].tolist()
    genders = run_query(
        "SELECT DISTINCT gender FROM competitor_rankings WHERE gender IS NOT NULL"
    )["gender"].tolist()
    limits = run_query(
        "SELECT MAX(`rank`) AS max_rank, MAX(points) AS max_points "
        "FROM competitor_rankings"
    )
    return countries, genders, int(limits.at[0, "max_rank"]), int(limits.at[0, "max_points"])

def show_explorer():
    """Search and filter competitors."""
    st.title("Competitor Explorer")

    try:
        countries, genders, max_rank, max_points = get_filter_options()
    except Exception as e:
        st.error(f"Could not load filter options: {e}")
        return

    name = st.text_input("Search by name")
    col1, col2 = st.columns(2)
    gender = col1.selectbox("Gender", ["All"] + genders)
    selected_countries = col2.multiselect("Country", countries)
    rank_range = st.slider("Rank range", 1, max_rank, (1, max_rank))
    # st.write("Rank range:", rank_range)
    min_points = st.slider("Minimum points", 0, max_points, 0)
    # st.write("min_points:", min_points)

    query = """
        SELECT r.`rank` AS 'Rank',
               c.name AS 'Name',
               c.country AS 'Country',
               r.gender AS 'Gender',
               r.tour AS 'Tour',
               r.points AS 'Points',
               r.movement AS 'Movement',
               r.competitions_played AS 'Competitions Played'
        FROM competitor_rankings r
        JOIN competitors c ON r.competitor_id = c.competitor_id
        WHERE r.`rank` BETWEEN :low AND :high
          AND r.points >= :min_points
    """
    params = {"low": rank_range[0], "high": rank_range[1], "min_points": min_points}

    if name:
        query += " AND c.name LIKE :name"
        params["name"] =f"%{name}%"
    if gender != "All":
        query += " AND r.gender = :gender"
        params["gender"]=f"%{gender}%" 
    if selected_countries:
        name = [f":c{i}" for i in range(len(selected_countries))]
        query += f" AND c.country IN ({', '.join(name)})"
        params.update({f"c{i}": c for i,c in enumerate(selected_countries)})
    query += " ORDER BY r.points DESC LIMIT 500"

    try:
        df = run_query(query, params)
    except Exception as e:
        st.error(f"Could not load competitors: {e}")
        return

    if df.empty:
        st.info("No competitors match your filters.")
        return
    
    df["Gender"] = df["Gender"].str.title()
    st.write(f"Showing {len(df)} competitors")
    # st.dataframe(df, hide_index=True, use_container_width=True)
    st.table(df.style.hide(axis="index"))
    st.write(f"Showing {len(df)} competitor{'s' if len(df) != 1 else ''}")

def show_details():
    """Competitor Details page: pick one player and show their ranking info."""
    st.title("Competitor Details")
 
    # 1. Dropdown data: names + IDs (IDs are unique, names may repeat)
    competitors = run_query(
        "SELECT competitor_id, name, country_code FROM competitors ORDER BY name"
    )
    if competitors.empty:
        st.warning("No competitors found in the database.")
        st.stop()
 
    # Label includes country code so duplicate names are distinguishable
    competitors["label"] = (
        competitors["name"] + " (" + competitors["country_code"] + ")"
    )
    label_to_id = dict(zip(competitors["label"], competitors["competitor_id"]))
 
    selected_label = st.selectbox("Select a competitor", list(label_to_id.keys()))
    competitor_id = label_to_id[selected_label]
 
    # 2. Details query: parameterized, newest ranking row first
    #    (%s is for mysql.connector / PyMySQL; use :id with SQLAlchemy text())
    sql = """
        SELECT c.name, c.country, c.country_code,
               r.`rank` AS current_rank, r.movement, r.points,
               r.competitions_played, r.tour, r.gender, r.year, r.week
        FROM competitors c
        JOIN competitor_rankings r ON c.competitor_id = r.competitor_id
        WHERE c.competitor_id = :cid
        ORDER BY r.year DESC, r.week DESC
    """
    df = run_query(sql, {"cid": competitor_id})
 
    if df.empty:
        st.warning("No ranking data found for this competitor.")
        st.stop()
 
    latest = df.iloc[0]  # most recent ranking row
 
    # 3. Header
    st.subheader(f"{latest['name']}  |  {latest['country']} ({latest['country_code']})")
    tour = latest["tour"] if pd.notna(latest["tour"]) else "N/A"
    gender = latest["gender"] if pd.notna(latest["gender"]) else "N/A"
    st.caption(f"Tour: {tour}  |  Gender: {gender}  |  Year {latest['year']}, Week {latest['week']}")
 
    # 4. Metric cards (movement shown as the delta: green up / red down)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rank", int(latest["current_rank"]), delta=int(latest["movement"]))
    col2.metric("Points", int(latest["points"]))
    col3.metric("Competitions Played", int(latest["competitions_played"]))
    col4.metric("Country", latest["country"])
 
    # 5. Optional: history, only if more than one ranking row exists
    if len(df) > 1:
        st.markdown("#### Ranking history")
        history = df.sort_values(["year", "week"]).copy()
        history["period"] = history["year"].astype(str) + "-W" + history["week"].astype(str).str.zfill(2)
        st.line_chart(history.set_index("period")[["points"]])
        with st.expander("Show history table"):
            # st.dataframe(
            #     history[["period", "current_rank", "movement", "points", "competitions_played"]],
            #     use_container_width=True,
            # )
            cols = ["period", "current_rank", "movement", "points", "competitions_played"]
            st.table(history[cols].reset_index(drop=True))
def show_country_analysis():
    """Country Analysis page: per-country competitor counts and points."""
    st.title("Country Analysis")
 
    # One row per competitor (their latest ranking), then aggregate by country.
    # ROW_NUMBER() needs MySQL 8+. Without it, see the note after this file.
    sql = """
        WITH latest AS (
            SELECT r.competitor_id, r.points,
                   ROW_NUMBER() OVER (
                       PARTITION BY r.competitor_id
                       ORDER BY r.year DESC, r.week DESC
                   ) AS rn
            FROM competitor_rankings r
        )
        SELECT c.country,
               c.country_code,
               COUNT(*)                  AS competitors,
               SUM(l.points)             AS total_points,
               ROUND(AVG(l.points), 1)   AS avg_points
        FROM competitors c
        JOIN latest l ON c.competitor_id = l.competitor_id AND l.rn = 1
        GROUP BY c.country, c.country_code
    """
    df = run_query(sql)
 
    if df.empty:
        st.warning("No country data available.")
        st.stop()
 
    # Controls
    col1, col2 = st.columns(2)
    sort_label = col1.radio(
        "Sort by",
        ["Number of competitors", "Average points", "Total points"],
        horizontal=True,
    )
    top_n = col2.selectbox("Show top", [5, 10, 15, 20], index=1)
 
    sort_col = {
        "Number of competitors": "competitors",
        "Average points": "avg_points",
        "Total points": "total_points",
    }[sort_label]
 
    df_sorted = df.sort_values(sort_col, ascending=False).reset_index(drop=True)
 
    # Summary metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Countries", len(df))
    m2.metric("Most competitors", df.loc[df["competitors"].idxmax(), "country"])
    m3.metric("Highest average points", df.loc[df["avg_points"].idxmax(), "country"])
 
    # Chart
    st.subheader(f"Top {top_n} countries by {sort_label.lower()}")
    chart_df = df_sorted.head(top_n).set_index("country")[[sort_col]]
    st.bar_chart(chart_df)
 
    # Table
    st.subheader("All countries")
    search = st.text_input("Search country")
    table = df_sorted
    if search:
        table = table[table["country"].str.contains(search, case=False, na=False)]
 
    if table.empty:
        st.info("No countries match your search.")
    else:
        st.caption(f"Showing {len(table)} countries")
        st.table(table.style.hide(axis="index"))
        # st.dataframe(table, use_container_width=True, hide_index=True)
        st.download_button(
            "Download as CSV",
            table.to_csv(index=False).encode("utf-8"),
            file_name="country_analysis.csv",
            mime="text/csv",
        )
ROW_OPTIONS = [5, 10, 20]

def _leaderboard_query(order_by: str, limit: int) -> str:
    """Build the leaderboard SQL: each player's latest ranking, sorted and limited.
 
    order_by must be one of the two fixed strings below (never user text).
    """
    allowed = {
        "rank": "l.`rank` ASC",
        "points": "l.points DESC",
    }
    order_clause = allowed[order_by]
    return f"""
        WITH latest AS (
            SELECT r.competitor_id, r.`rank`, r.movement, r.points,
                   r.competitions_played, r.year, r.week,
                   ROW_NUMBER() OVER (
                       PARTITION BY r.competitor_id
                       ORDER BY r.year DESC, r.week DESC
                   ) AS rn
            FROM competitor_rankings r
        )
        SELECT l.`rank` AS current_rank,
               c.name,
               c.country,
               l.points,
               l.movement,
               l.competitions_played
        FROM competitors c
        JOIN latest l ON c.competitor_id = l.competitor_id AND l.rn = 1
        ORDER BY {order_clause}, c.name
        LIMIT {int(limit)}
    """
 
 
def _render_board(order_by: str, limit: int, file_name: str):
    """Run one leaderboard query and display table, chart and download button."""
    df = run_query(_leaderboard_query(order_by, limit))
 
    if df.empty:
        st.warning("No leaderboard data available.")
        return
 
    df = df.rename(
        columns={
            "current_rank": "Rank",
            "name": "Competitor",
            "country": "Country",
            "points": "Points",
            "movement": "Movement",
            "competitions_played": "Competitions",
        }
    )
 
    st.caption(f"Showing top {len(df)} competitors")
    # st.dataframe(df, use_container_width=True, hide_index=True)
    st.table(df.style.hide(axis="index"))
 
    st.bar_chart(df.set_index("Competitor")[["Points"]])
 
    st.download_button(
        "Download as CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name=file_name,
        mime="text/csv",
        key=f"download_{order_by}",
    )
 
 
def show_leaderboards():
    """Leaderboards page: top ranked and highest points, in two tabs."""
    st.title("Leaderboards")
 
    top_n = st.selectbox("Rows to show", ROW_OPTIONS, index=1)
 
    tab_rank, tab_points = st.tabs(["Top Ranked", "Highest Points"])
 
    with tab_rank:
        st.subheader(f"Top {top_n} by rank")
        _render_board("rank", top_n, "top_ranked.csv")
 
    with tab_points:
        st.subheader(f"Top {top_n} by points")
        _render_board("points", top_n, "highest_points.csv")
import streamlit as st

# Uses your existing cached helper:
#   run_query(sql: str, params: dict | None = None) -> pd.DataFrame
# from db import run_query

LATEST_PER_COMPETITOR_SQL = """
    WITH latest AS (
        SELECT r.competitor_id, r.`rank`, r.movement, r.points,
               r.competitions_played, r.tour, r.gender,
               ROW_NUMBER() OVER (
                   PARTITION BY r.competitor_id
                   ORDER BY r.year DESC, r.week DESC
               ) AS rn
        FROM competitor_rankings r
    )
    SELECT l.`rank` AS current_rank,
           c.name,
           c.country,
           c.country_code,
           l.points,
           l.movement,
           l.competitions_played,
           l.tour,
           l.gender
    FROM competitors c
    JOIN latest l ON c.competitor_id = l.competitor_id AND l.rn = 1
    ORDER BY l.`rank`
"""


def show_competitor_explorer():
    """Competitor Explorer page: search and filter the current rankings."""
    st.title("Competitor Explorer")

    # One row per competitor (latest ranking). Cached by run_query.
    df = run_query(LATEST_PER_COMPETITOR_SQL)

    if df.empty:
        st.warning("No competitor data available.")
        st.stop()

    # Filter widgets (sidebar keeps the main area for results)
    st.sidebar.header("Filters")

    search = st.text_input("Search by name")

    min_rank, max_rank = int(df["current_rank"].min()), int(df["current_rank"].max())
    rank_range = st.sidebar.slider(
        "Rank range", min_rank, max_rank, (min_rank, max_rank)
    )

    countries = sorted(df["country"].dropna().unique())
    selected_countries = st.sidebar.multiselect("Country", countries)

    max_points = int(df["points"].max())
    min_points = st.sidebar.slider("Minimum points", 0, max_points, 0)

    # Apply filters step by step
    filtered = df[df["current_rank"].between(rank_range[0], rank_range[1])]
    filtered = filtered[filtered["points"] >= min_points]

    if selected_countries:
        filtered = filtered[filtered["country"].isin(selected_countries)]

    if search.strip():
        # regex=False so characters like "(" or "." are treated as plain text
        filtered = filtered[
            filtered["name"].str.contains(search.strip(), case=False, regex=False, na=False)
        ]

    # Results
    if filtered.empty:
        st.info("No competitors match your filters. Try widening the rank range or clearing a filter.")
        return

    st.caption(f"Showing {len(filtered)} of {len(df)} competitors")

    display = filtered.rename(
        columns={
            "current_rank": "Rank",
            "name": "Competitor",
            "country": "Country",
            "country_code": "Code",
            "points": "Points",
            "movement": "Movement",
            "competitions_played": "Competitions",
            "tour": "Tour",
            "gender": "Gender",
        }
    )
    st.table(display.style.hide(axis="index"))

    st.download_button(
        "Download filtered results as CSV",
        display.to_csv(index=False).encode("utf-8"),
        file_name="filtered_competitors.csv",
        mime="text/csv",
    )
# QUERIES = {
#     "1. Top 10 competitors by points (latest ranking)": """
#         WITH latest AS (
#             SELECT r.*, ROW_NUMBER() OVER (
#                 PARTITION BY r.competitor_id ORDER BY r.year DESC, r.week DESC
#             ) AS rn
#             FROM competitor_rankings r
#         )
#         SELECT c.name, c.country, l.`rank` AS current_rank, l.points
#         FROM competitors c
#         JOIN latest l ON c.competitor_id = l.competitor_id AND l.rn = 1
#         ORDER BY l.points DESC
#         LIMIT 10
#     """,
#     "2. Number of competitors per country": """
#         SELECT country, COUNT(*) AS competitors
#         FROM competitors
#         GROUP BY country
#         ORDER BY competitors DESC
#     """,
#     "3. Biggest rank climbers (latest movement)": """
#         WITH latest AS (
#             SELECT r.*, ROW_NUMBER() OVER (
#                 PARTITION BY r.competitor_id ORDER BY r.year DESC, r.week DESC
#             ) AS rn
#             FROM competitor_rankings r
#         )
#         SELECT c.name, c.country, l.`rank` AS current_rank, l.movement
#         FROM competitors c
#         JOIN latest l ON c.competitor_id = l.competitor_id AND l.rn = 1
#         ORDER BY l.movement DESC
#         LIMIT 10
#     """,
#     # "4. Your next query title": """
#     #     SELECT ...
#     # """,
# }


COMPETITION_QUERIES = {
    "1. List all competitions with category name": """
        SELECT com.competition_id,
               com.competition_name,
               com.`type`,
               com.gender,
               ca.category_name
        FROM competitions com
        LEFT JOIN categories ca
               ON com.category_id = ca.category_id
    """,
    "2. Number of competitions in each category": """
        SELECT ca.category_name,
               com.category_id,
               COUNT(*) AS no_competition
        FROM competitions com
        LEFT JOIN categories ca
               ON com.category_id = ca.category_id
        GROUP BY com.category_id, ca.category_name
        ORDER BY no_competition DESC
    """,
    "3. All competitions of type 'doubles'": """
        SELECT com.competition_id,
               com.competition_name,
               com.`type`,
               com.gender,
               ca.category_name
        FROM competitions com
        LEFT JOIN categories ca
               ON com.category_id = ca.category_id
        WHERE com.`type` = 'doubles'
    """,
    "4. Competitions in a specific category (ITF Men)": """
        SELECT ca.category_name,
               com.category_id,
               com.competition_name,
               com.`type`,
               com.gender
        FROM categories ca
        INNER JOIN competitions com
                ON ca.category_id = com.category_id
        WHERE ca.category_name = 'ITF Men'
    """,
    "5. Parent competitions and their sub-competitions": """
        SELECT p.competition_id   AS parent_id,
               p.competition_name AS parent_name,
               c.competition_id   AS sub_competition_id,
               c.competition_name AS sub_competition_name
        FROM competitions p
        JOIN competitions c
          ON c.parent_id = p.competition_id
        ORDER BY p.competition_id, c.competition_id
    """,
    "6. Distribution of competition types by category": """
        SELECT ca.category_name,
               com.`type`,
               COUNT(*) AS no_competition
        FROM competitions com
        LEFT JOIN categories ca
               ON com.category_id = ca.category_id
        GROUP BY ca.category_name, com.`type`
        ORDER BY ca.category_name, no_competition
    """,
    "7. Top-level competitions (no parent)": """
        SELECT competition_id,
               competition_name,
               `type`,
               gender
        FROM competitions
        WHERE parent_id IS NULL
    """,
}

COMPLEX_VENUE_QUERIES = {
    "1. All venues with their complex name": """
        SELECT v.venue_id,
               v.venue_name,
               v.city_id,
               v.city_name,
               v.country_name,
               v.country_code,
               v.timezone,
               c.complex_name
        FROM venues v
        LEFT JOIN complexes c
               ON v.complex_id = c.complex_id
    """,
    "2. Number of venues in each complex": """
        SELECT c.complex_id,
               c.complex_name,
               COUNT(v.venue_id) AS count_venue
        FROM complexes c
        LEFT JOIN venues v
               ON c.complex_id = v.complex_id
        GROUP BY c.complex_id, c.complex_name
        ORDER BY count_venue DESC
    """,
    "3. Venues in a specific country (Chile)": """
        SELECT *
        FROM venues
        WHERE country_name = 'Chile'
    """,
    "4. All venues and their timezones": """
        SELECT venue_name,
               city_id,
               city_name,
               country_name,
               country_code,
               timezone
        FROM venues
    """,
    "5. Complexes with more than one venue": """
        SELECT c.complex_id,
               c.complex_name,
               COUNT(v.venue_id) AS count_venue
        FROM complexes c
        JOIN venues v
          ON c.complex_id = v.complex_id
        GROUP BY c.complex_id, c.complex_name
        HAVING COUNT(v.venue_id) > 1
        ORDER BY count_venue DESC
    """,
    "6. Number of venues per country": """
        SELECT country_name,
               COUNT(venue_id) AS count_venue
        FROM venues
        GROUP BY country_name
        ORDER BY count_venue DESC
    """,
    "7. Venues for a specific complex (Nacional)": """
        SELECT v.venue_id,
               v.venue_name,
               v.city_id,
               v.city_name,
               v.country_name,
               v.country_code,
               v.timezone,
               c.complex_name
        FROM venues v
        LEFT JOIN complexes c
               ON v.complex_id = c.complex_id
        WHERE c.complex_name LIKE '%Nacional%'
    """,
}

RANKING_QUERIES = {
    "1. All competitors with their rank and points": """
        SELECT c.name,
               cr.`rank`,
               cr.points
        FROM competitors c
        LEFT JOIN competitor_rankings cr
               ON c.competitor_id = cr.competitor_id
        ORDER BY cr.`rank`
    """,
    "2. Competitors ranked in the top 5": """
        SELECT c.name,
               cr.`rank`,
               cr.points
        FROM competitors c
        LEFT JOIN competitor_rankings cr
               ON c.competitor_id = cr.competitor_id
        ORDER BY cr.`rank`
        LIMIT 5
    """,
    "3. Competitors with no rank movement (stable rank)": """
        SELECT c.name,
               cr.`rank`,
               cr.movement
        FROM competitor_rankings cr
        LEFT JOIN competitors c
               ON cr.competitor_id = c.competitor_id
        WHERE cr.movement = 0
        ORDER BY cr.`rank`
    """,
    "4. Total points of competitors from a country (Croatia)": """
        SELECT c.country,
               SUM(cr.points) AS total_points
        FROM competitor_rankings cr
        LEFT JOIN competitors c
               ON cr.competitor_id = c.competitor_id
        WHERE c.country = 'Croatia'
        GROUP BY c.country
    """,
    "5. Number of competitors per country": """
        SELECT c.country,
               COUNT(DISTINCT cr.competitor_id) AS competitor_count
        FROM competitor_rankings cr
        LEFT JOIN competitors c
               ON cr.competitor_id = c.competitor_id
        GROUP BY c.country
        ORDER BY competitor_count DESC
    """,
    "6. Competitors with the highest points in the current week": """
        SELECT c.name,
               c.country,
               cr.`rank`,
               cr.points,
               cr.week
        FROM competitor_rankings cr
        JOIN competitors c
          ON cr.competitor_id = c.competitor_id
        WHERE cr.week = 42
        ORDER BY cr.points DESC
        LIMIT 5
    """,
}

# ---- 2. Group them under the three headings ----
QUERY_GROUPS = {
    "Category & Competition Details": COMPETITION_QUERIES,
    "Complex & Venue Details": COMPLEX_VENUE_QUERIES,
    "Competitor Rankings & Competitor Details": RANKING_QUERIES,
}


def render_query_section(group_name, queries):
    """One tab: a dropdown of query titles, then run and show the result."""
    if not queries:
        st.info("No queries have been defined for this section yet.")
        return

    # key must be unique per tab, otherwise Streamlit raises a duplicate-widget error
    choice = st.selectbox(
        "Choose an analysis query",
        list(queries.keys()),
        key=f"select_{group_name}",
    )
    sql = queries[choice].strip()

    with st.expander("View SQL"):
        st.code(sql, language="sql")

    if st.button("Run query", type="primary", key=f"run_{group_name}"):
        try:
            with st.spinner("Running query..."):
                df = run_query(sql)
        except Exception as exc:
            st.error(f"The query could not be run: {exc}")
            return

        if df.empty:
            st.info("The query ran successfully but returned no rows.")
            return

        st.success(f"{len(df)} rows returned")
        # st.dataframe(df, use_container_width=True, hide_index=True)
        st.table(df.style.hide(axis="index"))

        # Quick chart when the result is one text column + one numeric column
        numeric_cols = df.select_dtypes("number").columns
        text_cols = df.select_dtypes(exclude="number").columns
        if len(df.columns) == 2 and len(numeric_cols) == 1 and len(text_cols) == 1:
            st.bar_chart(df.set_index(text_cols[0])[numeric_cols[0]].head(20))

        st.download_button(
            "Download result as CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="sql_insight_result.csv",
            mime="text/csv",
            key=f"download_{group_name}",
        )


def show_sql_insights():
    """SQL Insights page: three headings, each with its own query dropdown.

    Users can only choose from the fixed dictionaries, so no free text
    is ever executed as SQL.
    """
    st.title("SQL Insights")

    tabs = st.tabs(list(QUERY_GROUPS.keys()))
    for tab, (group_name, queries) in zip(tabs, QUERY_GROUPS.items()):
        with tab:
            st.subheader(group_name)
            render_query_section(group_name, queries)
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", PAGES)

    if page == "Home Dashboard":
        show_home()
    elif page == "Competitor Explorer":
        show_explorer()
    elif page == "Competitor Details":
        show_details()
    elif page == "Country Analysis":
        show_country_analysis()
    elif page == "Leaderboards":
        show_leaderboards()
    elif page == "Competitions & Venues":
        show_competitor_explorer()
    elif page == "SQL Insights":
        show_sql_insights()


if __name__ == "__main__":
    main()



