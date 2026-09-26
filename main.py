import time
from pathlib import Path
import datavolley as dv
import pandas as pd
import subprocess
import sys

PROJECT_DIR = Path(__file__).resolve().parent
DVW_FILE = PROJECT_DIR / "updates" / "myfile-live.dvw"

last_modified = None

print("Watching:", DVW_FILE.resolve())

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
                    "-m",
                    "streamlit",
                    "run",
                    str(PROJECT_DIR / "dashboard.py")
                ])

            last_modified = modified

        except Exception as e:
            print(f"Could not parse file: {e}")

    time.sleep(5)