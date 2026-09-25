import streamlit as st
import pandas as pd
import altair as alt
import datavolley as dv
from pathlib import Path


st.set_page_config(
    page_title="Live Volleyball Analysis",
    layout="wide"
)

st.title("Live Volleyball Analysis")

DVW_FILE = Path(__file__).resolve().parent / "updates" / "myfile-live.dvw"

ROTATION_LAYOUT = [
    [4, 3, 2],
    [5, 6, 1]
]

# Attack start zone -> where the set went
ZONE_NAMES = {
    4: "Left",
    3: "Middle",
    2: "Right",
    8: "Pipe",
    6: "Pipe",
    9: "Back right",
    1: "Back right",
    7: "Back left",
    5: "Back left"
}

ZONE_ORDER = [
    "Left",
    "Middle",
    "Right",
    "Pipe",
    "Back right",
    "Back left"
]

# Attacks that weren't set: setter dump, overpass, attack on 2nd contact
NOT_SET_COMBOS = ["PP", "PR", "P2"]

BAR_COLOR = "#2a78d6"


# ============================================================
# TEAM SELECTOR 
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

def load_plays():
    """Returns the selected team's plays with a numeric "Rotation" column,
    plus the attack combination -> start zone lookup from the file."""

    if not DVW_FILE.exists():
        return pd.DataFrame(), {}, "Waiting for myfile-live.dvw"

    try:
        data = dv.read_dv(str(DVW_FILE))
        plays = pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame(), {}, f"Could not parse DVW: {e}"

    if plays.empty:
        return pd.DataFrame(), {}, "DVW loaded, but contains no plays"

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
        "attack_code",
        "start_zone",
        team_name_column,
        rotation_column
    ]

    missing = [
        column
        for column in required
        if column not in plays.columns
    ]

    if missing:
        return pd.DataFrame(), {}, f"Missing columns: {missing}"

    team_value = plays[team_name_column].iloc[0]

    plays = plays[plays["team"] == team_value].copy()

    # Setter positions are parsed as text ("5"), rotations below are numbers
    plays["Rotation"] = pd.to_numeric(
        plays[rotation_column],
        errors="coerce"
    ).astype("Int64")

    plays["player_number"] = plays["player_number"].astype("Int64")

    try:
        combos = dv.extract_attack_combinations(
            DVW_FILE.read_text(encoding="utf-8", errors="replace")
        )
        combo_zones = {
            combo["code"]: combo["zone"]
            for combo in combos
        }
    except Exception:
        combo_zones = {}

    return plays, combo_zones, None


def passing_stats(plays):

    receptions = plays[
        plays["skill"] == "Reception"
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
            ["Rotation", "player_number"],
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
        "player_number": "Player"
    })

    return stats, f"{len(receptions)} receptions loaded"


# ============================================================
# SET DISTRIBUTION
# ============================================================

def set_distribution(plays, combo_zones):
    """Where the sets went in each rotation, based on where each
    attack started. Returns one row per rotation and zone."""

    attacks = plays[
        (plays["skill"] == "Attack") &
        (~plays["attack_code"].isin(NOT_SET_COMBOS))
    ].copy()

    if attacks.empty:
        return pd.DataFrame(), "No attacks recorded yet"

    # Use the typed start zone, or fall back to the attack combination's zone
    zone = pd.to_numeric(attacks["start_zone"], errors="coerce")
    combo_zone = attacks["attack_code"].map(combo_zones)
    attacks["Zone"] = zone.fillna(combo_zone).map(ZONE_NAMES)

    with_zone = attacks.dropna(subset=["Zone", "Rotation"])
    no_zone = len(attacks) - len(with_zone)

    status = f"{len(with_zone)} attacks with a zone"
    if no_zone:
        status += (
            f" ({no_zone} without a zone not shown - add the zone or an "
            "attack combination when scouting, e.g. *04AH#V5)"
        )

    if with_zone.empty:
        return pd.DataFrame(), status

    counts = (
        with_zone
        .groupby(["Rotation", "Zone"])
        .size()
        .reset_index(name="Sets")
    )

    counts["Share"] = (
        counts["Sets"] /
        counts.groupby("Rotation")["Sets"].transform("sum")
    )

    return counts, status


def distribution_chart(rotation_counts, zones):

    # Every zone gets a row, so all six charts line up
    data = (
        pd.DataFrame({"Zone": zones})
        .merge(rotation_counts, on="Zone", how="left")
        .fillna({"Sets": 0, "Share": 0})
    )

    data["Label"] = data.apply(
        lambda r: f"{r['Share']:.0%} ({int(r['Sets'])})" if r["Sets"] else "",
        axis=1
    )

    base = alt.Chart(data).encode(
        y=alt.Y(
            "Zone:N",
            sort=zones,
            title=None,
            axis=alt.Axis(ticks=False, domain=False, labelPadding=6)
        ),
        x=alt.X(
            "Share:Q",
            scale=alt.Scale(domain=[0, 1.35]),
            axis=None
        ),
        tooltip=[
            alt.Tooltip("Zone:N"),
            alt.Tooltip("Sets:Q"),
            alt.Tooltip("Share:Q", title="Share", format=".0%")
        ]
    )

    bars = base.mark_bar(
        color=BAR_COLOR,
        size=18,
        cornerRadiusEnd=4
    )

    labels = base.mark_text(
        align="left",
        dx=6
    ).encode(
        text="Label:N"
    )

    return (bars + labels).properties(
        height=len(zones) * 28
    ).configure_view(
        stroke=None
    )


# ============================================================
# LIVE SECTION
# ============================================================

@st.fragment(run_every=5)
def live_analysis():

    plays, combo_zones, load_error = load_plays()

    if load_error:
        stats, status = pd.DataFrame(), load_error
    else:
        stats, status = passing_stats(plays)

    st.caption(status)

    st.subheader(f"{team_choice} Passing by Rotation")

    for row in ROTATION_LAYOUT:

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

    st.divider()

    st.subheader(f"{team_choice} Set Distribution by Rotation")

    if load_error:
        distribution, status = pd.DataFrame(), load_error
    else:
        distribution, status = set_distribution(plays, combo_zones)

    st.caption(status)

    # Only list zones that have been used this match
    zones = [
        zone
        for zone in ZONE_ORDER
        if not distribution.empty and zone in distribution["Zone"].values
    ]

    for row in ROTATION_LAYOUT:

        cols = st.columns(3)

        for col, rotation in zip(cols, row):

            with col:

                st.markdown(f"### Rotation {rotation}")

                if distribution.empty:
                    rotation_counts = pd.DataFrame()
                else:
                    rotation_counts = distribution[
                        distribution["Rotation"] == rotation
                    ]

                if rotation_counts.empty:
                    st.caption("No sets yet")
                    continue

                st.altair_chart(
                    distribution_chart(rotation_counts, zones),
                    width="stretch"
                )


live_analysis()