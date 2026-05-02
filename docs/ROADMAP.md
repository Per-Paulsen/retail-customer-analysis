# Roadmap — Methods Considered

This document tracks the methodological roadmap of the project. The first four entries (survival analysis, demand forecasting, product embeddings, causal uplift) were on the original deferred list and have since been implemented as chapters 06–09. The remaining items are lower-priority candidates kept here for completeness.

The list is ranked by *expected portfolio impact* given the data we have.

---

## ✅ 1. Survival Analysis — Time-to-First-Repeat

**Status:** **Implemented** as [Chapter 06 — Survival Analysis](../06-survival.qmd). Kaplan-Meier on time-to-second-purchase plus Cox PH with covariates from the first basket. Synthetic data has no covariate-driven effects by design (lifetime and rate are random per customer), so the chapter doubles as an honest demonstration of how to read a "no significant effects" result. Mechanics transfer directly to real data with structural effects.

---

## ✅ 2. Demand Forecasting at Category Level

**Status:** **Implemented** as [Chapter 07 — Demand Forecasting](../07-forecasting.qmd). Monthly revenue per product group with a 3-month holdout, four models compared (naive, seasonal naive, ETS, SARIMA), MAE in EUR + MAPE per category. The chapter doubles as a real-world honest case study: with only 24 months of data the dominant finding is that simple baselines often beat fancier seasonal models — a classic forecasting result that survives every M-competition. Pivoted from `statsforecast` to `statsmodels` because statsforecast's scipy pin clashed with the Python 3.14 environment; statsmodels is pure-Python and dependable.

---

## ✅ 3. Product Embeddings — PPMI × SVD

**Status:** **Implemented** as [Chapter 08 — Product Embeddings](../08-embeddings.qmd). Pivoted from `gensim`'s word2vec to PPMI + Truncated SVD because gensim's wheel build failed on Python 3.14 — and the two are mathematically equivalent (Levy & Goldberg 2014). Outputs cosine-similarity tables, a t-SNE projection that recovers the catalog category structure without ever seeing the labels, and a substitution lookup. With 40 product names the geometry is real but a bit noisy; the technique scales cleanly to thousands of SKUs.

---

## ✅ 4. Causal Uplift — Did the Discount Cause the Repeat Purchase?

**Status:** **Implemented** as [Chapter 09 — Causal Uplift](../09-causal-uplift.qmd). Naive ATE plus T-learner and S-learner meta-learners on first-purchase discount → repurchase. CIs straddle zero (correct for random-discount synthetic data); a synthetic injection check confirms the technique recovers structure when present. Pivoted from `econml`/`causalml` to plain scikit-learn — the meta-learners are 5-line implementations and the heavyweight causal libraries had Python 3.14 wheel-build issues.

The chapter is loud about the methodology caveats: random treatment assignment in the data makes the analysis clean, but observational data with confounding needs propensity weighting / doubly-robust estimators / DR-learner before causal claims hold.

---

## 5. Lower-priority / future-future items

These are real techniques but the cost/benefit is poor for *this* dataset:

- **Hierarchical Bayesian RFM** — fit a hierarchical model over the RFM clusters. Better uncertainty quantification, but the BG/NBD chapter already has the probabilistic angle covered.
- **Sequence/Markov models for purchase paths** — what's typically the *first* purchase, what's the *second*? Useful for very large catalogs with clear customer journeys; sparse with 40 items.
- **Anomaly detection** — flag unusual baskets / customers. Mostly useful for fraud / data quality. Not a portfolio differentiator.
- **Recommender system (collaborative filtering, matrix factorization)** — would need substantially more customers (~10k+) for meaningful results.
- **Network analysis on co-purchase graphs** — turn association rules into a network, run community detection. Pretty visualizations, modest insight beyond what we already have.

## How to add a new chapter

1. Pick a method from the list above.
2. Create `0X-method.qmd` (next available number).
3. Add it to `_quarto.yml` navbar, `index.qmd`, and `README.md`.
4. If new dependencies: add to `requirements.txt` (Python) or `R/install_packages.R` (R), and to `.github/workflows/publish.yml` if needed.
5. Render locally first (`quarto render 0X-method.qmd`), then push.
