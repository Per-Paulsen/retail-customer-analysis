"""Generate the 1200x630 Open-Graph image for the site.

Run once after editing — output is committed at repo root as og-image.png
and referenced from _quarto.yml.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1200, 630
BG = (10, 10, 10)
FG = (250, 250, 250)
ACCENT = (251, 191, 36)  # amber-400 (different from Expliq indigo / APIQ violet)
MUTED = (161, 161, 170)  # zinc-400
DIM = (113, 113, 122)  # zinc-500


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/seguivar.ttf" if not bold else "C:/Windows/Fonts/seguibl.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def mono_font(size: int) -> ImageFont.FreeTypeFont:
    for path in [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
    ]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    pad = 80

    eyebrow = "PORTFOLIO PROJECT"
    title_line_1 = "Retail Customer"
    title_line_2 = "& Basket Analysis"
    subline = "End-to-end analytics across 9 chapters"
    desc = "Market basket, RFM, CLV, survival, forecasting, embeddings, causal."
    by = "by Per Paulsen"
    site = "per-paulsen.github.io/retail-customer-analysis"

    f_eyebrow = load_font(26, bold=False)
    f_title = load_font(108, bold=True)
    f_sub = load_font(48, bold=True)
    f_desc = load_font(30, bold=False)
    f_footer = load_font(24, bold=False)
    f_mono = mono_font(24)

    y = pad
    # eyebrow with letter spacing (manual: insert thin space)
    spaced = "   ".join(list(eyebrow))
    draw.text((pad, y), spaced, font=f_eyebrow, fill=DIM)
    y += 60

    draw.text((pad, y), title_line_1, font=f_title, fill=FG)
    y += 120
    draw.text((pad, y), title_line_2, font=f_title, fill=FG)
    y += 130

    draw.text((pad, y), subline, font=f_sub, fill=ACCENT)
    y += 70

    draw.text((pad, y), desc, font=f_desc, fill=MUTED)

    # footer
    fy = H - pad - 24
    draw.text((pad, fy), by, font=f_footer, fill=DIM)
    site_w = draw.textlength(site, font=f_mono)
    draw.text((W - pad - site_w, fy), site, font=f_mono, fill=DIM)

    out = Path(__file__).resolve().parent.parent / "og-image.png"
    img.save(out, "PNG", optimize=True)
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
