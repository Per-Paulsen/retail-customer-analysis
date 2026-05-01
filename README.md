# Retail Customer & Basket Analysis

End-to-end product analytics on a synthetic two-year retail transaction dataset, demonstrating three classic techniques **side-by-side in R and Python**:

1. **Association Rules / Market Basket Analysis** with `arules` (R) and `mlxtend` (Python)
2. **BCG-style Portfolio Clustering** — products positioned by market share × growth (Python / scikit-learn)
3. **RFM Clustering** — Recency, Frequency, Monetary value, with an interactive 3D view (R / `kmeans` + plotly)

The full analysis is published as a [Quarto](https://quarto.org) website that mixes both languages in a single project. A standalone Python notebook replays the RFM analysis end-to-end in Colab without any local setup.

## Live demo

- **Site:** [per-paulsen.github.io/retail-customer-analysis](https://per-paulsen.github.io/retail-customer-analysis/) *(deployed via GitHub Pages on every push)*
- **Standalone notebook:** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Per-Paulsen/retail-customer-analysis/blob/main/notebooks/rfm_clustering.ipynb)

## What's in here

| Chapter | Language | Tools | Output |
|---|---|---|---|
| [01 — Association Rules](01-association.qmd) | R + Python | `arules`, `arulesViz`, `mlxtend` | Apriori rules at sup ≥ 0.001, conf ≥ 0.5 |
| [02 — BCG Clustering](02-cluster-2d-bcg.qmd) | Python | `scikit-learn`, `seaborn` | k-means quadrants on share × growth |
| [03 — RFM Clustering](03-cluster-3d-rfm.qmd) | R | `kmeans`, `plotly`, `rpart` | 3D segmentation + decision tree |
| [Notebook — RFM in Python](notebooks/rfm_clustering.ipynb) | Python | `scikit-learn`, `plotly` | Self-contained, Colab-ready |

## Reproducing locally

```bash
git clone https://github.com/Per-Paulsen/retail-customer-analysis.git
cd retail-customer-analysis

# Python deps
pip install -r requirements.txt

# R deps (in R, or via Rscript)
Rscript R/install_packages.R

# Generate the deterministic synthetic dataset
python scripts/generate_synthetic_data.py

# Render the Quarto site
quarto render
quarto preview          # auto-reload during editing
```

Prerequisites: Python ≥ 3.10, R ≥ 4.4, [Quarto](https://quarto.org/docs/get-started/) ≥ 1.5.

## Origin

The methodology is based on a 2017 internship project for a German retail company. The original project was three iterative R scripts running on a confidential transaction dump. This repository is a from-scratch modernization with two key changes:

- **No real data.** The dataset in `data/synthetic/` is fully synthesized to preserve confidentiality while reproducing the structural and statistical properties needed to make the analyses meaningful — co-purchase patterns, temporal trends, popularity skew. See [`docs/DATA_SPEC.md`](docs/DATA_SPEC.md) for the schema and the synthesis design.
- **Multi-language.** The original was R-only with monolithic scripts. The modernized version splits the work into focused chapters, mixes R and Python where each language fits best, and uses Quarto so code, output, and explanation live in one document.

## Methods at a glance

**Association rules.** The Apriori algorithm finds rules of the form $A \Rightarrow B$ characterized by *support* (how common the joint occurrence is), *confidence* ($P(B|A)$), and *lift* ($\frac{P(B|A)}{P(B)}$). For this synthetic catalog, mining at sup ≥ 0.001 and conf ≥ 0.5 returns ~300 rules — the simplest and strongest recover engineered patterns like *dining_table → dining_chair* (86% confidence, 8× lift) and *bed → mattress* (69%, 6× lift).

**BCG clustering.** Compute per-product market share (`revenue / total_revenue`) and growth rate (period-over-period revenue change). Standardize, k-means with k=4 — the elbow plot lands cleanly there. The resulting clusters map onto the canonical BCG quadrants (Stars, Cash Cows, Question Marks, Dogs) and a depth-3 decision tree turns the boundaries into deployable if/else rules.

**RFM clustering.** Per product: recency (months since last sale, ref 2017-06-30), frequency (line-item count), monetary value (sum of gross prices). Standardize → k-means with k=4 → rank clusters from healthy core to dying tail. The interactive 3D scatter (plotly in R; the standalone notebook uses plotly in Python) lets you spin the view to see the structure.

## Repository layout

```
retail-customer-analysis/
├── _quarto.yml             # Quarto project config
├── index.qmd               # Landing page
├── 01-association.qmd      # Chapter 1 — R + Python
├── 02-cluster-2d-bcg.qmd   # Chapter 2 — Python
├── 03-cluster-3d-rfm.qmd   # Chapter 3 — R
├── notebooks/
│   └── rfm_clustering.ipynb        # Standalone Colab notebook
├── scripts/
│   ├── generate_synthetic_data.py  # Deterministic dataset generator
│   └── build_notebook.py           # Rebuilds the .ipynb from cell sources
├── R/
│   └── install_packages.R          # One-shot R dependency setup
├── data/
│   ├── raw/                # Real data (gitignored — see data/raw/README.md)
│   └── synthetic/
│       └── transactions.csv        # ~6,300 line items, deterministic seed
├── docs/
│   └── DATA_SPEC.md        # Schema and synthesis design
├── requirements.txt        # Python deps
├── .github/workflows/
│   └── publish.yml         # CI: render + deploy to GitHub Pages
└── LICENSE                 # MIT
```

## License

MIT — see [`LICENSE`](LICENSE).
