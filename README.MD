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
   install.packages(c("ovscout2", "readxl"), repos = c("https://openvolley.r-universe.dev", "https://cloud.r-project.org"))
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
pip3 install openvolley-pydatavolley pandas streamlit
```

**Windows:**

```
pip install openvolley-pydatavolley pandas streamlit
```

Wait for it to finish. You only need to do this once.

---

## Running it during a match

### 1. Fill in the rosters

Open **roster.xlsx** in the `OVScout2AddOn` folder (Excel or Numbers both work). It has two sheets, **Home** and **Visiting**:

- Type the team name in the yellow cell at the top.
- Add one player per row: **Number** (required), **First name**, **Last name** and **Role** (pick from the dropdown, or leave blank).
- Save the file.

> **First time only:** `roster.xlsx` doesn't exist yet. Run step 2 once and it will be created for you, then fill it in and run step 2 again.

You only need to change the file when the teams or players change.

### 2. Start scouting in R

Open RStudio, paste this into the Console and press Enter:

```r
source("~/Desktop/OVScout2AddOn/start_match.R")
```

ovscout2 opens with both rosters already loaded, and autosaves the match into the project's `updates` folder as you scout. Enter the starting lineups (**Edit lineups**) and start scouting.

> **Windows:** use the full path, for example `source("C:/Users/yourname/Desktop/OVScout2AddOn/start_match.R")` (use forward slashes `/`).
>
> If you put the project somewhere other than your Desktop, change the path to match. To find it on a Mac, right-click `start_match.R`, hold the **Option** key and choose **Copy "start_match.R" as Pathname**.

### 3. Start the dashboard

**Mac:** open the `OVScout2AddOn` folder on your Desktop and double-click **Start Dashboard.command**. It gets the latest version and opens the dashboard for you.

**Windows:** open a terminal, go into the project folder (setup steps 3 and 6), then run:

```
git pull
python main.py
```

The dashboard opens in your web browser. It refreshes automatically every few seconds as you scout.

It has two tabs:

- **Live stats**: passing and set distribution by rotation for the team you pick.
- **Match report**: the classic DataVolley-style match report for both teams (the same one ovscout2 makes). It's rebuilt a few seconds after each rally.

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

> **Don't edit the project's files yourself**, apart from `roster.xlsx`. As long as you only change that file, `git pull` will always work.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `command not found: python3` or `'python' is not recognized` | Python isn't installed, or on Windows "Add Python to PATH" wasn't ticked. Reinstall Python (setup step 1). |
| `No module named ...` | The Python packages aren't installed. Run setup step 7 again. |
| `git pull` says **"Your local changes would be overwritten"** | Run `git reset --hard` and then `git pull` again. This undoes any changes to the project files on your computer. |
| `not a git repository` | You're not in the project folder. Run setup step 6 first. |
| `there is no package called 'ovscout2'` or `'readxl'` in R | Run the install command in setup step 2 again. |
| R says **"Created roster.xlsx"** | That's expected the first time. Fill in `roster.xlsx`, save it, and run `start_match.R` again. |
| R says **"The team name (cell B1) is empty"** | Type the team name in the yellow cell on that sheet and save. |
| R says a shirt number **isn't a whole number** or is **used twice** | Fix the Number column on that sheet and save. |
| R says `cannot open file` when running `start_match.R` | The path is wrong. Check where the `OVScout2AddOn` folder is (see the note under "Start scouting in R"). |
| Dashboard says **"Waiting for myfile-live.dvw"** | Start ovscout2 with `start_match.R` (so it saves into the `updates` folder) and scout at least one rally. |
| Match report says **"Enter the starting lineups"** | Enter both teams' starting lineups in ovscout2 (**Edit lineups**). The report appears after the next rally. |
| Match report says **"Could not find R"** or **"Could not find pandoc"** | Install R and RStudio (setup step 2). |
| `File not found` keeps printing in the terminal | Make sure you ran the program from inside the project folder (setup step 6). |
