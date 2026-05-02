# Roadmap — Methods Deferred for Later

The five chapters in this repo (Association Rules, BCG, RFM, CLV, Insights) cover the *core* of modern retail analytics. This document records the methods we considered and consciously deferred — each is a candidate for a future chapter when there's time / appetite.

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

## 4. Causal Uplift — Did the Discount Cause the Purchase?

**Question it answers:** *Among customers who got a discount and bought, how many would have bought anyway? Should we target discounts narrowly (uplift > 0) or stop offering them altogether?*

This is a **causal** question, not a predictive one. Standard ML predicts "given these features, how likely is purchase?" Uplift modeling predicts "given these features, how much does the *treatment* shift purchase probability?"

**Tools**
- Python: [`econml`](https://econml.azurewebsites.net/) (Microsoft Research), [`causalml`](https://github.com/uber/causalml) (Uber), [`dowhy`](https://www.pywhy.org/dowhy/)

**Sketch**

```python
from econml.metalearners import TLearner
from sklearn.ensemble import RandomForestRegressor

# Treatment = had discount, outcome = future revenue / repurchase
# Confounders = customer features (RFM, CLV, cohort)
T = (df["discount_amount"] > 0).astype(int)   # treatment indicator
Y = future_revenue_per_customer                # outcome
X = customer_feature_matrix                    # confounders

learner = TLearner(models=RandomForestRegressor())
learner.fit(Y, T, X=X)

# Per-customer uplift estimate
uplift = learner.effect(X)
```

**Data requirements:** 🟡 *partial.* We have `discount_amount` and `discount_type` per line item. **Caveat that needs to be loud in the chapter:** in the synthetic data, discounts are randomly assigned. In real data, *they aren't* — discounts go to specific customers in specific contexts, which creates confounding. Causal claims from observational data require either an RCT or careful instrumental-variable / propensity-score arguments. With a real dataset, this analysis would require knowing *how* discounts are assigned in the source business.

**Effort:** 1 chapter, ~full-session. The methodology section needs to be careful about what *can* and *cannot* be claimed.

**Why this matters:** uplift modeling is the modern frontier of marketing analytics. It's where data science meets causal inference. A solid chapter here is the most "senior-level" piece of the portfolio.

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
