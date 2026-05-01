# Roadmap — Methods Deferred for Later

The five chapters in this repo (Association Rules, BCG, RFM, CLV, Insights) cover the *core* of modern retail analytics. This document records the methods we considered and consciously deferred — each is a candidate for a future chapter when there's time / appetite.

The list is ranked by *expected portfolio impact* given the data we have.

---

## ✅ 1. Survival Analysis — Time-to-First-Repeat

**Status:** **Implemented** as [Chapter 06 — Survival Analysis](../06-survival.qmd). Kaplan-Meier on time-to-second-purchase plus Cox PH with covariates from the first basket. Synthetic data has no covariate-driven effects by design (lifetime and rate are random per customer), so the chapter doubles as an honest demonstration of how to read a "no significant effects" result. Mechanics transfer directly to real data with structural effects.

---

## 2. Demand Forecasting at Category Level

**Question it answers:** *How many units of each product category will we sell in the next 1, 3, 6 months? When should we order garden furniture for next spring?*

SKU-level forecasting on this data is hopeless (66 SKUs × 24 months ≈ too sparse), but **product-group level** (10 groups × 24 months = 240 monthly observations) is enough for meaningful seasonal models.

**Tools**
- Python: [`prophet`](https://facebook.github.io/prophet/), [`statsforecast`](https://nixtla.github.io/statsforecast/) (modern, fast SARIMA / ETS / Theta)
- R: `forecast` (Hyndman), `prophet`

**Sketch**

```python
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA, AutoETS

# Aggregate to monthly category revenue
monthly = (df.assign(month=df["date"].dt.to_period("M"))
             .groupby(["month", "product_group"])["gross_price"].sum().reset_index())

# Fit per-category, predict 6 months ahead
sf = StatsForecast(models=[AutoARIMA(), AutoETS()], freq="MS")
sf.fit(monthly.rename(columns={"product_group": "unique_id", "month": "ds", "gross_price": "y"}))
forecast = sf.predict(h=6)
```

**Data requirements:** ✅ have date + revenue + category. *Caveat:* 24 months barely covers 2 seasonal cycles, so seasonal patterns will be uncertain. With more data, this is much stronger.

**Effort:** 1 chapter, ~half-session. Best presented with cross-validation (rolling-origin) to show forecast accuracy isn't fiction.

**Why this matters:** every retailer wants this. It's the single most-requested analysis in the wild.

---

## 3. Product Embeddings — Prod2Vec / Item2Vec

**Question it answers:** *Which products are functionally similar? If A is out of stock, what does the customer reach for instead? Where are the gaps in our catalog?*

Apply word2vec (skip-gram) on transactions, treating each basket as a "sentence" of product names. Similar products end up with similar vectors — even if they were never purchased together, as long as they have similar co-purchase neighborhoods.

**Tools**
- Python: `gensim` for Word2Vec, `umap-learn` or `scikit-learn` t-SNE for visualization, `faiss` for similarity lookup

**Sketch**

```python
from gensim.models import Word2Vec
import umap

baskets = df.groupby("transaction_id")["article_name"].apply(list).tolist()
model = Word2Vec(sentences=baskets, vector_size=32, window=5, min_count=3,
                 sg=1, epochs=200, seed=42)

# Embedding for one product
sofa_vec = model.wv["sofa"]
# Most similar items
print(model.wv.most_similar("sofa", topn=5))

# 2D visualization with UMAP
emb_2d = umap.UMAP(random_state=42).fit_transform(model.wv.vectors)
```

**Data requirements:** ✅ have baskets. *Caveat:* with 40 unique product names, embeddings are largely a didactic exercise — there's not much to learn beyond what association rules already show. With 1,000+ SKUs the technique becomes genuinely valuable.

**Effort:** 1 chapter, ~half-session. The visualization (UMAP scatter colored by product group) is the wow piece.

**Modern extension:** train embeddings *with customer context* (CBOW with customer_id as a token) — gets you toward neural collaborative filtering.

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
