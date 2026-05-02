# Granularity analysis — real Innatura data

Empirical evaluation of item-level granularity for the analyses in chapters 01 (Apriori), 02 (BCG), 03 (RFM), 05 (Insights), and the dashboard.

The chapters above all group on `article_name`. The synthetic dataset has 40 hand-curated family names (`bed`, `sofa`, `dining_table`, …); the real Innatura source has ~2 200 raw German Artikelbezeichnungen at variable granularity. Picking one item-level definition that fits both data sources isn't trivial — too coarse and the analyses become trivial (`Tisch → Stuhl`), too fine and Apriori finds nothing. This document records the empirical basis for the choice.

Reproducible: `python scripts/granularity_analysis.py --save` regenerates the tables below.

## Options tested

| Option | Definition | Real-data unique items |
|---|---|---|
| `raw` | `Artikelbezeichnung` exactly as stored | 2 198 |
| `light_norm` | `raw` with lowercase + accent-strip + collapse whitespace/punct | 2 108 |
| `model` | `Modellbezeichnung` alone | 3 311 |
| `family_model` | light-normed name + " " + light-normed model | 5 322 |
| `sku` | `article_id` (the inventory unit) | 3 534 |
| `family_synth` | The C1 mapping that collapses raw onto the 49-code synth vocabulary | 44 |
| `product_group` | Synth-aligned 10-code category from C1's PG-map (`DINI`, `LIVI`, …) | 8 |

Source: `Datenbasis.csv`, 17 103 line items, 7 244 baskets, 3 534 unique SKUs (after dropping accounting-only Warengruppen 50/70 and rows with missing date/article).

## Density per option

How many items have *enough basket-presence* to participate in Apriori? `≥k` columns count items appearing in at least *k* distinct baskets.

| option | unique items | med basket-count | p75 | max | ≥5 | ≥10 | ≥20 |
|---|---|---|---|---|---|---|---|
| `raw` | 2198 | 1 | 3 | 740 | 435 | 224 | 105 |
| `light_norm` | 2108 | 1 | 4 | 740 | 432 | 227 | 104 |
| `model` | 3311 | 1 | 3 | 182 | 564 | 253 | 112 |
| `family_model` | 5322 | 1 | 2 | 125 | 723 | 272 | 98 |
| `sku` | 3534 | 2 | 5 | 151 | 886 | 357 | 100 |
| `family_synth` | 44 | 166 | 373 | 1254 | 42 | 40 | 38 |
| `product_group` | 8 | 338 | 1581 | 3009 | 8 | 7 | 7 |

`family_synth` and `product_group` are pathologically dense — almost every "item" appears in hundreds of baskets, because the items aren't items, they're broad categories. The fine-grained options have long tails: most items appear in 1–3 baskets, with 100–360 items reaching the ≥20 threshold.

## Apriori yield per option × support threshold

Confidence ≥ 0.5, max rule length 2 (single antecedent → single consequent). "Non-trivial" = lift ≥ 2. Cells reading `-1` indicate the option × threshold combination ran out of memory or candidate space.

### `min_support = 0.0001` (≥1 basket — extreme low)

| option | rules | non-trivial | median lift | p75 lift |
|---|---|---|---|---|
| `raw` | 4987 | 4987 | 402.44 | 2414.67 |
| `light_norm` | 4726 | 4726 | 381.26 | 2414.67 |
| `model` | -1 | -1 | 0.00 | 0.00 |
| `family_model` | -1 | -1 | 0.00 | 0.00 |
| `sku` | -1 | -1 | 0.00 | 0.00 |
| `family_synth` | 11 | 11 | 7.00 | 13.93 |
| `product_group` | 0 | 0 | 0.00 | 0.00 |

### `min_support = 0.0005` (≥4 baskets)

| option | rules | non-trivial | median lift | p75 lift |
|---|---|---|---|---|
| `raw` | 231 | 231 | 133.53 | 452.75 |
| `light_norm` | 229 | 229 | 133.53 | 452.75 |
| `model` | 179 | 179 | 517.43 | 804.89 |
| `family_model` | 417 | 417 | 528.21 | 804.89 |
| `sku` | 482 | 482 | 546.04 | 804.89 |
| `family_synth` | 10 | 10 | 6.95 | 7.99 |
| `product_group` | 0 | 0 | 0.00 | 0.00 |

