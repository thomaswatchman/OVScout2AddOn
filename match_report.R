# Builds the classic match report (the one ovscout2 makes) from the live
# match file. main.py runs this in the background every time the file changes.
#
#   Rscript match_report.R <match file> <report file>
#
# If the report can't be made, the reason is written to <report file>.error
# and the previous report is kept.

args <- commandArgs(trailingOnly = TRUE)
match_file <- args[1]
report_file <- args[2]
error_file <- paste0(report_file, ".error")


# ============================================================
# FIND PANDOC
# ============================================================

# The report needs pandoc. RStudio includes it, but R run from a terminal
# doesn't know where, so look in RStudio's usual install folders
use_rstudio_pandoc <- function() {

    if (rmarkdown::pandoc_available()) {
        return(invisible())
    }

    rstudio_dirs <- c(
        "/Applications/RStudio.app/Contents/Resources/app/quarto/bin/tools/aarch64",
        "/Applications/RStudio.app/Contents/Resources/app/quarto/bin/tools/x86_64",
        "/Applications/RStudio.app/Contents/Resources/app/quarto/bin/tools",
        "/Applications/RStudio.app/Contents/MacOS/pandoc",
        "C:/Program Files/RStudio/resources/app/bin/quarto/bin/tools",
        "C:/Program Files/RStudio/bin/quarto/bin/tools",
        "C:/Program Files/RStudio/bin/pandoc"
    )

    rmarkdown::find_pandoc(cache = FALSE, dir = rstudio_dirs[dir.exists(rstudio_dirs)])

    if (!rmarkdown::pandoc_available()) {
        stop("Could not find pandoc. Install RStudio, or pandoc from pandoc.org")
    }
}


# ============================================================
# BUILD THE REPORT
# ============================================================

result <- tryCatch({

    suppressPackageStartupMessages({
        library(datavolley)
        library(volleyreport)
    })

    use_rstudio_pandoc()

    match <- dv_read(match_file)

    if (nrow(match$plays) == 0) {
        stop("No rallies scouted yet")
    }

    built <- suppressWarnings(suppressMessages(
        vr_match_summary(match, format = "html")
    ))

    # Copy next to the report then rename, so the dashboard never
    # reads a half-written file
    temp_file <- paste0(report_file, ".tmp")
    file.copy(built, temp_file, overwrite = TRUE)
    file.rename(temp_file, report_file)

    NULL

}, error = function(e) conditionMessage(e))

if (is.null(result)) {
    unlink(error_file)
} else {
    # These only happen at the start of a match, so any report is from
    # the last match and shouldn't be shown
    if (grepl("starting lineup|No rallies", result)) {
        unlink(report_file)
    }
    if (grepl("starting lineup", result)) {
        result <- "Enter the starting lineups in ovscout2 to see the report"
    }
    writeLines(result, error_file)
    quit(status = 1)
}
