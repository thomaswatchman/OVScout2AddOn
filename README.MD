# OVScout2AddOn

A live volleyball stats dashboard. You scout a match in **ovscout2** (in R), which autosaves a DataVolley (`.dvw`) file. This program watches that file and updates the stats in your web browser as the match goes on.

---

## One-time setup

### 1. Install Python

Go to [python.org/downloads](https://www.python.org/downloads/), click the yellow **Download Python** button and run the installer.

> **Windows users:** on the first screen of the installer, tick **"Add Python to PATH"** before clicking Install.

### 2. Install R and ovscout2

1. Download and install **R** from [cran.r-project.org](https://cran.r-project.org/).
2. Download and install **RStudio** from [posit.co/download/rstudio-desktop](https://posit.co/download/rstudio-desktop/).
3. Open RStudio, paste this into the **Console** (bottom-left panel) and press Enter:

   ```r
   install.packages("ovscout2", repos = c("https://openvolley.r-universe.dev", "https://cloud.r-project.org"))
   ```

   Wait for it to finish. It can take a few minutes.

### 3. Open a terminal

- **Mac:** press `Cmd + Space`, type **Terminal** and press Enter.
- **Windows:** press the Windows key, type **cmd** and press Enter.

### 4. Install git

Type this and press Enter:

```
git --version
```

- If it shows a version number (like `git version 2.39.0`), git is already installed. Go to the next step.
- **Mac:** if a pop-up asks to install "command line developer tools", click **Install** and wait for it to finish.
- **Windows:** download and install git from [git-scm.com](https://git-scm.com/downloads) (the default options are fine), then close and reopen the terminal.

### 5. Download this project

Copy and paste these two lines into the terminal, pressing Enter after each:

**Mac:**

```
cd ~/Desktop
git clone https://github.com/thomaswatchman/OVScout2AddOn.git
```

**Windows:**

```
cd %USERPROFILE%\Desktop
git clone https://github.com/thomaswatchman/OVScout2AddOn.git
```

This creates a folder called `OVScout2AddOn` on your Desktop.

### 6. Go into the project folder

**Mac:**

```
cd ~/Desktop/OVScout2AddOn
```

**Windows:**

```
cd %USERPROFILE%\Desktop\OVScout2AddOn
```

> You'll need to do this every time you open a new terminal window, before running any of the commands below.

### 7. Install the required Python packages

Copy and paste this line into the terminal and press Enter:

**Mac:**

```
pip3 install openvolley-pydatavolley pandas streamlit matplotlib
```

**Windows:**

```
pip install openvolley-pydatavolley pandas streamlit matplotlib
```

Wait for it to finish. You only need to do this once.

---

## Running it during a match

### 1. Start scouting in R

Open RStudio and paste this into the Console. It opens ovscout2 in autosave mode, so the match file is saved into the project's `updates` folder as you scout.

```r
library(ovscout2)

ov_scouter(
  video_file = FALSE,
  scout_mode = "type",
  auto_save_dir = "~/Desktop/OVScout2AddOn/updates"
)
```

> **Windows:** replace the path with the full path, for example `"C:/Users/yourname/Desktop/OVScout2AddOn/updates"` (use forward slashes `/`).
>
> If you put the project somewhere other than your Desktop, change the `auto_save_dir` path to match. To find the path on a Mac, right-click the `updates` folder, hold the **Option** key and choose **Copy "updates" as Pathname**.

### 2. Start the dashboard

**Mac:** open the `OVScout2AddOn` folder on your Desktop and double-click **Start Dashboard.command**. It gets the latest version and opens the dashboard for you.

**Windows:** open a terminal, go into the project folder (setup steps 3 and 6), then run:

```
git pull
python main.py
```

The dashboard opens in your web browser. It refreshes automatically every few seconds as you scout.

**To stop the program:** click the Terminal window and press `Ctrl + C`.

---

## Scouting code examples

`*` = home team, `a` = visiting team.

| Code | Meaning |
| --- | --- |
| `*z1` | Home setter is in position 1 |
| `az1` | Visiting setter is in position 1 |
| `*01SM+` | Home #1, positive serve |
| `*02RH#` | Home #2, perfect reception |
| `*03AH#` | Home #3, high ball attack, kill |
| `a04SM+` | Visiting #4, positive serve |
| `a05RH+` | Visiting #5, positive reception |
| `a06AH=` | Visiting #6, high ball attack, error |

---

## Getting the latest version

**Mac:** nothing to do. **Start Dashboard.command** does this automatically every time.

**Windows:** run `git pull` in the project folder before each match (it's included in the steps above).

> **Don't edit the project's files yourself.** If you only ever run `git pull`, it will always work.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `command not found: python3` or `'python' is not recognized` | Python isn't installed, or on Windows "Add Python to PATH" wasn't ticked. Reinstall Python (setup step 1). |
| `No module named ...` | The Python packages aren't installed. Run setup step 7 again. |
| `git pull` says **"Your local changes would be overwritten"** | Run `git reset --hard` and then `git pull` again. This undoes any changes to the project files on your computer. |
| `not a git repository` | You're not in the project folder. Run setup step 6 first. |
| `there is no package called 'ovscout2'` in R | Run the install command in setup step 2 again. |
| Dashboard says **"Waiting for live match data..."** | Check that `auto_save_dir` in R points to the project's `updates` folder, and that you've started scouting. |
| `File not found` keeps printing in the terminal | Make sure you ran the program from inside the project folder (setup step 6). |
