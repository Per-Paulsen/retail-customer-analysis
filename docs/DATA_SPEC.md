# Data Specification

This document describes the schema of the transaction dataset and the design choices behind the synthetic version.

## Target schema (English, post-cleaning)

The synthetic dataset and the cleaned version of the real dataset share this schema:

| Column | Type | Description |
|---|---|---|
| `customer_id` | string | Customer identifier (one per repeat-buyer; `transaction_id` is unique per basket) |
| `transaction_id` | string | Purchase contract identifier (one per basket / customer visit) |
| `line_item` | int | Position within the transaction (1, 2, 3, …) |
| `article_id` | string | SKU identifier (multiple SKUs may share the same `article_name`) |
| `article_name` | string | Normalized product name (lowercase, single token) |
| `model` | string | Model/series name |
| `quantity` | int | Units purchased on this line |
| `gross_price` | float | Sales price per unit, including VAT |
| `net_price` | float | Sales price per unit, excluding VAT |
| `net_cost` | float | Purchase cost per unit (for the retailer) |
| `date` | date (YYYY-MM-DD) | Transaction date |
| `product_group` | string | 4-character category code (e.g. `DINI`, `LIVI`) |
| `supplier_id` | string | Supplier identifier |
| `discount_type` | int | `0` = none, `1` = line-level, `2` = order-level |
| `discount_amount` | float | Absolute discount applied to this line |
| `discount_percentage` | float | Discount as fraction of gross |
| `discount_reason` | string | Single-character code, or empty |

**Removed columns** (relative to the original): customer last name, salesperson, free-form order text, raw split of line/order discounts. These were either personally identifiable or redundant after consolidation.

## Original German schema (for reference)

The historical raw file used these columns. The preprocessing step normalizes and renames them:

| Original | Mapped to | Notes |
|---|---|---|
| `Kaufvertragsnummer` | `transaction_id` | |
| `Kaufvertragsposition` | `line_item` | |
| `Nachname` | *(dropped)* | PII |
| `Menge` | `quantity` | |
| `Artikelnummer` | `article_id` | |
| `Artikel_Bezeichnung` | `article_name` | Normalized: lowercase, LED prefix stripped, "tv-" → "fernseh", "Xer" → "sofa", first token only |
| `Model_Bezeichnung` | `model` | First token only |
| `Brutto_VKP` | `gross_price` | |
| `Netto_VKP` | `net_price` | |
| `Netto_EKP` | `net_cost` | |
| `Verkaufer` | *(dropped)* | Salesperson — not needed for the analyses |
| `Bestelltext` | *(dropped)* | Duplicate of `Nachname` per source comment |
| `Datum` | `date` | Format `DD.MM.YYYY` → ISO |
| `Warengruppe` | `product_group` | First 4 characters |
| `Lieferantennummer` | `supplier_id` | |
| `Position_Nachlass` / `Gesamt_Nachlass` | consolidated → `discount_amount` | |
| `Position_Nachlass_p` / `Gesamt_Nachlass_p` | consolidated → `discount_percentage` | |
| `Position_Nachlass_Grund` / `Gesamt_Nachlass_Grund` | consolidated → `discount_reason` | First character only |
| (derived) | `discount_type` | `0` if both zero, `1` if line-level only, `2` otherwise |

## Synthetic dataset design

The synthesis is calibrated so that the three downstream analyses produce non-trivial, interpretable results.

### Volume

| Quantity | Value | Rationale |
|---|---|---|
| Customers | 2,400 | Heavy-tailed transaction count per customer (see below) |
| Transactions | ~3,500 | Average ~1.46 transactions per customer |
| Line items | ~6,400 | Average basket size ~1.8 |
| Date range | 2015-07-01 to 2017-06-30 | Two years; midpoint 2016-06-30 used as BCG split |
| Unique articles (`article_id`) | 66 | |
| Unique article names | 40 | Multiple SKUs per name (different models / price points) |
| Product groups | 10 | DINI, LIVI, BEDR, OFFI, LIGH, ELEC, DECO, STOR, KITC, OUTD |

### Customer-level structure (for CLV / BG/NBD)

Customers are generated with a BG/NBD-shaped process so that the CLV chapter can fit a model whose assumptions are actually satisfied by the data:

- **First purchase date** — uniform within the window. Customers arriving late are observed for less time (right-censored).
- **Lifetime** — exponential with mean 250 days. Most customers churn well before the window ends.
- **Transaction rate while alive** — Gamma-distributed (shape 2.0, scale 0.5 → mean ≈ 1 tx/year). Heterogeneous across customers.
- **Repeat purchases** — Poisson with rate · observed-lifetime.

This produces the canonical retail mix: ~70% one-time buyers, ~25% with 2–4 transactions, ~5% with 5+. A non-trivial fraction of customers is "still alive" at window end (last purchase recent, lifetime not yet expired) — exactly the situation BG/NBD is designed to disentangle from "permanently churned" (last purchase long ago, likely dead).

### Co-purchase patterns (for association rules)

Encoded co-purchase probabilities so that Apriori finds meaningful rules at `support ≥ 0.001, confidence ≥ 0.5`:

| Anchor article | Likely co-purchases (probability) |
|---|---|
| `dining_table` | `dining_chair` (0.85), `table_extension` (0.40), `sideboard` (0.20) |
| `bed` | `mattress` (0.70), `nightstand` (0.40), `headboard` (0.30) |
| `sofa` | `coffee_table` (0.30), `armchair` (0.20), `rug` (0.20) |
| `desk` | `office_chair` (0.65), `bookshelf` (0.20) |
| `tv` | `soundbar` (0.25), `speakers` (0.15) |
| `kitchen_table` | `kitchen_chair` (0.75) |
| `garden_table` | `garden_chair` (0.70), `parasol` (0.30) |

### Temporal trends (for BCG growth/share and RFM recency)

A subset of articles has time-dependent selection weights:

- **Growing**: weight ramps linearly from 0× (window start) to 2× (window end). These articles barely appear in the first months and dominate by the end. Examples: `ottoman`, `led_strip`, `garden_chair`, `garden_table`, `parasol`.
- **Declining**: weight ramps linearly from 2× (start) to 0× (end). These vanish by the end of the window, producing real recency variation in the data (last-seen dates of several months). Examples: `filing_cabinet`, `dvd_player`.
- **Stable**: constant weight throughout (everything else).

The hard-zero endpoints are intentional: without them, every article would have a last-purchase date in the final week or two of the window, squashing recency to zero and making RFM clustering uninformative.

### Variation (for RFM)

- **Recency** is induced by spreading purchase dates non-uniformly per article (some articles cluster near start, some near end of the window)
- **Frequency** is induced by varying baseline popularity per article (~10× spread between rare and common SKUs)
- **Monetary value** is induced by base prices spanning ~€20 (small decor) to ~€2,500 (sofas, beds)

### Reproducibility

The generator uses a fixed seed (`SEED = 42`). Re-running `scripts/generate_synthetic_data.py` always produces the same `data/synthetic/transactions.csv`.
