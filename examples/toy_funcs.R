#!/usr/bin/env Rscript
# examples/toy_funcs.R

# Simple helper that adds two numbers and scales the result
add_and_scale <- function(x, y, scale = 1) {
  res <- (x + y) * scale
  return(list(result = res))
}

# Returns a simple data.frame demonstrating a repeated multiplication
multiply_table <- function(a, b, times = 3) {
  vals <- seq_len(times)
  df <- data.frame(
    a = a * vals,
    b = b * vals,
    product = (a * vals) * (b * vals)
  )
  return(df)
}

# Returns a list of data.frames
make_list_of_dfs <- function() {
    list(
        df1 = data.frame(a = 1:3),
        df2 = data.frame(b = 4:6)
    )
}
