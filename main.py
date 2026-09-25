import time
from pathlib import Path
import datavolley as dv
import time
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import sys

DVW_FILE = Path("/Users/thomaswatchman/VolleyballDWVAnalysis/updates/myfile-live.dvw")

last_modified = None

print("Watching:", DVW_FILE.resolve())

plt.ion()

dashboard_process = None

while True:

    if not DVW_FILE.exists():
        print("File not found")
        time.sleep(1)
        continue

    modified = DVW_FILE.stat().st_mtime

    if modified != last_modified:

        if last_modified is None:
            print("\nInitial file detected")
        else:
            print("\nfile updated")

        try:
            # Parse updated DVW
            data = dv.read_dv(str(DVW_FILE))

            # Convert plays to DataFrame
            plays = pd.DataFrame(data)

            print(f"parsed {len(plays)} plays")

            # Launch dashboard if it isn't already running
            if dashboard_process is None or dashboard_process.poll() is not None:
                print("Launching dashboard...")

                dashboard_process = subprocess.Popen([
                    sys.executable,
                    "-m"
                    "streamlit",
                    "run",
                    "dashboard.py"
                ])


            # Keep only successful attacks
            kills = plays[
                (plays["skill"] == "Attack") &
                (plays["evaluation_code"] == "#")
            ]

            # Count kills by player
            kills_by_player = (
                kills.groupby(["team", "player_number"])
                .size()
                .reset_index(name="kills")
            )

            print("\nKILLS BY PLAYER")
            print(kills_by_player)

            # Plot
            if not kills_by_player.empty:
                kills_by_player["label"] = (
                    kills_by_player["team"].astype(str)
                    + " #"
                    + kills_by_player["player_number"].astype(int).astype(str)
                )

                plt.clf()

                plt.bar(
                    kills_by_player["label"],
                    kills_by_player["kills"]
                )

                plt.title("Kills by Player")
                plt.xlabel("Player")
                plt.ylabel("Kills")
                plt.xticks(rotation=45)
                plt.tight_layout()

                plt.pause(0.1)

            last_modified = modified

        except Exception as e:
            print(f"Could not parse file: {e}")

    time.sleep(5)