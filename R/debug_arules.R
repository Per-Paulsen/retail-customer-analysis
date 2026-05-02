.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))
Sys.setlocale("LC_COLLATE", "C")
suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(arules)
})

raw <- read_delim(
  "C:/Users/perpa/Dev/retail-customer-analysis/data/raw/transactions.csv",
  delim = ";", show_col_types = FALSE
)
clean <- raw[!is.na(raw$article_name) & nchar(trimws(raw$article_name)) > 0, ]
clean$article_name <- trimws(clean$article_name)

# Try with sort() on each basket
baskets <- split(clean$article_name, clean$transaction_id)
baskets <- lapply(baskets, function(b) sort(unique(b)))

result <- tryCatch({
  trans <- as(baskets, "transactions")
  cat(sprintf("Conversion success! %d transactions, %d items\n",
              length(trans), ncol(trans)))
  "success"
}, error = function(e) paste("Error:", conditionMessage(e)))
cat(result, "\n")
