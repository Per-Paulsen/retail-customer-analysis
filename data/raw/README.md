# `data/raw/` — Real data location (gitignored)

This directory is reserved for the original, confidential transaction data from the source retailer. **Nothing in this directory is committed to git** (see `.gitignore`), with the exception of this README and `.gitkeep`.

If you have access to the original dataset, place the file as:

```
data/raw/transactions.csv
```

with the column structure described in [`docs/DATA_SPEC.md`](../../docs/DATA_SPEC.md) (Section: *Original German schema*). The analysis scripts will pick it up automatically when `USE_RAW=true` is set as an environment variable; otherwise they default to `data/synthetic/transactions.csv`.

## Why physical separation?

`.gitignore` alone is not enough — a typo in the pattern or an accidental `git add -A` can leak files into history. Keeping the real data in a directory that's both physically separate (originally) **and** gitignored is defense in depth.
