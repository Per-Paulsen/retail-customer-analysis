"""Build ``notebooks/rfm_clustering.ipynb`` from declarative cells.

Producing the notebook from a Python script keeps it reviewable in PRs
(JSON diffs of executed notebooks are unreadable). Run once to regenerate
the committed `.ipynb` whenever the cell content changes.

Usage::

    python scripts/build_notebook.py

Dependencies: ``nbformat`` (ships with Jupyter).
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "notebooks"
    / "rfm_clustering.ipynb"
)


CELLS: list[tuple[str, str]] = [
    (
        "markdown",
        """\
# RFM Clustering — A Standalone Walkthrough

Segment a retail catalog by **R**ecency, **F**requency, and **M**onetary value, then visualize the result as an interactive 3D scatter.

This notebook is fully self-contained — it loads the synthetic dataset directly from the project's GitHub repository and runs end-to-end with no local setup. Click *Open in Colab* and go.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Per-Paulsen/retail-customer-analysis/blob/main/notebooks/rfm_clustering.ipynb)

> The full project, including R-side equivalents and a complete Quarto site, lives at [github.com/Per-Paulsen/retail-customer-analysis](https://github.com/Per-Paulsen/retail-customer-analysis).
""",
    ),
    (
        "code",
        """\
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

DATA_URL = (
    "https://raw.githubusercontent.com/Per-Paulsen/retail-customer-analysis"
    "/main/data/synthetic/transactions.csv"
)
LOCAL_PATH = "../data/synthetic/transactions.csv"

source = LOCAL_PATH if os.path.exists(LOCAL_PATH) else DATA_URL
df = pd.read_csv(source, sep=";", parse_dates=["date"])
print(f"Loaded {len(df):,} line items from {source}")
df.head()
""",
    ),
    (
        "markdown",
        """\
## What we're computing

For each unique **product** (here `article_name` — different SKUs of the same product roll up together), we compute:

| Metric | Definition | Direction |
|---|---|---|
| **Recency** | Months since the article's last sale, measured from a reference date | Lower = better |
| **Frequency** | Number of line items the article appears in | Higher = better |
| **Monetary** | Total gross revenue the article generated | Higher = better |

We use 2017-06-30 (the last day of the data window) as the reference date.
""",
    ),
    (
        "code",
        """\
REF_DATE = pd.Timestamp("2017-06-30")

rfm = (
    df.groupby("article_name")
    .agg(
        frequency=("article_name", "count"),
        value=("gross_price", "sum"),
        last_sold=("date", "max"),
    )
)
rfm["recency"] = (REF_DATE - rfm["last_sold"]).dt.days / 30.4375  # months
rfm = rfm[["recency", "frequency", "value"]]

print(f"{len(rfm)} articles | recency range [{rfm['recency'].min():.1f}, {rfm['recency'].max():.1f}] months")
rfm.describe().round(2)
""",
    ),
    (
        "markdown",
        """\
## Choosing the number of clusters

Standardize the three RFM dimensions to unit scale (otherwise *value* — measured in thousands of euros — would swamp the others), then run k-means for a sweep of *k* values and look for the elbow:
""",
    ),
    (
        "code",
        """\
features = StandardScaler().fit_transform(rfm[["recency", "frequency", "value"]])

ks = range(1, 11)
inertias = [KMeans(n_clusters=k, random_state=42, n_init=10).fit(features).inertia_ for k in ks]

elbow = px.line(x=list(ks), y=inertias, markers=True,
                labels={"x": "Number of clusters", "y": "Within-cluster SS"},
                title="Elbow plot — pick where the curve bends")
elbow.update_layout(width=720, height=360)
elbow.show()
""",
    ),
    (
        "markdown",
        """\
The bend lands around **k = 4**. Fit that, then rank clusters from best (high frequency + value, low recency) to worst:
""",
    ),
    (
        "code",
        """\
K = 4
km = KMeans(n_clusters=K, random_state=42, n_init=25).fit(features)
rfm["cluster"] = km.labels_

# Centers in standardized space — combine into a single weighted score
centers = pd.DataFrame(km.cluster_centers_, columns=["recency_z", "frequency_z", "value_z"])
centers["score"] = (centers["frequency_z"] + centers["value_z"] - centers["recency_z"]) / 3
centers["rank"] = centers["score"].rank(ascending=False).astype(int)

rfm["rank"] = rfm["cluster"].map(centers["rank"])
centers.round(3)
""",
    ),
    (
        "markdown",
        """\
## The 3D view

Drag to rotate, scroll to zoom. Hover for the article name. Cluster numbers are *ranked*: rank 1 is the healthy core, rank 4 is the dying tail.
""",
    ),
    (
        "code",
        """\
plot_df = rfm.reset_index()
plot_df["rank"] = plot_df["rank"].astype(str)

fig = px.scatter_3d(
    plot_df,
    x="recency", y="frequency", z="value",
    color="rank", hover_name="article_name",
    color_discrete_sequence=["#27ae60", "#3498db", "#f39c12", "#c0392b"],
    category_orders={"rank": ["1", "2", "3", "4"]},
    title="RFM space — each point is one product",
)
fig.update_traces(marker=dict(size=6, opacity=0.85))
fig.update_layout(
    scene=dict(
        xaxis_title="Recency (months since last sale)",
        yaxis_title="Frequency",
        zaxis_title="Monetary value (EUR)",
    ),
    width=820, height=600,
)
fig.show()
""",
    ),
    (
        "markdown",
        """\
## Cluster narrative

A textual summary of who lives in each rank:
""",
    ),
    (
        "code",
        """\
def head_examples(g, n=4):
    return ", ".join(g.sort_values("value", ascending=False).head(n).index)

summary = (
    rfm
    .reset_index()
    .groupby("rank")
    .agg(
        n_products=("article_name", "count"),
        mean_recency=("recency", "mean"),
        mean_frequency=("frequency", "mean"),
        mean_value=("value", "mean"),
    )
    .round({"mean_recency": 2, "mean_frequency": 0, "mean_value": 0})
)
summary["examples"] = (
    rfm.reset_index().groupby("rank")
    .apply(lambda g: ", ".join(g.nlargest(4, "value")["article_name"].tolist()),
           include_groups=False)
)
summary.sort_index()
""",
    ),
    (
        "markdown",
        """\
## A simple deployable rule

A shallow decision tree turns the cluster boundaries into plain `if`-thresholds — useful when the production system shouldn't carry a clustering library:
""",
    ),
    (
        "code",
        """\
tree = DecisionTreeClassifier(max_depth=3, random_state=42).fit(
    rfm[["recency", "frequency", "value"]], rfm["rank"]
)
print(export_text(
    tree,
    feature_names=["recency", "frequency", "value"],
    class_names=[str(i) for i in sorted(rfm["rank"].unique())],
))
""",
    ),
    (
        "markdown",
        """\
## Takeaway

Four clusters, derived purely from the data, separate the catalog into a healthy core, a long middle, and a dying tail. The synthesis encoded *declining* trends for `filing_cabinet` and `dvd_player` — and they reliably end up in rank 4. The framework transfers to any entity you can summarize as (recency, frequency, monetary): customers, products, suppliers, content items.

For the R version of this same analysis (with `kmeans` and `rpart` instead of `sklearn`), see the [Quarto site chapter](https://github.com/Per-Paulsen/retail-customer-analysis/blob/main/03-cluster-3d-rfm.qmd).
""",
    ),
]


def build() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell(content) if kind == "markdown" else nbf.v4.new_code_cell(content)
        for kind, content in CELLS
    ]
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "pygments_lexer": "ipython3",
        },
        "colab": {"provenance": []},
    }
    return nb


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    nb = build()
    nbf.write(nb, OUTPUT_PATH)
    print(f"Wrote {OUTPUT_PATH} ({len(nb['cells'])} cells)")


if __name__ == "__main__":
    main()
