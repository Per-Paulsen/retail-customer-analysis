"""Generate the 1200x630 Open-Graph image for the site.

Quarto Cosmo-inspired palette: white background, cosmo-blue accent,
light-weight title — matches the data-analytics feel of the live site.

Run once after editing — output is committed at repo root as og-image-v2.png
and referenced from _quarto.yml.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1200, 630
BG = (255, 255, 255)  # white
FG = (33, 37, 41)  # Bootstrap default body dark  #212529
ACCENT = (39, 128, 227)  # Cosmo blue  #2780e3
MUTED = (108, 117, 125)  # Bootstrap muted  #6c757d
DIM = (173, 181, 189)  # Bootstrap secondary-muted  #adb5bd


def font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    """weight: 'light' | 'regular' | 'semibold' | 'bold'"""
    by_weight = {
        "light": ["C:/Windows/Fonts/segoeuil.ttf", "C:/Windows/Fonts/segoeui.ttf"],
        "regular": ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"],
        "semibold": ["C:/Windows/Fonts/seguisb.ttf", "C:/Windows/Fonts/segoeui.ttf"],
        "bold": ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"],
    }
    for path in by_weight[weight]:
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
    title = "Retail Analysis"
    subline = "End-to-end analytics"
    by = "by Per Paulsen"
    site = "per-paulsen.github.io"

    f_eyebrow = font(26, "semibold")
    f_title = font(160, "light")
    f_sub = font(56, "regular")
    f_footer = font(22, "regular")
    f_mono = mono_font(22)

    # Stack the three core blocks (eyebrow / title / subline) so that
    # they sit visually centered in the upper-middle of the canvas,
    # leaving generous white space around them — matches the airier
    # composition of the Expliq / APIQ tiles.
    y = 150
    spaced = "   ".join(list(eyebrow))
    draw.text((pad, y), spaced, font=f_eyebrow, fill=ACCENT)
    y += 70

    draw.text((pad, y), title, font=f_title, fill=FG)
    y += 200

    draw.text((pad, y), subline, font=f_sub, fill=ACCENT)

    # footer
    fy = H - pad - 22
    draw.text((pad, fy), by, font=f_footer, fill=DIM)
    site_w = draw.textlength(site, font=f_mono)
    draw.text((W - pad - site_w, fy), site, font=f_mono, fill=DIM)

    out = Path(__file__).resolve().parent.parent / "og-image-v5.png"
    img.save(out, "PNG", optimize=True)
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
