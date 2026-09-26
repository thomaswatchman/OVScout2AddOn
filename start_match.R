# Starts ovscout2 with both rosters loaded from roster.xlsx.
#
# Run it in RStudio with:
#   source("~/Desktop/OVScout2AddOn/start_match.R")

library(ovscout2)
library(readxl)


# ============================================================
# FIND THE PROJECT FOLDER
# ============================================================

# When run with source(), this is the folder the script is in
project_dir <- tryCatch(
    dirname(normalizePath(sys.frame(1)$ofile)),
    error = function(e) path.expand("~/Desktop/OVScout2AddOn")
)

roster_file <- file.path(project_dir, "roster.xlsx")
template_file <- file.path(project_dir, "roster_template.xlsx")
updates_dir <- file.path(project_dir, "updates")


# ============================================================
# FIRST RUN: CREATE roster.xlsx FROM THE TEMPLATE
# ============================================================

# roster.xlsx isn't stored in git, so editing it never breaks git pull
if (!file.exists(roster_file)) {
    file.copy(template_file, roster_file)
    stop(
        "\n\nCreated roster.xlsx in ", project_dir, "\n",
        "Fill in both sheets (Home and Visiting), save it, then run this again.\n",
        call. = FALSE
    )
}


# ============================================================
# READ ONE TEAM FROM THE EXCEL FILE
# ============================================================

read_team <- function(sheet) {

    team_name <- read_excel(
        roster_file,
        sheet = sheet,
        range = "B1",
        col_names = FALSE,
        .name_repair = "minimal"
    )

    team_name <- if (nrow(team_name) == 0) "" else trimws(as.character(team_name[[1, 1]]))

    if (is.na(team_name) || team_name == "") {
        stop("The team name (cell B1) is empty on the ", sheet, " sheet", call. = FALSE)
    }

    # Players start at row 4: Number, First name, Last name, Role
    players <- read_excel(
        roster_file,
        sheet = sheet,
        range = cell_limits(c(4, 1), c(NA, 4)),
        col_names = c("number", "firstname", "lastname", "role"),
        col_types = "text"
    )

    players <- players[!is.na(players$number) & trimws(players$number) != "", ]

    numbers <- suppressWarnings(as.integer(players$number))

    if (any(is.na(numbers))) {
        stop(
            "These shirt numbers on the ", sheet, " sheet aren't whole numbers: ",
            paste(players$number[is.na(numbers)], collapse = ", "),
            call. = FALSE
        )
    }

    if (any(duplicated(numbers))) {
        stop(
            "Shirt number(s) used twice on the ", sheet, " sheet: ",
            paste(unique(numbers[duplicated(numbers)]), collapse = ", "),
            call. = FALSE
        )
    }

    players$number <- numbers
    players$firstname[is.na(players$firstname)] <- ""
    players$lastname[is.na(players$lastname)] <- ""
    players$role <- tolower(trimws(players$role))
    players$role[is.na(players$role) | players$role == ""] <- "unknown"

    list(name = team_name, players = players)
}


home <- read_team("Home")
visiting <- read_team("Visiting")


# ============================================================
# BUILD THE MATCH AND START SCOUTING
# ============================================================

# Short team codes: first 4 letters, made unique if both teams share them
team_ids <- toupper(substr(gsub("[^A-Za-z0-9]", "", c(home$name, visiting$name)), 1, 4))
if (team_ids[1] == team_ids[2] || any(team_ids == "")) {
    team_ids <- c("HOME", "VISI")
}

# Player ids must be unique, and names can repeat or be blank
home$players$player_id <- paste0(team_ids[1], "-", home$players$number)
visiting$players$player_id <- paste0(team_ids[2], "-", visiting$players$number)

match <- dv_create(
    teams = data.frame(team_id = team_ids, team = c(home$name, visiting$name)),
    players_h = home$players,
    players_v = visiting$players
)

match$meta$match$date <- Sys.Date()

message(
    "Starting ovscout2: ", home$name, " (", nrow(home$players), " players) vs ",
    visiting$name, " (", nrow(visiting$players), " players)"
)

ov_scouter(
    match,
    video_file = FALSE,
    scout_mode = "type",
    auto_save_dir = updates_dir
)
