"""Convert the original (German, confidential) Innatura `Datenbasis.csv` into
the same schema as the synthetic dataset, with PII removed.

Anonymization: customer last names are hashed to deterministic IDs (md5 first
6 hex chars → integer). Salesperson and free-form order text columns are
dropped. The customer dimension is preserved so chapters that need it
(CLV, survival, uplift) work on the real data.

The output is written to ``data/raw/transactions.csv`` in the *repo* — that
path is gitignored, so the file lives only on the local machine.

Usage:

    python scripts/preprocess_real_data.py \\
        --source "C:/Users/perpa/OneDrive/Desktop/PC/Arbeit/Praktikum/Innatura/Daten/Datenbasis.csv"

If --source is omitted the script looks at the default path above.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_SOURCE = Path(
    "C:/Users/perpa/OneDrive/Desktop/PC/Arbeit/Praktikum/Innatura/Daten/Datenbasis.csv"
)
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "raw" / "transactions.csv"
)

# 4-digit Warengruppe code (first 2 digits) → department
# Based on the Warengruppen taxonomy in the source file:
#   00 Anbauwände | 01 Polstermöbel | 02 Couchtische/Kleinmöbel
#   03 Betten | 04 Kleiderschränke | 05 Kommoden/Nachttische | 06 Matratzen
#   07 Eßtische/Stühle/Vitrinen | 08 Küche | 09 Dielenmöbel
#   10+ further (Lampen, Teppiche, Deko, ...)
DEPARTMENT_MAP: dict[str, str] = {
    "00": "Living",      # Anbauwände
    "01": "Living",      # Polstermöbel
    "02": "Living",      # Couchtische, Kleinmöbel
    "03": "Bedroom",     # Betten
    "04": "Bedroom",     # Kleiderschränke
    "05": "Bedroom",     # Kommoden, Nachttische, Spiegel
    "06": "Bedroom",     # Matratzen
    "07": "Dining",      # Eßtische, Stühle, Vitrinen
    "08": "Dining",      # Küche
    "09": "Storage",     # Dielenmöbel (entryway)
    "10": "Living",      # Lampen / Leuchten
    "11": "Living",      # Teppiche / Deko
    "12": "Living",
    "13": "Living",
    "14": "Living",
    "15": "Living",
    "16": "Living",
    "17": "Outdoor",
    "18": "Outdoor",
    "19": "Outdoor",
    # Empirically discovered codes from the actual data:
    "20": "Living",      # Fundgrube / Sale items, Stoff, Pflege
    "22": "Living",      # Bild / Fotodruck (decor)
    "25": "Living",      # Bild / Fotodruck
    "40": "Bedroom",     # Spiegel, Sitzkissen
    "41": "Bedroom",     # Bettwaesche, Kissen
    "42": "Living",      # Hängelampen, Gardinen
    "50": "Other",       # Gutschrift (credit notes — accounting, not a real purchase)
    "70": "Other",       # Transportkosten (shipping fees)
}

# Article-name patterns → bundle_group. Matched against the lowercased,
# accent-stripped Artikelbezeichnung.
BUNDLE_PATTERNS: list[tuple[str, str]] = [
    (r"\b(bett|matratze|kopfteil|nachttisch|nachtkonsole|lattenrost)\b", "bed_system"),
    (r"\b(esstisch|stuhl|vitrine|sideboard|anrichte|ansteckplatte|auszug)\b", "dining_system"),
    (r"\b(kuechentisch|kuechenstuhl|barhocker|hocker.*kueche)\b", "kitchen_system"),
    (r"\b(schreibtisch|buerostuhl|buecherregal|aktenschrank)\b", "office_system"),
    (r"\b(garten|gartentisch|gartenstuhl|sonnenschirm|liege.*garten|outdoor)\b", "garden_system"),
]

# Fallback name → department, used when Warengruppe code is missing.
# Tested against accent-stripped, lowercased article_name in order.
NAME_DEPARTMENT_PATTERNS: list[tuple[str, str]] = [
    (r"\b(bett|matratze|kopfteil|nachttisch|nachtkonsole|kleiderschrank|kommode|spiegel|hutablage|garderobe)\b",
     "Bedroom"),
    (r"\b(esstisch|stuhl|freischwinger|vitrine|sideboard|anrichte|kuechen)\b", "Dining"),
    (r"\b(sofa|sessel|couchtisch|polster|teppich|leuchte|lampe|bild|kunstwerk|fotodruck|gardine|stehleuchte|haengelampe)\b",
     "Living"),
    (r"\b(schreibtisch|sekretaer|aktenschrank|buerostuhl)\b", "Living"),
    (r"\b(garten|outdoor|sonnenschirm)\b", "Outdoor"),
    (r"\b(gutschrift|transportkosten|versand)\b", "Other"),
    (r"\b(hocker|fundgrube)\b", "Living"),
]

# Items considered accessories of their bundle's primary product.
ACCESSORY_PATTERNS = [
    r"\bkopfteil\b", r"\bnachttisch\b", r"\bnachtkonsole\b", r"\blattenrost\b",
    r"\bansteckplatte\b", r"\bauszug\b",
]


def _strip_accents(s: str) -> str:
    """German diacritic stripping: ä→ae, ö→oe, ü→ue, ß→ss."""
    if not isinstance(s, str):
        return ""
    return (s.lower()
              .replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
              .replace("Ä", "ae").replace("Ö", "oe").replace("Ü", "ue"))


def _hash_customer(name: str) -> str:
    """Deterministic 5-digit numeric ID from a last name. Same name → same ID."""
    if pd.isna(name) or not str(name).strip():
        return ""
    h = hashlib.md5(str(name).strip().encode("utf-8")).hexdigest()
    n = int(h[:8], 16) % 99999
    return f"C{n:05d}"


def _parse_warengruppe(wg: str) -> tuple[str, str, str]:
    """Returns (4-digit code, functional category text, material/wood)."""
    if pd.isna(wg) or not str(wg).strip():
        return ("", "", "")
    s = str(wg).strip()
    m = re.match(r"(\d{4})\s+(.*)", s)
    if not m:
        return (s[:4] if len(s) >= 4 else s, s, "")
    code = m.group(1)
    rest = m.group(2)
    # Last word(s) are typically the material/wood
    parts = rest.rsplit(" ", 1)
    if len(parts) == 2:
        category_text, material = parts
    else:
        category_text, material = rest, ""
    return code, category_text.strip(", "), material


def _derive_department(wg_code: str, article_name: str = "") -> str:
    """Try Warengruppe code first; fall back to name-based pattern match."""
    if wg_code:
        dept = DEPARTMENT_MAP.get(wg_code[:2], "")
        if dept:
            return dept
    name = _strip_accents(article_name)
    for pattern, dept in NAME_DEPARTMENT_PATTERNS:
        if re.search(pattern, name):
            return dept
    return ""


def _derive_bundle_group(article_name: str) -> str:
    name = _strip_accents(article_name)
    for pattern, bundle in BUNDLE_PATTERNS:
        if re.search(pattern, name):
            return bundle
    return ""


def _is_accessory(article_name: str) -> bool:
    name = _strip_accents(article_name)
    return any(re.search(p, name) for p in ACCESSORY_PATTERNS)


def _safe_float(s: object) -> float:
    """Parse a number that may contain commas as decimal separators or be NaN."""
    if pd.isna(s):
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip().replace(".", "").replace(",", ".") if "," in str(s) else str(s).strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def preprocess(source: Path, output: Path) -> pd.DataFrame:
    print(f"Reading {source}")
    raw = pd.read_csv(source, sep=";", encoding="cp1252", dtype=str, on_bad_lines="warn")
    print(f"  {len(raw)} rows, {len(raw.columns)} columns")

    # Rename columns by position (the German names are messy and there's a duplicate "Nachlassgrund")
    # Layout known from inspection:
    #   0  KV-Nr.                  → transaction_id
    #   1  Position-Nr.            → line_item
    #   2  Nachname                → (PII, hashed)
    #   3  Menge                   → quantity
    #   4  Artikel-Nr.             → article_id
    #   5  Artikelbezeichnung      → article_name (raw, will clean)
    #   6  Modellbezeichnung       → model
    #   7  Brutto-VKP              → gross_price
    #   8  NettoNetto-VKP          → net_price
    #   9  NettoNetto-EKP          → net_cost
    #   10 PosNachlass             → position_discount_eur
    #   11 PosNachlassAnteilGesamt → total_discount_eur
    #   12 % Nachlass              → total_discount_pct
    #   13 % PosNachlass           → position_discount_pct
    #   14 Nachlassgrund (1)       → total_discount_reason
    #   15 Nachlassgrund (2)       → position_discount_reason
    #   16 Verkäufer               → (PII, dropped)
    #   17 Bestelltext             → (PII, dropped)
    #   18 Datum                   → date
    #   19 Warengruppe             → (parsed below)
    #   20 Lieferanten-Nr.         → supplier_id
    cols = list(raw.columns)
    raw = raw.rename(columns={
        cols[0]:  "_kv",
        cols[1]:  "_pos",
        cols[2]:  "_nachname",
        cols[3]:  "_menge",
        cols[4]:  "_artnr",
        cols[5]:  "_artbez",
        cols[6]:  "_model",
        cols[7]:  "_brutto",
        cols[8]:  "_netto",
        cols[9]:  "_ekp",
        cols[10]: "_posnachlass",
        cols[11]: "_gesnachlass",
        cols[12]: "_pct_kv",
        cols[13]: "_pct_pos",
        cols[14]: "_grund_ges",
        cols[15]: "_grund_pos",
        cols[16]: "_verk",      # PII
        cols[17]: "_bestelltext",  # PII
        cols[18]: "_datum",
        cols[19]: "_wg",
        cols[20]: "_lieferant",
    })

    out = pd.DataFrame()

    # Customer (anonymized) + transaction key
    out["customer_id"]    = raw["_nachname"].apply(_hash_customer)
    out["transaction_id"] = "T" + raw["_kv"].astype(str).str.replace(".", "_", regex=False)
    out["line_item"]      = pd.to_numeric(raw["_pos"], errors="coerce").fillna(0).astype(int)

    # Article info — keep real names + models
    out["article_id"]   = raw["_artnr"].astype(str).str.strip().str.rstrip(".")
    out["article_name"] = raw["_artbez"].astype(str).str.strip()
    out["model"]        = raw["_model"].fillna("").astype(str).str.strip()

    # Numeric fields
    out["quantity"]    = pd.to_numeric(raw["_menge"],   errors="coerce").fillna(1).astype(int)
    out["gross_price"] = raw["_brutto"].apply(_safe_float)
    out["net_price"]   = raw["_netto"].apply(_safe_float)
    out["net_cost"]    = raw["_ekp"].apply(_safe_float)

    # Date
    out["date"] = pd.to_datetime(raw["_datum"], format="%d.%m.%Y", errors="coerce")

    # Hierarchy from Warengruppe
    parsed = raw["_wg"].apply(_parse_warengruppe)
    out["product_group"]      = parsed.apply(lambda t: t[0])  # 4-digit code
    out["product_group_text"] = parsed.apply(lambda t: t[1])
    out["material"]           = parsed.apply(lambda t: t[2])
    out["department"]         = out.apply(
        lambda r: _derive_department(r["product_group"], r["article_name"]), axis=1
    )

    # Bundle membership (derived from article_name)
    out["bundle_group"] = out["article_name"].apply(_derive_bundle_group)

    out["supplier_id"] = raw["_lieferant"].fillna("").astype(str).str.strip()

    # Discounts: prefer position-level, fall back to total-level
    pos_eur = raw["_posnachlass"].apply(_safe_float)
    ges_eur = raw["_gesnachlass"].apply(_safe_float)
    out["discount_amount"]     = np.where(pos_eur > 0, pos_eur, ges_eur)
    pos_pct = raw["_pct_pos"].apply(_safe_float)
    ges_pct = raw["_pct_kv"].apply(_safe_float)
    out["discount_percentage"] = np.where(pos_pct > 0, pos_pct / 100.0, ges_pct / 100.0)
    out["discount_type"] = np.where(
        (pos_eur > 0) | (pos_pct > 0), 1,
        np.where((ges_eur > 0) | (ges_pct > 0), 2, 0)
    ).astype(int)
    out["discount_reason"] = np.where(
        out["discount_type"] == 1,
        raw["_grund_pos"].fillna("").astype(str).str[:1],
        np.where(out["discount_type"] == 2, raw["_grund_ges"].fillna("").astype(str).str[:1], "")
    )

    # Drop rows with no usable date or article (strict: NaN, empty, "nan" string)
    before = len(out)
    out = out[
        out["date"].notna()
        & out["article_name"].notna()
        & (out["article_name"].astype(str).str.strip() != "")
        & (out["article_name"].astype(str).str.lower() != "nan")
    ].copy()
    if len(out) < before:
        print(f"  dropped {before - len(out)} rows with missing date/article")

    out = out.sort_values(["transaction_id", "line_item"]).reset_index(drop=True)

    # Round monetary fields
    for col in ("gross_price", "net_price", "net_cost", "discount_amount", "discount_percentage"):
        out[col] = out[col].round(4 if "percentage" in col else 2)

    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output, sep=";", index=False)
    print(f"Wrote {output}: {len(out)} rows")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    df = preprocess(args.source, args.output)

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Customers:    {df['customer_id'].nunique():>5,d}")
    print(f"Transactions: {df['transaction_id'].nunique():>5,d}")
    print(f"Line items:   {len(df):>5,d}")
    print(f"Articles:     {df['article_id'].nunique():>5,d} unique SKUs")
    print(f"Article names:{df['article_name'].nunique():>5,d} unique product names")
    print(f"Models:       {df['model'].nunique():>5,d} unique models")
    print(f"Date range:   {df['date'].min().date()} to {df['date'].max().date()}")
    print()
    print("Department distribution:")
    print(df.groupby("department").agg(
        line_items=("line_item", "count"),
        revenue=("gross_price", "sum"),
        skus=("article_id", "nunique"),
    ).round(0).to_string())


if __name__ == "__main__":
    main()