### `min_support = 0.001` (≥7 baskets — chapter default)

| option | rules | non-trivial | median lift | p75 lift |
|---|---|---|---|---|
| `raw` | 73 | 73 | 64.68 | 251.53 |
| `light_norm` | 71 | 71 | 61.13 | 226.46 |
| `model` | 44 | 44 | 179.98 | 253.33 |
| `family_model` | 109 | 109 | 233.68 | 495.32 |
| `sku` | 129 | 129 | 253.39 | 429.27 |
| `family_synth` | 10 | 10 | 6.95 | 7.99 |
| `product_group` | 0 | 0 | 0.00 | 0.00 |

### `min_support = 0.005` (≥36 baskets)

| option | rules | non-trivial | median lift | p75 lift |
|---|---|---|---|---|
| `raw` | 5 | 5 | 28.90 | 28.90 |
| `light_norm` | 5 | 5 | 28.90 | 28.90 |
| `model` | 0 | 0 | 0.00 | 0.00 |
| `family_model` | 4 | 4 | 121.76 | 181.10 |
| `sku` | 1 | 1 | 41.84 | 41.84 |
| `family_synth` | 10 | 10 | 6.95 | 7.99 |
| `product_group` | 0 | 0 | 0.00 | 0.00 |

## Findings

1. **`family_synth` (the C1 mapping) is the worst-of-both-worlds for Apriori.** It produces only 10 rules at any support threshold, with median lift ≈ 7 — i.e. a small set of generic, weakly-associated patterns of the form "table → chair". This is the granularity that landed in the rendered site after C1; statistically it provides almost no signal beyond what a domain expert already knows.

2. **`product_group` is too coarse to be useful.** Zero Apriori rules at every threshold, including `0.0001`. Eight categories simply don't have enough between-category co-purchase patterns to surface anything.

3. **`raw` and `light_norm` are nearly equivalent.** Light normalization (lowercase, accent-strip, whitespace) reduces 2 198 → 2 108 unique items but doesn't materially change the density profile or rule yield. Light normalization is preferable for stability against minor formatting differences.

4. **The fine-grained options (`raw`/`light_norm`/`model`/`family_model`/`sku`) all produce many rules at higher support thresholds with very high lift.** Median lift > 60 across the board at sup=0.001 indicates the rules surface real co-purchase structure rather than noise. The high lifts also reflect that many products are bought together in tight model-line clusters (a Cartago set, an Olivia set), not as random co-occurrence.

5. **`min_support = 0.001` (the chapter default) is statistically appropriate for `light_norm`.** 71 rules is a workable count after triage; lift distribution is healthy (median 61, p75 226).

6. **For more model-specific patterns**, `family_model` at `sup=0.0005` (417 rules) or `sku` at `sup=0.0005` (482 rules) deliver more granular cross-sell signal at the cost of larger output volumes.

## Recommendation per chapter

| Chapter | Granularity | Threshold |
|---|---|---|
| 01 Association | `light_norm` of `article_name` | `sup=0.001`, `conf=0.5` |
| 02 BCG | `light_norm` of `article_name`, plot top-N annotated | — (clustering, not Apriori) |
| 03 RFM | `light_norm` of `article_name`, plot top-N annotated | — |
| 05 Insights | `light_norm` of `article_name`; data-driven prose | `sup=0.001` (mirrors 01) |
| 08 Embeddings | `article_id` (SKU level — already correct) | — |
| dashboard | `light_norm` of `article_name`, top-N annotated | `sup=0.001` |

Customer-level chapters (04 CLV, 06 Survival, 09 Uplift) and aggregate-level chapters (07 Forecasting at department/product_group) are unaffected by item-level granularity.

## Implications for the C1 work

C1 (the `FAMILY_PATTERNS` mapping that produced 49 synth-aligned families) needs to be replaced with the `light_norm` step. The bundle/department mappings in `preprocess_real_data.py` are orthogonal to article_name granularity and stay as they are.
