# --------------------------------------
# Project Environment Setup with `conda`
# --------------------------------------

# Remove from R installation the packages installed by conda:
skip_packages <- c(
  "tidyverse", "data.table", "curl", "textshaping", "haven", "xml2",
  "dtplyr", "httr", "ragg", "gargle", "rvest", "googledrive", "googlesheets4", "writexl"
)

# Original list
required_packages <- c(
  "argparse",
  "binom",
  "broom",
  "broom.helpers",
  "caret",
  "cardx",
  "config",
  "DataExplorer",
  "dlookr",
  "downloadthis",
  "DT",
  "epitools",
  "flextable",
  "forestplot",
  "ggbreak",
  "ggplot2",
  "ggpubr",
  "ggrepel",
  "ggsignif",
  "ggsurvfit",
  "ggtext",
  "glue",
  "gridExtra",
  "gtExtras",
  "gtsummary",
  "kableExtra",
  "languageserver",
  "lubridate",
  "mice",
  "officer",
  "openxlsx",
  "party",
  "purrr",
  "randomcoloR",
  "reshape2",
  "reticulate",
  "rlang",
  "RMariaDB",
  "rstatix",
  "rvg",
  "showtext",
  "styler",
  "survival",
  "survminer",
  "swimplot",
  "tibble",
  "tidier",
  "webshot",
  "yaml",
  "tidyverse"
)

# Filter out packages that are already installed via conda
to_install <- setdiff(required_packages, skip_packages)

install.packages(to_install)

# Install this.path from CRAN or GitHub if needed
if (!requireNamespace("this.path", quietly = TRUE)) {
  message("Attempting to install 'this.path' from CRAN...")
  tryCatch(
    {
      install.packages("this.path")
    },
    error = function(e) {
      message("CRAN install failed, attempting GitHub install...")
      if (!requireNamespace("remotes", quietly = TRUE)) {
        install.packages("remotes")
      }
      remotes::install_github("ArcadeAntics/this.path")
    }
  )
}

# Bioconductor packages
biocpackages <- c("ComplexHeatmap")

if (!require("BiocManager", quietly = TRUE)) {
  install.packages("BiocManager")
}

BiocManager::install(biocpackages, force = TRUE)

# Install phantomjs (needed for webshot)
webshot::install_phantomjs(force = TRUE)
