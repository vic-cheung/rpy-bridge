#!/usr/bin/env Rscript
# examples/toy_more_funcs.R

# Returns a numeric sequence, optionally reversed
seq_vector <- function(start = 1, end = 5, step = 1, reverse = FALSE) {
  vec <- seq(from = start, to = end, by = step)
  if (reverse) {
    vec <- rev(vec)
  }
  return(vec)
}

# Returns a data.frame of squared numbers
square_table <- function(n = 5) {
  df <- data.frame(
    num = 1:n,
    squared = (1:n)^2
  )
  return(df)
}

# Returns a named list with mixed types
make_named_list <- function() {
  list(
    numbers = 1:3,
    letters = c("x", "y", "z"),
    flags = c(TRUE, FALSE, TRUE)
  )
}
