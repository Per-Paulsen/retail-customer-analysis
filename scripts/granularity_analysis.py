"""Empirical evaluation of item-level granularity for the real Innatura data.

The chapters that group on ``article_name`` (01 Apriori, 02 BCG, 03 RFM,
05 Insights, dashboard) need a granularity that produces statistically
meaningful outputs:

- enough density per item for Apriori at reasonable support thresholds
- enough cluster separation for K-means
- non-trivial lift in the discovered rules

This script tests several candidate granularities and reports per-option
metrics so the granularity choice is empirical, not guessed:

- ``raw``           — Artikelbezeichnung exactly as stored
- ``light_norm``    — lowercase, accent-strip, collapse whitespace/punct
- ``model``         — Modellbezeichnung alone
- ``family_model``  — light-normed name + model concatenated
- ``sku``           — article_id (3,500+ unique)
- ``family_synth``  — the C1 mapping that collapses onto the synth vocabulary
- ``product_group`` — the 10-code synth-aligned category from C1's PG-map

Reads the raw Innatura ``Datenbasis.csv`` directly so the diagnosis is
independent of whatever the preprocess pipeline is currently configured
to do.

Output: a table on stdout summarising density and Apriori-yield per
option. Save to ``docs/GRANULARITY_ANALYSIS.md`` for permanent record
when invoked with ``--save``.

Run from repo root:

    python scripts/granularity_analysis.py            # stdout only
    python scripts/granularity_analysis.py --save     # also writes md
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata

# Windows console defaults to cp1252 which can't encode the unicode glyphs
# we use in the report (≥ etc). Force UTF-8 output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules


DEFAULT_SOURCE = Path(
    "C:/Users/perpa/OneDrive/Desktop/PC/Arbeit/Praktikum/Innatura/Daten/Datenbasis.csv"
)
SUPPORT_LEVELS = [0.0001, 0.0005, 0.001, 0.005]
CONFIDENCE = 0.5
LIFT_NONTRIVIAL = 2.0


# ----------------------------------------------------------------------------
# Loading + cleaning the raw source
# ----------------------------------------------------------------------------

def _safe_float(s: object) -> float:
    if pd.isna(s):
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def load_raw(source: Path) -> pd.DataFrame:
    """Read Datenbasis.csv and rename the columns we need."""
    raw = pd.read_csv(source, sep=";", encoding="cp1252", dtype=str, on_bad_lines="warn")
    cols = list(raw.columns)
    df = pd.DataFrame()
    df["transaction_id"] = "T" + raw[cols[0]].astype(str).str.replace(".", "_", regex=False)
    df["article_id"]     = raw[cols[4]].astype(str).str.strip().str.rstrip(".")
    df["article_name"]   = raw[cols[5]].astype(str).str.strip()
    df["model"]          = raw[cols[6]].fillna("").astype(str).str.strip()
    df["gross_price"]    = raw[cols[7]].apply(_safe_float)
    df["date"]           = pd.to_datetime(raw[cols[18]], format="%d.%m.%Y", errors="coerce")
    df["wg"]             = raw[cols[19]].fillna("").astype(str).str.strip()

    # Drop rows that the production preprocess would also drop (missing date,
    # empty / "nan" article_name, accounting-only Warengruppen 50/70).
    df = df[df["date"].notna()]
    df = df[df["article_name"].astype(str).str.strip() != ""]
    df = df[df["article_name"].astype(str).str.lower() != "nan"]
    wg_prefix = df["wg"].str[:2]
    df = df[~wg_prefix.isin(["50", "70"])]
    return df.reset_index(drop=True)


# ----------------------------------------------------------------------------
# Granularity variants
# ----------------------------------------------------------------------------

_PUNCT_RE = re.compile(r"[^a-z0-9]+")


def light_normalize(s: str) -> str:
    """Lowercase, strip accents (NFKD → ASCII), collapse non-alphanum to space."""
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode("ascii")
    s = _PUNCT_RE.sub(" ", s).strip()
    s = " ".join(s.split())
    return s


# Reuse the C1 mapping for the family_synth option. The list is duplicated
# (rather than imported) to keep the diagnosis self-contained.
_FAMILY_PATTERNS = [
    (r"\bschlafsofa\b", "sofa_bed"), (r"\bdoppelbett\b", "bed"),
    (r"\bsystembett\b", "bed"),  (r"\bbalkenbett\b", "bed"),
    (r"\bschubkastenbett\b", "bed"), (r"\bkinderbett\b", "bed"),
    (r"\beinzelbett\b", "bed"),  (r"\bhochbett\b", "bed"),
    (r"\bmittelhochbett\b", "bed"), (r"\bboxspringbett\b", "bed"),
    (r"\bcomfortbett\b", "bed"),  (r"\bbettrahmen\b", "bed"),
    (r"\bbettgestell\b", "bed"),  (r"\bbett\b", "bed"),
    (r"\bschaummatratze\b", "mattress"), (r"\bmatratze\b", "mattress"),
    (r"\blattenrost\b", "slatted_frame"), (r"\bkopfteil\b", "headboard"),
    (r"\bkopfstuetze\b", "headrest"), (r"\barmlehnkissen\b", "pillow"),
    (r"\barmlehnenkissen\b", "pillow"), (r"\bnierenkissen\b", "pillow"),
    (r"\bklemmkissen\b", "pillow"), (r"\bnachttisch\b", "nightstand"),
    (r"\bnachtkommode\b", "nightstand"), (r"\bnachtkonsole\b", "nightstand"),
    (r"\bnako\b", "nightstand"), (r"\bkissen\b", "pillow"),
    (r"\bbettwaesche\b", "bedding"),
    (r"\bkleiderschrank\b", "wardrobe"), (r"\bschuhschrank\b", "shoe_cabinet"),
    (r"\baktenschrank\b", "filing_cabinet"),
    (r"\bschiebetuerenschrank\b", "wardrobe"),
    (r"\bschwebetuerenschrank\b", "wardrobe"),
    (r"\bmediaschrank\b", "cabinet"),
    (r"\bvitrinenschrank\b", "display_cabinet"),
    (r"\bmultivitrine\b", "display_cabinet"),
    (r"\bglasvitrine\b", "display_cabinet"),
    (r"\bvitrine\b", "display_cabinet"), (r"\bvertiko\b", "cabinet"),
    (r"\bbuffetschrank\b", "display_cabinet"),
    (r"\bbuffet\b", "display_cabinet"),
    (r"\bfernsehkommode\b", "lowboard"), (r"\btv.?board\b", "lowboard"),
    (r"\btv.?longboard\b", "lowboard"), (r"\btv.?kommode\b", "lowboard"),
    (r"\btv.?schrank\b", "lowboard"),
    (r"\bhighboard\b", "highboard"), (r"\blowboard\b", "lowboard"),
    (r"\bsideboard\b", "sideboard"), (r"\banrichte\b", "sideboard"),
    (r"\bbuecherregal\b", "bookshelf"), (r"\bwandboard\b", "wall_shelf"),
    (r"\bwandregal\b", "wall_shelf"), (r"\bhaengekiste\b", "wall_shelf"),
    (r"\bhutablage\b", "wall_shelf"), (r"\bweinregal\b", "shelf"),
    (r"\banbauwand\b", "wall_unit"), (r"\bwohnwand\b", "wall_unit"),
    (r"\bwuerfelsystem\b", "shelf"), (r"\bwuerfel\b", "shelf"),
    (r"\bregal\b", "shelf"), (r"\bkommode\b", "dresser"),
    (r"\bschrank\b", "cabinet"),
    (r"\besstisch\b", "dining_table"), (r"\bcouchtisch\b", "coffee_table"),
    (r"\bsalontisch\b", "coffee_table"), (r"\bkuechentisch\b", "kitchen_table"),
    (r"\bbeistelltisch\b", "side_table"), (r"\bschreibtisch\b", "desk"),
    (r"\bsekretaer\b", "desk"), (r"\bgartentisch\b", "garden_table"),
    (r"\bbaumtisch\b", "dining_table"), (r"\bkonsolentisch\b", "side_table"),
    (r"\becktisch\b", "table"), (r"\btisch\b", "table"),
    (r"\bbarhocker\b", "bar_stool"), (r"\bkuechenstuhl\b", "kitchen_chair"),
    (r"\bbuerostuhl\b", "office_chair"), (r"\bgartenstuhl\b", "garden_chair"),
    (r"\bfreischwinger\b", "dining_chair"), (r"\bschwingstuhl\b", "dining_chair"),
    (r"\bschwinger\b", "dining_chair"), (r"\bstuhl\b", "dining_chair"),
    (r"\beckbank\b", "bench"), (r"\bschuhbank\b", "bench"),
    (r"\bbank\b", "bench"), (r"\bhocker\b", "stool"),
    (r"\becksofa\b", "corner_sofa"), (r"\bpolsterecke\b", "corner_sofa"),
    (r"\beckgarnitur\b", "corner_sofa"),
    (r"\bohrenbackensessel\b", "armchair"), (r"\bohrensessel\b", "armchair"),
    (r"\bsolitaersessel\b", "armchair"), (r"\bruhesessel\b", "armchair"),
    (r"\bsofa\b", "sofa"), (r"\bsessel\b", "armchair"),
    (r"\bsitzer\b", "sofa"), (r"\bgarnitur\b", "sofa"),
    (r"\bpolster\b", "sofa"),
    (r"\bsonnenschirm\b", "parasol"), (r"\bgartenliege\b", "garden_lounger"),
    (r"\beinzelliege\b", "lounger"), (r"\bliege\b", "lounger"),
    (r"\bgarten\b", "outdoor_misc"),
    (r"\bteppich\b", "rug"), (r"\bspiegel\b", "mirror"),
    (r"\bgardine\b", "curtain"), (r"\bvorhang\b", "curtain"),
    (r"\bbild\b", "picture"), (r"\bfotodruck\b", "picture"),
    (r"\bkunstwerk\b", "artwork"),
    (r"\bstehlampe\b", "floor_lamp"), (r"\bstehleuchte\b", "floor_lamp"),
    (r"\bhaengelampe\b", "pendant_lamp"), (r"\bhaengeleuchte\b", "pendant_lamp"),
    (r"\bdeckenlampe\b", "ceiling_lamp"), (r"\bdeckenleuchte\b", "ceiling_lamp"),
    (r"\btischlampe\b", "table_lamp"), (r"\btischleuchte\b", "table_lamp"),
    (r"\bbeleuchtungsset\b", "lighting"), (r"\bbeleuchtung\b", "lighting"),
    (r"\bleuchte\b", "lamp"), (r"\blampe\b", "lamp"), (r"\bled\b", "lighting"),
    (r"\bansteckplatte\b", "table_extension"), (r"\baufpreis\b", "accessory"),
    (r"\bnachbestellung\b", "accessory"), (r"\bersatzteil\b", "accessory"),
    (r"\bersatz\b", "accessory"), (r"\bzubehoer\b", "accessory"),
    (r"\bauszug\b", "accessory"), (r"\bablage\b", "accessory"),
    (r"\bschubkasten\b", "accessory"), (r"\bschublade\b", "accessory"),
    (r"\beinlegeboden\b", "accessory"), (r"\bhakenleiste\b", "accessory"),
    (r"\brollcontainer\b", "accessory"), (r"\bfussteil\b", "accessory"),
    (r"\bschubladenmodul\b", "accessory"), (r"\bpanel\b", "accessory"),
    (r"\braumteiler\b", "accessory"), (r"\bfundgrube\b", "misc"),
]


def family_synth(name: str) -> str:
    n = light_normalize(name)
    for pattern, family in _FAMILY_PATTERNS:
        if re.search(pattern, n):
            return family
    return ""


_PRODUCT_GROUP_MAP = {
    "00": "LIVI", "01": "LIVI", "02": "LIVI",
    "03": "BEDR", "04": "BEDR", "05": "BEDR", "06": "BEDR",
    "07": "DINI", "08": "KITC", "09": "STOR", "10": "LIGH",
    "11": "DECO", "12": "DECO", "13": "DECO", "14": "DECO",
    "15": "DECO", "16": "DECO",
    "17": "OUTD", "18": "OUTD", "19": "OUTD",
    "20": "LIVI", "22": "DECO", "25": "DECO",
    "40": "BEDR", "41": "BEDR", "42": "LIGH",
}


def derive_options(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Build the candidate item series, one per granularity option."""
    name = df["article_name"].astype(str)
    model = df["model"].astype(str)
    name_norm = name.apply(light_normalize)
    model_norm = model.apply(light_normalize)
    return {
        "raw":            name,
        "light_norm":     name_norm,
        "model":          model,
        "family_model":   (name_norm + " " + model_norm).str.strip().replace(r"\s+", " ", regex=True),
        "sku":            df["article_id"].astype(str),
        "family_synth":   name.apply(family_synth),
        "product_group":  df["wg"].str[:2].map(_PRODUCT_GROUP_MAP).fillna(""),
    }


