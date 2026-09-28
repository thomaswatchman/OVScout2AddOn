import re
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

# Player role numbers in the file's player list (from roster.xlsx)
ROLE_CODES = {
    "2": "outside",
    "3": "opposite",
    "4": "middle"
}

FRONT_ROW = [2, 3, 4]

# When no zone is typed: (role, in front row) -> usual attack zone
INFERRED_ZONES = {
    ("outside", True): 4,
    ("outside", False): 8,
    ("opposite", True): 2,
    ("opposite", False): 9,
    ("middle", True): 3
}

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
    """Returns the selected team's plays with numeric "Rotation" and
    "Court position" columns and each player's "Role", plus the attack
    combination -> start zone lookup from the file."""

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
        lineup_prefix = "home_p"
        players_section = "3PLAYERS-H"
    else:
        team_name_column = "visiting_team"
        rotation_column = "visiting_setter_position"
        lineup_prefix = "visiting_p"
        players_section = "3PLAYERS-V"

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

    # Where the player was in the rotation (1-6), from the lineup on each play
    plays["Court position"] = pd.Series(pd.NA, index=plays.index, dtype="Int64")
    for position in range(1, 7):
        column = f"{lineup_prefix}{position}"
        if column not in plays.columns:
            continue
        in_position = (
            pd.to_numeric(plays[column], errors="coerce").astype("Int64")
            == plays["player_number"]
        ).fillna(False).astype(bool)
        plays.loc[in_position, "Court position"] = position

    raw = DVW_FILE.read_text(encoding="utf-8", errors="replace")

    roles = player_roles(raw, players_section)
    plays["Role"] = plays["player_number"].map(roles)

    try:
        combos = dv.extract_attack_combinations(raw)
        combo_zones = {
            combo["code"]: combo["zone"]
            for combo in combos
        }
    except Exception:
        combo_zones = {}

    return plays, combo_zones, None


def player_roles(raw, section):
    """Shirt number -> role ("outside", "opposite", "middle") from the
    file's player list. Other roles are left out."""

    match = re.search(rf"\[{section}\]\n(.*?)(?=\n\[3|$)", raw, re.DOTALL)
    if not match:
        return {}

    roles = {}
    for line in match.group(1).splitlines():
        parts = line.split(";")
        if len(parts) > 13 and parts[1].strip().isdigit() and parts[13] in ROLE_CODES:
            roles[int(parts[1])] = ROLE_CODES[parts[13]]

    return roles


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

    # Use the typed start zone, then the attack combination's zone, then
    # guess from the player's role and whether they were in the front row
    typed_zone = pd.to_numeric(attacks["start_zone"], errors="coerce")
    combo_zone = pd.to_numeric(
        attacks["attack_code"].map(combo_zones),
        errors="coerce"
    )
    inferred_zone = pd.Series(
        [
            INFERRED_ZONES.get((role, position in FRONT_ROW))
            if pd.notna(position) else None
            for role, position in zip(attacks["Role"], attacks["Court position"])
        ],
        index=attacks.index,
        dtype="float"
    )

    known_zone = typed_zone.fillna(combo_zone)
    attacks["Zone"] = known_zone.fillna(inferred_zone).map(ZONE_NAMES)
    inferred = known_zone.isna() & attacks["Zone"].notna()

    with_zone = attacks.dropna(subset=["Zone", "Rotation"])
    no_zone = attacks["Zone"].isna().sum()
    no_rotation = len(attacks) - len(with_zone) - no_zone

    status = f"{len(with_zone)} attacks"
    if inferred.any():
        status += f", {inferred.sum()} with the zone guessed from the player's role"
    if no_zone:
        status += (
            f". {no_zone} not shown: no zone typed and the player's role is "
            "not outside, opposite or middle in roster.xlsx"
        )
    if no_rotation:
        status += f". {no_rotation} not shown: no setter position (rotation)"

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
            axis=alt.Axis(
                ticks=False,
                domain=False,
                labelPadding=6,
                labelFontSize=12,
                labelLimit=0
            )
        ),
        x=alt.X(
            "Share:Q",
            # Room past 100% for the value label
            scale=alt.Scale(domain=[0, 1.5]),
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

    # Text marks don't follow Streamlit's theme, so match it here
    if st.context.theme.type == "dark":
        text_color = "#fafafa"
    else:
        text_color = "#31333f"

    labels = base.mark_text(
        align="left",
        dx=6,
        fontSize=12,
        color=text_color
    ).encode(
        text="Label:N"
    )

    # Fill the column, and keep axis labels and value labels inside it
    return (bars + labels).properties(
        width="container",
        height=len(zones) * 28,
        autosize=alt.AutoSizeParams(type="fit-x", contains="padding")
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