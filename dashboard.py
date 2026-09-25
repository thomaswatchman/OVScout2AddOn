import streamlit as st
import pandas as pd
import datavolley as dv
from pathlib import Path


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="Live Volleyball Passing",
    layout="wide"
)

st.title("Live Volleyball Passing")

DVW_FILE = Path("updates/myfile-live.dvw")


# ============================================================
# LIVE DASHBOARD
# ============================================================

@st.fragment(run_every=5)
def live_dashboard():

    # --------------------------------------------------------
    # LOAD LIVE DVW
    # --------------------------------------------------------

    if not DVW_FILE.exists():
        st.warning("Waiting for live match data...")
        st.write(f"Looking for: {DVW_FILE.resolve()}")
        return

    try:
        data = dv.read_dv(str(DVW_FILE))
        plays = pd.DataFrame(data)

    except Exception as e:
        st.warning(f"Could not read live DVW file: {e}")
        return

    if plays.empty:
        st.info("Waiting for plays...")
        return


    # --------------------------------------------------------
    # TEAM SELECTION
    # --------------------------------------------------------

    team_choice = st.radio(
        "Team",
        ["Home", "Visiting"],
        horizontal=True
    )

    if team_choice == "Home":
        team_value = "Home"
        rotation_column = "home_setter_position"
    else:
        team_value = "Visiting"
        rotation_column = "visiting_setter_position"


    # --------------------------------------------------------
    # GET RECEPTIONS
    # --------------------------------------------------------

    receptions = plays[
        (plays["skill"] == "Reception") &
        (plays["team"] == team_value)
    ].copy()


    if receptions.empty:
        st.info(f"No receptions recorded for {team_choice} yet.")
        return


    # --------------------------------------------------------
    # PASS CLASSIFICATION
    #
    # Good passes:
    # #  &  +  !
    #
    # Reception error:
    # =
    # --------------------------------------------------------

    GOOD_PASS_CODES = ["#", "&", "+", "!"]

    receptions["good_pass"] = (
        receptions["evaluation_code"]
        .isin(GOOD_PASS_CODES)
    )

    receptions["reception_error"] = (
        receptions["evaluation_code"] == "="
    )


    # --------------------------------------------------------
    # CALCULATE PLAYER STATS BY ROTATION
    # --------------------------------------------------------

    passing_stats = (
        receptions
        .groupby(
            [
                rotation_column,
                "player_number"
            ],
            dropna=False
        )
        .agg(
            attempts=(
                "evaluation_code",
                "size"
            ),
            good_passes=(
                "good_pass",
                "sum"
            ),
            reception_errors=(
                "reception_error",
                "sum"
            )
        )
        .reset_index()
    )


    # Passing percentage:
    #
    # (# + & + + + !) / total attempts
    #
    passing_stats["pass_percentage"] = (
        passing_stats["good_passes"]
        / passing_stats["attempts"]
        * 100
    ).round(1)


    # --------------------------------------------------------
    # CLEAN PLAYER NUMBERS
    # --------------------------------------------------------

    passing_stats["player_number"] = (
        pd.to_numeric(
            passing_stats["player_number"],
            errors="coerce"
        )
        .astype("Int64")
    )


    # ========================================================
    # DISPLAY
    # ========================================================

    st.divider()

    st.subheader(f"{team_choice} Passing")


    # --------------------------------------------------------
    # SIX ROTATIONS
    # --------------------------------------------------------

    rotation_order = [
        [4, 3, 2],
        [5, 6, 1]
    ]


    for rotation_row in rotation_order:

        columns = st.columns(3)

        for column, rotation in zip(columns, rotation_row):

            with column:

                st.markdown(f"### Rotation {rotation}")

                rotation_stats = passing_stats[
                    passing_stats[rotation_column] == rotation
                ].copy()


                if rotation_stats.empty:

                    st.info("No receptions")

                else:

                    rotation_stats = (
                        rotation_stats[
                            [
                                "player_number",
                                "attempts",
                                "pass_percentage",
                                "reception_errors"
                            ]
                        ]
                        .rename(
                            columns={
                                "player_number": "Player",
                                "attempts": "Attempts",
                                "pass_percentage": "Pass %",
                                "reception_errors": "Errors"
                            }
                        )
                        .sort_values(
                            "Player"
                        )
                    )


                    st.dataframe(
                        rotation_stats,
                        hide_index=True,
                        width="stretch",
                        column_config={
                            "Player": st.column_config.NumberColumn(
                                "Player",
                                format="#%d"
                            ),
                            "Attempts": st.column_config.NumberColumn(
                                "Attempts",
                                format="%d"
                            ),
                            "Pass %": st.column_config.NumberColumn(
                                "Pass %",
                                format="%.1f%%"
                            ),
                            "Errors": st.column_config.NumberColumn(
                                "Errors",
                                format="%d"
                            )
                        }
                    )


    # ========================================================
    # TOTAL PASSING
    # ========================================================

    st.divider()

    st.subheader("Overall Passing")


    overall = (
        receptions
        .groupby(
            "player_number",
            dropna=False
        )
        .agg(
            attempts=(
                "evaluation_code",
                "size"
            ),
            good_passes=(
                "good_pass",
                "sum"
            ),
            reception_errors=(
                "reception_error",
                "sum"
            )
        )
        .reset_index()
    )


    overall["pass_percentage"] = (
        overall["good_passes"]
        / overall["attempts"]
        * 100
    ).round(1)


    overall["player_number"] = (
        pd.to_numeric(
            overall["player_number"],
            errors="coerce"
        )
        .astype("Int64")
    )


    overall = (
        overall[
            [
                "player_number",
                "attempts",
                "pass_percentage",
                "reception_errors"
            ]
        ]
        .rename(
            columns={
                "player_number": "Player",
                "attempts": "Attempts",
                "pass_percentage": "Pass %",
                "reception_errors": "Errors"
            }
        )
        .sort_values("Player")
    )


    st.dataframe(
        overall,
        hide_index=True,
        width="stretch",
        column_config={
            "Player": st.column_config.NumberColumn(
                "Player",
                format="#%d"
            ),
            "Attempts": st.column_config.NumberColumn(
                "Attempts",
                format="%d"
            ),
            "Pass %": st.column_config.NumberColumn(
                "Pass %",
                format="%.1f%%"
            ),
            "Errors": st.column_config.NumberColumn(
                "Errors",
                format="%d"
            )
        }
    )


# ============================================================
# START DASHBOARD
# ============================================================

live_dashboard()