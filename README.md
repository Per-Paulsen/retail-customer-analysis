# Retail Customer & Basket Analysis

End-to-end product and customer analytics on a synthetic two-year retail transaction dataset, demonstrating five techniques in both R and Python — from classic market basket analysis to modern probabilistic CLV modeling.

1. **Association Rules / Market Basket Analysis** with `arules` (R) and `mlxtend` (Python)
2. **BCG-style Portfolio Clustering** — products positioned by market share × growth (Python / scikit-learn)
3. **RFM Clustering** — Recency, Frequency, Monetary value, with an interactive 3D view (R / `kmeans` + plotly)
4. **Customer Lifetime Value** — probabilistic CLV with BG/NBD + Gamma-Gamma (Python / `lifetimes`)
5. **Insights synthesis** — cross-cuts between the four upstream chapters with concrete recommendations

The full analysis is published as a [Quarto](https://quarto.org) website that mixes both languages in a single project. There's also a one-page **dashboard view** with KPI cards and tabbed visualizations, and a standalone Python notebook that replays the RFM analysis in Colab.

## Live demo

- **Site:** [per-paulsen.github.io/retail-customer-analysis](https://per-paulsen.github.io/retail-customer-analysis/) *(deployed via GitHub Pages on every push)*
- **Dashboard:** [per-paulsen.github.io/retail-customer-analysis/dashboard.html](https://per-paulsen.github.io/retail-customer-analysis/dashboard.html)
- **Standalone notebook:** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Per-Paulsen/retail-customer-analysis/blob/main/notebooks/rfm_clustering.ipynb)

## What's in here

| Chapter | Language | Tools | Output |
|---|---|---|---|
| [01 — Association Rules](01-association.qmd) | R + Python | `arules`, `arulesViz`, `mlxtend` | Apriori rules at sup ≥ 0.001, conf ≥ 0.5 |
| [02 — BCG Clustering](02-cluster-2d-bcg.qmd) | Python | `scikit-learn`, `seaborn` | k-means quadrants on share × growth |
| [03 — RFM Clustering](03-cluster-3d-rfm.qmd) | R | `kmeans`, `plotly`, `rpart` | 3D segmentation + decision tree |
| [04 — Customer Lifetime Value](04-clv-bgnbd.qmd) | Python | `lifetimes` (BG/NBD + Gamma-Gamma) | Per-customer CLV + P(alive), holdout-validated |
| [06 — Survival Analysis](06-survival.qmd) | Python | `lifelines` (Kaplan-Meier + Cox PH) | Time-to-first-repeat curves, hazard ratios |
| [07 — Demand Forecasting](07-forecasting.qmd) | Python | `statsmodels` (naive, ETS, SARIMA) | Per-category monthly revenue forecasts with backtest |
| [05 — Insights](05-insights.qmd) | Python | Cross-method synthesis | Recommendations + headline findings |
| [Dashboard](dashboard.qmd) | Python | Quarto Dashboard, plotly | KPI tiles + tabbed visual explorer |
| [Notebook — RFM in Python](notebooks/rfm_clustering.ipynb) | Python | `scikit-learn`, `plotly` | Self-contained, Colab-ready |

For methods we considered and deferred — survival analysis, demand forecasting, prod2vec embeddings, causal uplift — see [`docs/ROADMAP.md`](docs/ROADMAP.md).

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

Prerequisites: Python ≥ 3.10, R ≥ 4.5, [Quarto](https://quarto.org/docs/get-started/) ≥ 1.5.

## Origin

The methodology is based on a 2017 internship project for a German retail company. The original was three iterative R scripts running on a confidential transaction dump. This repository is a from-scratch modernization with three key differences:

- **No real data.** The dataset in `data/synthetic/` is fully synthesized to preserve confidentiality while reproducing the structural and statistical properties needed to make the analyses meaningful — co-purchase patterns, temporal trends, popularity skew, customer-level lifetime/frequency structure. See [`docs/DATA_SPEC.md`](docs/DATA_SPEC.md) for the schema and the synthesis design.
- **Multi-language.** The original was R-only with monolithic scripts. The modernized version splits the work into focused chapters, mixes R and Python where each language fits best, and uses Quarto so code, output, and explanation live in one document.
- **Modern methods added.** The original had three classic chapters (rules, BCG, RFM). The modernized version adds probabilistic CLV with BG/NBD + Gamma-Gamma, a synthesis chapter that cross-references the upstream analyses, and a dashboard summary. Future-work methods are documented in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Methods at a glance

**Association rules.** The Apriori algorithm finds rules of the form $A \Rightarrow B$ characterized by *support*, *confidence* ($P(B|A)$), and *lift* ($P(B|A)/P(B)$). Mining at sup ≥ 0.001 and conf ≥ 0.5 returns ~300 rules — the simplest and strongest recover engineered patterns like *dining_table → dining_chair* (~86% confidence, 6× lift).

**BCG clustering.** Per-product market share (`revenue / total_revenue`) and growth rate (period-over-period revenue change). Standardize, k-means with k=4 — elbow lands cleanly there. Maps onto canonical BCG quadrants (Stars, Cash Cows, Question Marks, Dogs).

**RFM clustering.** Per product: recency (months since last sale), frequency (line-item count), monetary value (sum of gross prices). Standardize → k-means with k=4 → rank from healthy core to dying tail. Interactive 3D scatter (plotly).

**Customer Lifetime Value.** BG/NBD models per-customer purchase frequency + dropout probability assuming Gamma-distributed transaction rates and Beta-distributed dropout. Gamma-Gamma models per-transaction value as Gamma-distributed conditional on frequency. Combined: 12-month forecast revenue per customer, validated against a held-out tail of the timeline.

**Survival analysis.** Kaplan-Meier estimates the population survival curve for time-to-first-repeat, with right-censoring on customers who haven't returned yet. Cox proportional hazards adds covariates (basket value, category, discount usage) and reports hazard ratios. Together: *who's still in play, when does the comeback rate flatten, what features speed or slow return?*

**Demand forecasting.** Monthly revenue per product group projected three months ahead with four models (naive, seasonal naive, ETS, SARIMA), backtested on the last quarter and compared by MAE in EUR plus MAPE. The chapter is honest about how 24 months sits at the edge of what classical seasonal models can support — the right answer is often that simple baselines win, which is itself a finding.

**Insights synthesis.** Per-product table joining BCG + RFM ranks; per-rule table annotating top-tier consequents; Lorenz-style CLV concentration curve. Closes with five business recommendations grounded in the cross-cuts.

## Repository layout

```
retail-customer-analysis/
├── _quarto.yml             # Quarto project config
├── index.qmd               # Landing page
├── 01-association.qmd      # Chapter 1 — R + Python
├── 02-cluster-2d-bcg.qmd   # Chapter 2 — Python
├── 03-cluster-3d-rfm.qmd   # Chapter 3 — R
├── 04-clv-bgnbd.qmd        # Chapter 4 — Python
├── 05-insights.qmd         # Chapter 5 — Python (synthesis)
├── 06-survival.qmd         # Chapter 6 — Python (survival analysis)
├── 07-forecasting.qmd      # Chapter 7 — Python (demand forecasting)
├── dashboard.qmd           # Quarto dashboard view
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
│       └── transactions.csv        # ~6,400 line items, deterministic seed
├── docs/
│   ├── DATA_SPEC.md        # Schema and synthesis design
│   └── ROADMAP.md          # Methods deferred for future work
├── requirements.txt        # Python deps
├── .github/workflows/
│   └── publish.yml         # CI: render + deploy to GitHub Pages
└── LICENSE                 # MIT
```

## License

MIT — see [`LICENSE`](LICENSE).
