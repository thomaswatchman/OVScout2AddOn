import streamlit as st
import pandas as pd
import datavolley as dv
from pathlib import Path


st.set_page_config(
    page_title="Live Volleyball Analysis",
    layout="wide"
)

st.title("Live Volleyball Analysis")

DVW_FILE = Path("updates/myfile-live.dvw")


# ============================================================
# TEAM SELECTOR - ALWAYS RENDERED
# ============================================================

team_choice = st.radio(
    "Team",
    ["Home", "Visiting"],
    horizontal=True
)

st.divider()


# ============================================================
# EMPTY TABLE
# ============================================================

def empty_table():
    return pd.DataFrame({
        "Player": pd.Series(dtype="Int64"),
        "Attempts": pd.Series(dtype="int"),
        "Pass %": pd.Series(dtype="float"),
        "Errors": pd.Series(dtype="int")
    })


# ============================================================
# LOAD LIVE DATA
# ============================================================

def load_stats():

    if not DVW_FILE.exists():
        return pd.DataFrame(), "Waiting for myfile-live.dvw"

    try:
        data = dv.read_dv(str(DVW_FILE))
        plays = pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame(), f"Could not parse DVW: {e}"

    if plays.empty:
        return pd.DataFrame(), "DVW loaded, but contains no plays"

    # The "team" column holds the actual team names from the file,
    # so look up the selected team's name rather than hardcoding it
    if team_choice == "Home":
        team_name_column = "home_team"
        rotation_column = "home_setter_position"
    else:
        team_name_column = "visiting_team"
        rotation_column = "visiting_setter_position"

    required = [
        "skill",
        "team",
        "evaluation_code",
        "player_number",
        team_name_column,
        rotation_column
    ]

    missing = [
        column
        for column in required
        if column not in plays.columns
    ]

    if missing:
        return pd.DataFrame(), f"Missing columns: {missing}"

    team_value = plays[team_name_column].iloc[0]

    # Setter positions are parsed as text ("5"), rotations below are numbers
    plays[rotation_column] = pd.to_numeric(
        plays[rotation_column],
        errors="coerce"
    ).astype("Int64")

    plays["player_number"] = plays["player_number"].astype("Int64")

    receptions = plays[
        (plays["skill"] == "Reception") &
        (plays["team"] == team_value)
    ].copy()

    if receptions.empty:
        return pd.DataFrame(), "No receptions recorded yet"

    # Good reception codes
    receptions["good_pass"] = (
        receptions["evaluation_code"]
        .isin(["#", "&", "+", "!"])
    )

    # Reception errors
    receptions["error"] = (
        receptions["evaluation_code"] == "="
    )

    stats = (
        receptions
        .groupby(
            [rotation_column, "player_number"],
            dropna=False
        )
        .agg(
            Attempts=("evaluation_code", "size"),
            Good=("good_pass", "sum"),
            Errors=("error", "sum")
        )
        .reset_index()
    )

    stats["Pass %"] = (
        stats["Good"] /
        stats["Attempts"] *
        100
    ).round(1)

    stats = stats.rename(columns={
        rotation_column: "Rotation",
        "player_number": "Player"
    })

    return stats, f"{len(receptions)} receptions loaded"


# ============================================================
# LIVE SECTION
# ============================================================

@st.fragment(run_every=5)
def live_analysis():

    stats, status = load_stats()

    st.caption(status)

    st.subheader(f"{team_choice} Passing by Rotation")

    rotation_layout = [
        [4, 3, 2],
        [5, 6, 1]
    ]

    for row in rotation_layout:

        cols = st.columns(3)

        for col, rotation in zip(cols, row):

            with col:

                st.markdown(f"### Rotation {rotation}")

                if stats.empty:
                    display = empty_table()

                else:
                    display = stats[
                        stats["Rotation"] == rotation
                    ].copy()

                    if display.empty:
                        display = empty_table()

                    else:
                        display = display[
                            [
                                "Player",
                                "Attempts",
                                "Pass %",
                                "Errors"
                            ]
                        ]

                st.dataframe(
                    display,
                    hide_index=True,
                    width="stretch",
                    height=200,
                    column_config={
                        "Player": st.column_config.NumberColumn(
                            "Player"
                        ),
                        "Attempts": st.column_config.NumberColumn(
                            "Attempts"
                        ),
                        "Pass %": st.column_config.NumberColumn(
                            "Pass %",
                            format="%.1f%%"
                        ),
                        "Errors": st.column_config.NumberColumn(
                            "Errors"
                        )
                    }
                )


live_analysis()