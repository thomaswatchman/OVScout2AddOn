import time
from pathlib import Path
import datavolley as dv
import pandas as pd
import shutil
import subprocess
import sys

PROJECT_DIR = Path(__file__).resolve().parent
DVW_FILE = PROJECT_DIR / "updates" / "myfile-live.dvw"
REPORT_FILE = PROJECT_DIR / "updates" / "match-report.html"
REPORT_ERROR_FILE = PROJECT_DIR / "updates" / "match-report.html.error"


def find_rscript():
    """Path to Rscript, which runs match_report.R. On Windows and some Macs
    R isn't on the PATH, so look in the usual install folders too."""

    rscript = shutil.which("Rscript")
    if rscript:
        return rscript

    candidates = [
        Path("/Library/Frameworks/R.framework/Resources/bin/Rscript"),
        Path("/opt/homebrew/bin/Rscript"),
        Path("/usr/local/bin/Rscript")
    ]
    # Newest R version first
    candidates += sorted(
        Path("C:/Program Files/R").glob("R-*/bin/Rscript.exe"),
        reverse=True
    )

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


rscript = find_rscript()

if rscript is None:
    print("Could not find R, so the match report won't be made")
    REPORT_ERROR_FILE.write_text("Could not find R on this computer")

last_modified = None

print("Watching:", DVW_FILE.resolve())

dashboard_process = None

# The report takes a few seconds to make, so it's made in the background.
# If the file changes meanwhile, it's made again once that one finishes.
report_process = None
report_wanted = False

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

        report_wanted = True

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

    report_running = report_process is not None and report_process.poll() is None

    if rscript and report_wanted and not report_running:
        report_process = subprocess.Popen(
            [
                rscript,
                str(PROJECT_DIR / "match_report.R"),
                str(DVW_FILE),
                str(REPORT_FILE)
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        report_wanted = False

    time.sleep(5)