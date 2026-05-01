"""Generate the synthetic retail transaction dataset.

Produces ``data/synthetic/transactions.csv``. The dataset is calibrated so that
the three downstream analyses (association rules, BCG growth/share clustering,
RFM clustering) yield interpretable, non-trivial results.

See ``docs/DATA_SPEC.md`` for the schema and design rationale.

Dependencies: ``numpy``, ``pandas`` (Python 3.10+).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
N_CUSTOMERS = 2400
DATE_START = date(2015, 7, 1)
DATE_END = date(2017, 6, 30)
VAT = 0.19
COST_RATIO = 0.55  # net_cost ≈ 55% of gross_price

# Customer-level parameters (BG/NBD-shaped so chapter 04 can fit a model that
# matches the generative process, while still producing realistic spread).
# Each customer has an exponential "lifetime" and, while alive, a Gamma-distributed
# transaction rate. Censoring at window_end produces a mix of churned and active
# customers — exactly the situation BG/NBD is designed for.
LIFETIME_DAYS_MEAN = 250
TX_RATE_GAMMA_SHAPE = 2.0
TX_RATE_GAMMA_SCALE = 0.5  # mean rate = shape * scale = 1.0 transactions / year

OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "synthetic"
    / "transactions.csv"
)


@dataclass(frozen=True)
class Article:
    article_id: str
    article_name: str
    model: str
    product_group: str
    base_price: float
    supplier_id: str
    popularity: float
    trend: str  # "stable" | "growing" | "declining"


# Article catalog. Multiple SKUs may share the same article_name (different
# models / price points). Trends drive both BCG growth and RFM recency.
CATALOG: list[Article] = [
    # Living room
    Article("L1001", "sofa",          "harmony",  "LIVI", 1199.00, "S01", 1.00, "stable"),
    Article("L1002", "sofa",          "milano",   "LIVI", 1799.00, "S01", 0.55, "stable"),
    Article("L1003", "sofa",          "kompakt",  "LIVI",  799.00, "S02", 0.75, "stable"),
    Article("L1010", "armchair",      "harmony",  "LIVI",  599.00, "S01", 0.65, "stable"),
    Article("L1011", "armchair",      "luna",     "LIVI",  449.00, "S03", 0.50, "stable"),
    Article("L1020", "coffee_table",  "oak",      "LIVI",  349.00, "S04", 0.70, "stable"),
    Article("L1021", "coffee_table",  "glass",    "LIVI",  279.00, "S04", 0.55, "stable"),
    Article("L1030", "side_table",    "oak",      "LIVI",  119.00, "S04", 0.45, "stable"),
    Article("L1040", "ottoman",       "luna",     "LIVI",  219.00, "S03", 0.40, "growing"),
    Article("L1041", "ottoman",       "kompakt",  "LIVI",  159.00, "S02", 0.35, "growing"),
    Article("L1050", "rug",           "berber",   "LIVI",  189.00, "S05", 0.60, "stable"),
    Article("L1051", "rug",           "shaggy",   "LIVI",  299.00, "S05", 0.50, "stable"),

    # Dining
    Article("D2001", "dining_table",      "oak",     "DINI",  899.00, "S04", 0.85, "stable"),
    Article("D2002", "dining_table",      "walnut",  "DINI", 1299.00, "S04", 0.45, "stable"),
    Article("D2003", "dining_table",      "kompakt", "DINI",  599.00, "S02", 0.55, "stable"),
    Article("D2010", "dining_chair",      "oak",     "DINI",  149.00, "S04", 0.95, "stable"),
    Article("D2011", "dining_chair",      "fabric",  "DINI",  119.00, "S03", 0.85, "stable"),
    Article("D2012", "dining_chair",      "leather", "DINI",  199.00, "S01", 0.60, "stable"),
    Article("D2020", "sideboard",         "oak",     "DINI",  649.00, "S04", 0.45, "stable"),
    Article("D2030", "table_extension",   "oak",     "DINI",  119.00, "S04", 0.40, "stable"),
    Article("D2031", "table_extension",   "walnut",  "DINI",  149.00, "S04", 0.30, "stable"),

    # Bedroom
    Article("B3001", "bed",         "harmony", "BEDR", 1099.00, "S01", 0.80, "stable"),
    Article("B3002", "bed",         "milano",  "BEDR", 1599.00, "S01", 0.50, "stable"),
    Article("B3003", "bed",         "kompakt", "BEDR",  749.00, "S02", 0.65, "stable"),
    Article("B3010", "mattress",    "comfort", "BEDR",  599.00, "S06", 0.85, "stable"),
    Article("B3011", "mattress",    "premium", "BEDR",  899.00, "S06", 0.55, "stable"),
    Article("B3020", "headboard",   "harmony", "BEDR",  279.00, "S01", 0.45, "stable"),
    Article("B3030", "nightstand",  "harmony", "BEDR",  179.00, "S01", 0.65, "stable"),
    Article("B3031", "nightstand",  "kompakt", "BEDR",  119.00, "S02", 0.55, "stable"),
    Article("B3040", "wardrobe",    "harmony", "BEDR", 1099.00, "S01", 0.50, "stable"),

    # Office
    Article("O4001", "desk",            "oak",     "OFFI",  399.00, "S04", 0.55, "stable"),
    Article("O4002", "desk",            "compact", "OFFI",  249.00, "S02", 0.50, "stable"),
    Article("O4010", "office_chair",    "ergo",    "OFFI",  349.00, "S07", 0.70, "stable"),
    Article("O4011", "office_chair",    "basic",   "OFFI",  179.00, "S07", 0.55, "stable"),
    Article("O4020", "bookshelf",       "oak",     "OFFI",  249.00, "S04", 0.45, "stable"),
    Article("O4030", "filing_cabinet",  "metal",   "OFFI",  269.00, "S07", 0.30, "declining"),

    # Lighting
    Article("G5001", "floor_lamp",   "luna",   "LIGH", 119.00, "S03", 0.50, "stable"),
    Article("G5010", "table_lamp",   "luna",   "LIGH",  79.00, "S03", 0.60, "stable"),
    Article("G5011", "table_lamp",   "modern", "LIGH",  49.00, "S05", 0.65, "stable"),
    Article("G5020", "ceiling_light","modern", "LIGH", 169.00, "S05", 0.40, "stable"),
    Article("G5030", "led_strip",    "smart",  "LIGH",  39.00, "S08", 0.30, "growing"),
    Article("G5031", "led_strip",    "basic",  "LIGH",  19.00, "S08", 0.35, "growing"),

    # Electronics
    Article("E6001", "tv",          "smart55", "ELEC",  799.00, "S08", 0.55, "stable"),
    Article("E6002", "tv",          "smart65", "ELEC", 1199.00, "S08", 0.40, "stable"),
    Article("E6010", "soundbar",    "compact", "ELEC",  249.00, "S08", 0.45, "stable"),
    Article("E6011", "soundbar",    "premium", "ELEC",  399.00, "S08", 0.30, "stable"),
    Article("E6020", "speakers",    "stereo",  "ELEC",  179.00, "S08", 0.30, "stable"),
    Article("E6030", "dvd_player",  "basic",   "ELEC",   69.00, "S08", 0.20, "declining"),

    # Decor
    Article("C7001", "mirror",        "round",   "DECO", 119.00, "S05", 0.45, "stable"),
    Article("C7002", "mirror",        "framed",  "DECO", 169.00, "S05", 0.40, "stable"),
    Article("C7010", "vase",          "ceramic", "DECO",  39.00, "S05", 0.50, "stable"),
    Article("C7020", "picture_frame", "wood",    "DECO",  19.00, "S05", 0.55, "stable"),
    Article("C7030", "curtain",       "linen",   "DECO",  79.00, "S05", 0.55, "stable"),

    # Storage
    Article("S8001", "dresser",   "harmony",  "STOR", 379.00, "S01", 0.50, "stable"),
    Article("S8010", "cabinet",   "oak",      "STOR", 549.00, "S04", 0.45, "stable"),
    Article("S8020", "shoe_rack", "compact",  "STOR", 109.00, "S02", 0.40, "stable"),

    # Kitchen
    Article("K9001", "kitchen_table", "oak",      "KITC", 449.00, "S04", 0.55, "stable"),
    Article("K9002", "kitchen_table", "kompakt",  "KITC", 299.00, "S02", 0.50, "stable"),
    Article("K9010", "kitchen_chair", "oak",      "KITC", 119.00, "S04", 0.70, "stable"),
    Article("K9011", "kitchen_chair", "fabric",   "KITC",  99.00, "S03", 0.60, "stable"),
    Article("K9020", "bar_stool",     "oak",      "KITC", 139.00, "S04", 0.40, "stable"),
    Article("K9021", "bar_stool",     "metal",    "KITC", 109.00, "S07", 0.35, "stable"),

    # Outdoor
    Article("U1001", "garden_chair",  "rattan",  "OUTD", 119.00, "S09", 0.45, "growing"),
    Article("U1002", "garden_chair",  "metal",   "OUTD",  89.00, "S09", 0.40, "growing"),
    Article("U1010", "garden_table",  "rattan",  "OUTD", 299.00, "S09", 0.40, "growing"),
    Article("U1020", "parasol",       "basic",   "OUTD", 119.00, "S09", 0.35, "growing"),
]


# Co-purchase patterns. When the seed item has one of these names, partners
# are independently rolled into the same basket at the given probability.
COPURCHASE: dict[str, list[tuple[str, float]]] = {
    "dining_table":  [("dining_chair", 0.85), ("table_extension", 0.40), ("sideboard", 0.20)],
    "bed":           [("mattress", 0.70), ("nightstand", 0.40), ("headboard", 0.30)],
    "sofa":          [("coffee_table", 0.30), ("armchair", 0.20), ("rug", 0.20)],
    "desk":          [("office_chair", 0.65), ("bookshelf", 0.20)],
    "tv":            [("soundbar", 0.25), ("speakers", 0.15)],
    "kitchen_table": [("kitchen_chair", 0.75)],
    "garden_table":  [("garden_chair", 0.70), ("parasol", 0.30)],
}


# Articles for which customers commonly buy multiple units (e.g. chair sets).
QUANTITY_DISTRIBUTIONS: dict[str, tuple[list[int], list[float]]] = {
    "dining_chair":   ([1, 2, 4, 6], [0.15, 0.25, 0.40, 0.20]),
    "kitchen_chair":  ([1, 2, 4, 6], [0.20, 0.30, 0.35, 0.15]),
    "garden_chair":   ([1, 2, 4],    [0.25, 0.40, 0.35]),
    "nightstand":     ([1, 2],       [0.40, 0.60]),
    "table_lamp":     ([1, 2],       [0.70, 0.30]),
    "vase":           ([1, 2, 3],    [0.60, 0.30, 0.10]),
    "picture_frame":  ([1, 2, 3, 4], [0.40, 0.30, 0.20, 0.10]),
}


DISCOUNT_REASONS_LINE = ["A", "B", "M"]
DISCOUNT_REASONS_ORDER = ["A", "K"]


def _trend_weight(trend: str, date_progress: float) -> float:
    """Multiplicative weight on selection probability based on temporal trend.

    ``date_progress`` is in [0, 1] over the full date window. Growing articles
    ramp from 0× to 2× across the window; declining articles do the reverse.
    The hard zero at one end is intentional — it forces real recency variation
    in the data (declining articles literally stop appearing late in the
    window, so their max-date lies mid-window).
    """
    if trend == "growing":
        return 2.0 * date_progress
    if trend == "declining":
        return 2.0 * (1.0 - date_progress)
    return 1.0


def _pick_quantity(rng: np.random.Generator, article_name: str) -> int:
    if article_name not in QUANTITY_DISTRIBUTIONS:
        return 1
    values, probs = QUANTITY_DISTRIBUTIONS[article_name]
    return int(rng.choice(values, p=probs))


def _generate_discount(
    rng: np.random.Generator, gross: float
) -> tuple[int, float, float, str]:
    r = rng.random()
    if r < 0.85:
        return 0, 0.0, 0.0, ""
    if r < 0.95:
        pct = float(rng.uniform(0.05, 0.15))
        return 1, gross * pct, pct, str(rng.choice(DISCOUNT_REASONS_LINE))
    pct = float(rng.uniform(0.05, 0.20))
    return 2, gross * pct, pct, str(rng.choice(DISCOUNT_REASONS_ORDER))


def _pick_partner_sku(
    rng: np.random.Generator,
    name: str,
    by_name: dict[str, list[Article]],
) -> Article | None:
    candidates = by_name.get(name)
    if not candidates:
        return None
    weights = np.array([a.popularity for a in candidates])
    weights = weights / weights.sum()
    return candidates[int(rng.choice(len(candidates), p=weights))]


def _add_with_copurchase(
    item: Article,
    basket: list[Article],
    seen_names: set[str],
    rng: np.random.Generator,
    by_name: dict[str, list[Article]],
) -> None:
    """Add ``item`` to ``basket`` and roll its co-purchase partners.

    Co-purchase rules fire whenever an item enters the basket — whether as
    seed or random extra. This matches real shopping behavior (you need
    chairs whether the table was a planned or impulse purchase).
    """
    if item.article_name in seen_names:
        return
    basket.append(item)
    seen_names.add(item.article_name)
    for partner_name, prob in COPURCHASE.get(item.article_name, []):
        if partner_name in seen_names or rng.random() >= prob:
            continue
        partner = _pick_partner_sku(rng, partner_name, by_name)
        if partner is not None:
            basket.append(partner)
            seen_names.add(partner_name)


def _generate_customer_tx_dates(
    rng: np.random.Generator, window_days: int
) -> list[date]:
    """Return the list of transaction dates for a single customer.

    Draws a first-purchase date uniformly in the window, then an exponential
    "lifetime" after which the customer goes dormant. While alive, repeat
    transactions occur at a Gamma-distributed rate.
    """
    first_offset = int(rng.integers(0, window_days))
    first_date = DATE_START + timedelta(days=first_offset)

    lifetime_days = float(rng.exponential(LIFETIME_DAYS_MEAN))
    last_active = first_date + timedelta(days=int(lifetime_days))
    last_active = min(last_active, DATE_END)
    observed_days = (last_active - first_date).days

    if observed_days <= 0:
        return [first_date]

    rate_per_year = float(rng.gamma(TX_RATE_GAMMA_SHAPE, TX_RATE_GAMMA_SCALE))
    n_repeat = int(rng.poisson(rate_per_year * observed_days / 365.25))
    if n_repeat == 0:
        return [first_date]

    offsets = sorted(int(o) for o in rng.integers(1, observed_days + 1, size=n_repeat))
    return [first_date] + [first_date + timedelta(days=o) for o in offsets]


def generate_dataset() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    window_days = (DATE_END - DATE_START).days

    by_name: dict[str, list[Article]] = {}
    for article in CATALOG:
        by_name.setdefault(article.article_name, []).append(article)

    rows: list[dict] = []
    tx_counter = 0
    for c_idx in range(N_CUSTOMERS):
        customer_id = f"C{c_idx + 1:05d}"
        tx_dates = _generate_customer_tx_dates(rng, window_days)

        for tx_date in tx_dates:
            tx_counter += 1
            tx_id = f"T{tx_counter:05d}"
            days_offset = (tx_date - DATE_START).days
            date_progress = days_offset / window_days

            # Date-conditional selection weights drive temporal trends.
            weights = np.array(
                [a.popularity * _trend_weight(a.trend, date_progress) for a in CATALOG]
            )
            weights = weights / weights.sum()

            seed = CATALOG[int(rng.choice(len(CATALOG), p=weights))]
            basket: list[Article] = []
            seen_names: set[str] = set()
            _add_with_copurchase(seed, basket, seen_names, rng, by_name)

            n_extras = int(rng.choice([0, 1, 2], p=[0.65, 0.25, 0.10]))
            for _ in range(n_extras):
                extra = CATALOG[int(rng.choice(len(CATALOG), p=weights))]
                _add_with_copurchase(extra, basket, seen_names, rng, by_name)

            basket = basket[:6]

            for line_no, item in enumerate(basket, start=1):
                quantity = _pick_quantity(rng, item.article_name)
                gross = item.base_price * float(rng.uniform(0.95, 1.05))
                net = gross / (1 + VAT)
                cost = gross * COST_RATIO
                discount_type, discount_amount, discount_pct, discount_reason = (
                    _generate_discount(rng, gross)
                )
                rows.append(
                    {
                        "customer_id": customer_id,
                        "transaction_id": tx_id,
                        "line_item": line_no,
                        "article_id": item.article_id,
                        "article_name": item.article_name,
                        "model": item.model,
                        "quantity": quantity,
                        "gross_price": round(gross, 2),
                        "net_price": round(net, 2),
                        "net_cost": round(cost, 2),
                        "date": tx_date.isoformat(),
                        "product_group": item.product_group,
                        "supplier_id": item.supplier_id,
                        "discount_type": discount_type,
                        "discount_amount": round(discount_amount, 2),
                        "discount_percentage": round(discount_pct, 4),
                        "discount_reason": discount_reason,
                    }
                )

    return pd.DataFrame(rows)


def main() -> None:
    df = generate_dataset()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, sep=";")

    n_customers = df["customer_id"].nunique()
    n_tx = df["transaction_id"].nunique()
    n_rows = len(df)
    n_articles = df["article_id"].nunique()
    n_names = df["article_name"].nunique()
    avg_basket = n_rows / n_tx
    avg_tx_per_customer = n_tx / n_customers
    tx_per_customer = df.groupby("customer_id")["transaction_id"].nunique()
    print(f"Wrote {OUTPUT_PATH}")
    print(
        f"  {n_rows} line items across {n_tx} transactions "
        f"from {n_customers} customers"
    )
    print(
        f"  avg basket size {avg_basket:.2f}, "
        f"avg transactions/customer {avg_tx_per_customer:.2f}"
    )
    print(
        f"  one-time customers: {(tx_per_customer == 1).mean():.1%},  "
        f"repeat (>=2): {(tx_per_customer >= 2).mean():.1%},  "
        f"top buyers (>=5): {(tx_per_customer >= 5).mean():.1%}"
    )
    print(f"  {n_articles} unique article_ids, {n_names} unique article_names")
    print(f"  date range {df['date'].min()} to {df['date'].max()}")


if __name__ == "__main__":
    main()
