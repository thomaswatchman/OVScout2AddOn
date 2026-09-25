#!/bin/bash
# Double-click this file to get the latest version and start the dashboard.

cd "$(dirname "$0")" || exit 1

echo "Getting the latest version..."
git pull || echo "Could not update. Starting the version you already have."

echo
echo "Starting the dashboard. Press Ctrl + C in this window to stop it."
python3 main.py
