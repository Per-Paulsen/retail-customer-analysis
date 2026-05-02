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
| `department` | string | Top-level store section (`Living`, `Bedroom`, `Dining`, `Office`, `Storage`, `Outdoor`) |
| `product_group` | string | 4-character category code (e.g. `DINI`, `LIVI`) — the analytical default for grouping |
| `bundle_group` | string | Functional product-system membership (e.g. `bed_system`, `dining_system`) — empty for standalone items. Used by the [data audit](../00-data-audit.qmd) chapter to flag definitional co-purchases. |
| `supplier_id` | string | Supplier identifier |
| `discount_type` | int | `0` = none, `1` = line-level, `2` = order-level |
| `discount_amount` | float | Absolute discount applied to this line |
| `discount_percentage` | float | Discount as fraction of gross |
| `discount_reason` | string | Single-character code, or empty |

**Removed columns** (relative to the original): customer last name, salesperson, free-form order text, raw split of line/order discounts. These were either personally identifiable or redundant after consolidation.

## Product hierarchy

The catalog has a 5-level hierarchy that downstream analyses use at different granularities — pick the level that matches the analytical question, not always the finest one:

```
Department      6 sections        Living, Bedroom, Dining, Office, Storage, Outdoor
    │
    └── Category (product_group)   10 codes        BEDR, BIN, DECO, DINI, ELEC, ...
            │
            └── Family (article_name)   40 names    bed, mattress, sofa, ...
                    │
                    └── Model           ~20 series  harmony, milano, kompakt, oak, walnut, ...
                            │
                            └── SKU (article_id)   66 stock keeping units   B3001, B3002, ...
```

| Level | Granularity | Used by |
|---|---|---|
| **Department** | Store-floor section | Demand forecasting (highest signal-to-noise on this dataset), executive reporting |
| **Category** (`product_group`) | Functional category | Drill-down forecasting, RFM-style segmentation |
| **Family** (`article_name`) | The product, ignoring variants | **Default for most analyses**: association rules, BCG/RFM clustering, embeddings |
| **Model** | Variant within a family | Pricing analysis, supplier reporting |
| **SKU** (`article_id`) | Unique stock unit | Inventory, point-of-sale, embedding lookups in production |

The Family level is the analytical default because (a) it groups variants of the same product together (`bed-harmony`, `bed-milano`, `bed-kompakt` → `bed`), which is what cross-sell logic should care about, and (b) at 40 distinct names the count is dense enough for clustering and rule mining without being so fine-grained that signal disappears into noise.

Department mapping:

| Department | Categories | Rationale |
|---|---|---|
| **Living** | LIVI, DECO, LIGH, ELEC | Living-room ecosystem: furniture, decor, lighting, entertainment electronics |
| **Bedroom** | BEDR | Bedroom furniture and bedding |
| **Dining** | DINI, KITC | Eating spaces — formal dining + kitchen |
| **Office** | OFFI | Workspace furniture |
| **Storage** | STOR | Standalone storage pieces |
| **Outdoor** | OUTD | Garden and patio |

## Original German schema (for reference)

The historical raw file uses these columns. `scripts/preprocess_real_data.py` normalizes them into the target schema above so all chapters can load real and synthetic data through the same code path:

| Original | Mapped to | Notes |
|---|---|---|
| `Kaufvertragsnummer` | `transaction_id` | |
| `Kaufvertragsposition` | `line_item` | |
| `Nachname` | `customer_id` | PII — hashed (md5 → deterministic 5-digit ID) |
| `Menge` | `quantity` | |
| `Artikelnummer` | `article_id` | |
| `Artikel_Bezeichnung` | `article_name` | Normalised to the synth family vocabulary (`bed`, `sofa`, `dining_table`, …) via `FAMILY_PATTERNS`. The raw 2,200 German Artikelbezeichnungen collapse to ~50 families; ~85% of rows match a pattern, the rest land with `article_name=""`. |
| `Model_Bezeichnung` | `model` | First token only |
| `Brutto_VKP` | `gross_price` | |
| `Netto_VKP` | `net_price` | |
| `Netto_EKP` | `net_cost` | |
| `Verkaufer` | *(dropped)* | Salesperson — PII |
| `Bestelltext` | *(dropped)* | PII |
| `Datum` | `date` | Format `DD.MM.YYYY` → ISO |
| `Warengruppe` | `department`, `product_group` | First 2 digits → `department` via `DEPARTMENT_MAP` (with name-pattern fallback for missing codes) and → `product_group` via `PRODUCT_GROUP_MAP`, which collapses the ~30 numeric source codes onto the 10-code synthetic taxonomy (`DINI`, `LIVI`, …) |
| `Lieferantennummer` | `supplier_id` | |
| `Position_Nachlass` / `Gesamt_Nachlass` | consolidated → `discount_amount` | |
| `Position_Nachlass_p` / `Gesamt_Nachlass_p` | consolidated → `discount_percentage` | |
| `Position_Nachlass_Grund` / `Gesamt_Nachlass_Grund` | consolidated → `discount_reason` | First character only |
| (derived) | `discount_type` | `0` if both zero, `1` if line-level only, `2` otherwise |
| (derived) | `bundle_group` | From `article_name` via `BUNDLE_PATTERNS` regex |

**Filtered out during preprocessing** (real-data path only):
- Rows with `Warengruppe` codes `50` (Gutschrift) or `70` (Transportkosten) — accounting line items, not product sales (mapped to `department="Other"` then dropped).
- Rows with missing/empty `date` or `article_name`.

**Known gaps** (real-data path):
- Rows where `Warengruppe` is missing *and* the `article_name` doesn't match any `NAME_DEPARTMENT_PATTERNS` entry land with `department=""` and `product_group=""`. These remain in the dataset (~5% of rows) and surface as a residual category in department-level aggregations.
- Rows whose raw German Artikelbezeichnung doesn't match any `FAMILY_PATTERNS` entry land with `article_name=""` (~15% of rows). These remain in the dataset; chapters that group on `article_name` either filter them or treat them as their own bucket.

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
