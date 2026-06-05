#!/usr/bin/env python3
"""
CAMEL-HOT — Generate all required icon and branding assets.

Run ONCE before building on any platform.  Reads assets/camel_mascot.png
and produces the icon/branding files that build scripts and PyInstaller need.

Output files:
  assets/camel_hot.ico           – Windows multi-size icon (ICO)
  assets/camel_hot_512.png       – Linux icon  (512×512 PNG)
  assets/camel_hot.icns          – macOS icon  (ICNS via iconutil — macOS only)
  assets/installer_sidebar.png   – Inno Setup welcome/finish panel (410×797)
  assets/installer_header.png    – Inno Setup inner-page header   (55×58)

Usage:
    pip install Pillow          # one-time
    python tools/generate_icons.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed.  Run: pip install Pillow")
    sys.exit(1)

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SOURCE = ASSETS / "camel_mascot.png"

# Windows ICO sizes (pixels per side)
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]

# Dark background colour matching the app theme (#1a1a2e)
DARK_BG = (26, 26, 46, 255)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _square_crop(img: Image.Image) -> Image.Image:
    """Return a center-cropped square version of *img*."""
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def _on_dark_canvas(img: Image.Image, canvas_w: int, canvas_h: int,
                    pad_frac: float = 0.10) -> Image.Image:
    """Place *img* centred on a dark canvas of *canvas_w* × *canvas_h*."""
    canvas = Image.new("RGBA", (canvas_w, canvas_h), DARK_BG)
    max_w = int(canvas_w * (1 - 2 * pad_frac))
    max_h = int(canvas_h * (1 - 2 * pad_frac))
    copy = img.copy().convert("RGBA")
    copy.thumbnail((max_w, max_h), Image.LANCZOS)
    x = (canvas_w - copy.width) // 2
    y = (canvas_h - copy.height) // 2
    mask = copy.split()[3]
    canvas.paste(copy, (x, y), mask=mask)
    return canvas


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def generate_ico(src: Image.Image) -> None:
    out = ASSETS / "camel_hot.ico"
    sq = _square_crop(src.convert("RGBA"))
    # Pillow ICO writer: pass sizes= on the single source image; it resizes internally.
    sq.save(out, format="ICO", sizes=[(s, s) for s in ICO_SIZES])
    print(f"  ✔  {out.name}  ({'/'.join(str(s) for s in ICO_SIZES)} px)")


def generate_linux_png(src: Image.Image) -> None:
    out = ASSETS / "camel_hot_512.png"
    _square_crop(src.convert("RGBA")).resize((512, 512), Image.LANCZOS).save(out)
    print(f"  ✔  {out.name}  (512×512)")


def generate_installer_sidebar(src: Image.Image) -> None:
    """410×797 panel for Inno Setup welcome/finish pages."""
    out = ASSETS / "installer_sidebar.png"
    canvas = _on_dark_canvas(src.convert("RGBA"), 410, 797, pad_frac=0.08)
    canvas.convert("RGB").save(out, format="PNG")
    print(f"  ✔  {out.name}  (410×797)")


def generate_installer_header(src: Image.Image) -> None:
    """55×58 image for Inno Setup inner-page headers."""
    out = ASSETS / "installer_header.png"
    sq = _square_crop(src.convert("RGBA"))
    sq.resize((55, 58), Image.LANCZOS).convert("RGB").save(out, format="PNG")
    print(f"  ✔  {out.name}  (55×58)")


def generate_icns(src: Image.Image) -> None:
    """macOS .icns icon — requires macOS with iconutil (ships with Xcode CLT)."""
    out = ASSETS / "camel_hot.icns"

    if sys.platform != "darwin":
        print("  ⚠  camel_hot.icns  skipped — iconutil requires macOS")
        print("     Run this script on macOS (or on the macOS CI runner)")
        print("     to generate the .icns file.")
        return

    sq = _square_crop(src.convert("RGBA"))

    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "CamelHot.iconset"
        iconset.mkdir()

        # Required filename/size pairs as per Apple spec
        spec = {
            "icon_16x16.png":      16,
            "icon_16x16@2x.png":   32,
            "icon_32x32.png":      32,
            "icon_32x32@2x.png":   64,
            "icon_128x128.png":    128,
            "icon_128x128@2x.png": 256,
            "icon_256x256.png":    256,
            "icon_256x256@2x.png": 512,
            "icon_512x512.png":    512,
            "icon_512x512@2x.png": 1024,
        }
        for fname, size in spec.items():
            sq.resize((size, size), Image.LANCZOS).save(
                iconset / fname, format="PNG"
            )

        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(out)],
            check=True,
        )

    print(f"  ✔  {out.name}  (macOS ICNS via iconutil)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not SOURCE.exists():
        print(f"ERROR: Source image not found: {SOURCE}")
        sys.exit(1)

    img = Image.open(SOURCE)
    print(f"Source : {SOURCE.name}  ({img.width}×{img.height}  {img.mode})")
    print()
    print("Generating assets …")

    generate_ico(img)
    generate_linux_png(img)
    generate_installer_sidebar(img)
    generate_installer_header(img)
    generate_icns(img)

    print()
    print("Done.  Commit the updated assets/ directory before building.")


if __name__ == "__main__":
    main()