# ----------------------------------------------------------------------------
# Metrics per granularity option
# ----------------------------------------------------------------------------

def _baskets(df: pd.DataFrame, item_col: pd.Series) -> list[list[str]]:
    """Build basket → list-of-items, dropping empty items."""
    work = pd.DataFrame({"transaction_id": df["transaction_id"], "item": item_col})
    work = work[work["item"].astype(str).str.strip() != ""]
    grouped = work.groupby("transaction_id")["item"].apply(lambda s: sorted(set(s)))
    return [b for b in grouped.tolist() if len(b) >= 1]


def density_metrics(items: pd.Series, baskets: list[list[str]]) -> dict:
    """Item-level frequency distribution."""
    item_count: Counter[str] = Counter()
    for b in baskets:
        for it in b:
            item_count[it] += 1
    counts = np.array(list(item_count.values()))
    return {
        "n_unique":      len(item_count),
        "n_baskets":     len(baskets),
        "median_count":  int(np.median(counts)) if len(counts) else 0,
        "p75_count":     int(np.percentile(counts, 75)) if len(counts) else 0,
        "max_count":     int(counts.max()) if len(counts) else 0,
        "items_ge_5":    int((counts >= 5).sum()),
        "items_ge_10":   int((counts >= 10).sum()),
        "items_ge_20":   int((counts >= 20).sum()),
    }


