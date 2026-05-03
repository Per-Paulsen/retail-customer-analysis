# Bootstrap R packages into the user library.
# Designed for fresh installs where R_LIBS_USER does not yet exist.

user_lib <- Sys.getenv("R_LIBS_USER")
if (user_lib == "") {
  stop("R_LIBS_USER not set; refusing to install to system library.")
}
user_lib <- gsub("\\\\", "/", user_lib)
if (!dir.exists(user_lib)) {
  dir.create(user_lib, recursive = TRUE)
  cat("Created user library:", user_lib, "\n")
}
.libPaths(c(user_lib, .libPaths()))

needed <- c("readr","dplyr","arules","arulesViz","ggplot2",
            "plotly","rpart","rpart.plot","knitr","reticulate",
            "cluster","patchwork","tibble")
already <- rownames(installed.packages())
to_install <- setdiff(needed, already)

cat("Already installed:", paste(intersect(needed, already), collapse = ", "), "\n")
cat("To install      :", paste(to_install, collapse = ", "), "\n\n")

if (length(to_install) > 0) {
  install.packages(
    to_install,
    lib = user_lib,
    repos = "https://cloud.r-project.org",
    Ncpus = 4
  )
}

cat("\nFinal status:\n")
final <- installed.packages()
for (p in needed) {
  rows <- final[final[, "Package"] == p, , drop = FALSE]
  if (nrow(rows) == 0) {
    cat(sprintf("  %-12s MISSING\n", p))
  } else {
    cat(sprintf("  %-12s %s\n", p, rows[1, "Version"]))
  }
}
