#!/usr/bin/env python3
"""Generate the full Android launcher icon set from the desktop .ico.

Legacy square/round mipmaps plus adaptive-icon foreground layers.
Run with the repo venv: .venv/bin/python scripts/gen_android_icons.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "android_app" / "app" / "src" / "main" / "res"
BACKGROUND = (32, 33, 36, 255)  # dark slate, matches the desktop icon's look

LEGACY_SIZES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
FOREGROUND_SIZES = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}


def source_logo() -> Image.Image:
    ico = Image.open(ROOT / "ncm_converter.ico")
    return ico.convert("RGBA").resize((256, 256), Image.LANCZOS)


def legacy_icon(logo: Image.Image, size: int, round_mask: bool) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), BACKGROUND)
    scaled = ImageOps.contain(logo, (int(size * 0.82), int(size * 0.82)), Image.LANCZOS)
    canvas.alpha_composite(
        scaled, ((size - scaled.width) // 2, (size - scaled.height) // 2)
    )
    if round_mask:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        canvas.putalpha(mask)
    return canvas


def foreground(logo: Image.Image, size: int) -> Image.Image:
    # Adaptive-icon foreground: logo inside the 66/108 safe zone.
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    scaled = ImageOps.contain(logo, (int(size * 0.50), int(size * 0.50)), Image.LANCZOS)
    canvas.alpha_composite(
        scaled, ((size - scaled.width) // 2, (size - scaled.height) // 2)
    )
    return canvas


def main() -> None:
    logo = source_logo()
    for dpi, size in LEGACY_SIZES.items():
        out = RES / "mipmap-{dpi}".format(dpi=dpi)
        out.mkdir(parents=True, exist_ok=True)
        legacy_icon(logo, size, round_mask=False).save(out / "ic_launcher.png")
        legacy_icon(logo, size, round_mask=True).save(out / "ic_launcher_round.png")
    for dpi, size in FOREGROUND_SIZES.items():
        out = RES / "mipmap-{dpi}".format(dpi=dpi)
        out.mkdir(parents=True, exist_ok=True)
        foreground(logo, size).save(out / "ic_launcher_foreground.png")
    print("icons generated under", RES)


if __name__ == "__main__":
    main()