def apriori_metrics(baskets: list[list[str]]) -> dict[float, dict]:
    """Run Apriori at each support level; report rule counts + lift stats."""
    if not baskets:
        return {sup: {"rules": 0, "nontrivial": 0, "median_lift": 0, "p75_lift": 0}
                for sup in SUPPORT_LEVELS}
    te = TransactionEncoder()
    matrix = pd.DataFrame(te.fit_transform(baskets), columns=te.columns_)
    out: dict[float, dict] = {}
    for sup in SUPPORT_LEVELS:
        try:
            freq = apriori(matrix, min_support=sup, use_colnames=True, max_len=2)
            if freq.empty:
                out[sup] = {"rules": 0, "nontrivial": 0, "median_lift": 0.0, "p75_lift": 0.0}
                continue
            rules = association_rules(
                freq, num_itemsets=len(matrix),
                metric="confidence", min_threshold=CONFIDENCE,
            )
            n_rules = len(rules)
            if n_rules == 0:
                out[sup] = {"rules": 0, "nontrivial": 0, "median_lift": 0.0, "p75_lift": 0.0}
                continue
            n_nt = int((rules["lift"] >= LIFT_NONTRIVIAL).sum())
            out[sup] = {
                "rules":       n_rules,
                "nontrivial":  n_nt,
                "median_lift": float(rules["lift"].median()),
                "p75_lift":    float(rules["lift"].quantile(0.75)),
            }
        except Exception as e:  # noqa: BLE001
            out[sup] = {"rules": -1, "nontrivial": -1,
                        "median_lift": 0.0, "p75_lift": 0.0,
                        "error": str(e)[:50]}
    return out


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------

def render_table(rows: list[dict]) -> str:
    """Format the report as a markdown table."""
    lines = []
    lines.append("## Density per granularity option\n")
    header = ["option", "unique items", "med basket-count", "p75", "max",
              "≥5", "≥10", "≥20"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for r in rows:
        d = r["density"]
        lines.append(
            f"| `{r['option']}` | {d['n_unique']} | {d['median_count']} | "
            f"{d['p75_count']} | {d['max_count']} | {d['items_ge_5']} | "
            f"{d['items_ge_10']} | {d['items_ge_20']} |"
        )
    lines.append("")
    lines.append("## Apriori yield per granularity × support threshold\n")
    lines.append("Confidence ≥ 0.5, max rule length 2 (single antecedent → "
                 "single consequent). 'non-trivial' = lift ≥ 2.\n")
    for sup in SUPPORT_LEVELS:
        lines.append(f"### `min_support = {sup}`")
        lines.append("")
        lines.append("| option | rules | non-trivial | median lift | p75 lift |")
        lines.append("|---|---|---|---|---|")
        for r in rows:
            a = r["apriori"][sup]
            lines.append(
                f"| `{r['option']}` | {a['rules']} | {a['nontrivial']} | "
                f"{a['median_lift']:.2f} | {a['p75_lift']:.2f} |"
            )
        lines.append("")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--save", action="store_true",
                        help="also write the report to docs/GRANULARITY_ANALYSIS.md")
    args = parser.parse_args()

    print(f"Loading {args.source}")
    df = load_raw(args.source)
    print(f"  {len(df):,} line items, {df['transaction_id'].nunique():,} baskets, "
          f"{df['article_id'].nunique():,} unique SKUs\n")

    options = derive_options(df)
    rows = []
    for name, series in options.items():
        print(f"[{name}] computing...", flush=True)
        baskets = _baskets(df, series)
        rows.append({
            "option":   name,
            "density":  density_metrics(series, baskets),
            "apriori":  apriori_metrics(baskets),
        })

    report = render_table(rows)
    print()
    print(report)

    if args.save:
        out_path = Path("docs/GRANULARITY_ANALYSIS.md")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        header = (
            "# Granularity analysis — real Innatura data\n\n"
            "Empirical evaluation of item-level granularity for the analyses "
            "in chapters 01 (Apriori), 02 (BCG), 03 (RFM), 05 (Insights), "
            "and the dashboard. Generated by `scripts/granularity_analysis.py`.\n\n"
        )
        out_path.write_text(header + report, encoding="utf-8")
        print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
