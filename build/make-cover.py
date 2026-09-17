"""Render og-cover.jpg -- the 1200x630 link preview, in the deck's palette."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent.parent / "og-cover.jpg"
W, H = 1200, 630

BG      = (22, 22, 25)
WHITE   = (243, 243, 241)
ACCENT  = (226, 84, 92)
MUTED   = (158, 158, 166)
DIM     = (138, 138, 146)
PANEL   = (30, 30, 34)
RULE    = (49, 49, 56)

FONTS = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"]
FALLBACK = ["C:/Windows/Fonts/seguisb.ttf", "C:/Windows/Fonts/segoeui.ttf"]


def font(size, bold=True):
    return ImageFont.truetype(FONTS[0 if bold else 1], size)


def has_glyph(f, ch):
    """A missing glyph renders as nothing or as the same box as an unassigned
    codepoint; either way it must not reach the JPEG."""
    try:
        return f.getmask(ch).getbbox() != f.getmask("\ufff0").getbbox()
    except Exception:
        return False


PESO_FONT_BOLD = None
if not has_glyph(font(40), "\u20b1"):
    for path in FALLBACK:
        if Path(path).exists():
            PESO_FONT_BOLD = path
            break


def blob(img, cx, cy, r, color, alpha, falloff=1.7):
    """One of the deck's ambient gradient blobs, flattened.

    A blurred solid ellipse still reads as a disc with a soft rim; the deck's
    blobs are radial-gradient(...) fading all the way to transparent, so the
    mask needs the same falloff -- brightest at the centre, zero at the rim.
    """
    ramp = Image.radial_gradient("L").resize((2 * r, 2 * r), Image.BICUBIC)
    ramp = ramp.point(lambda v: int(alpha * (1.0 - v / 255.0) ** falloff))
    mask = Image.new("L", img.size, 0)
    mask.paste(ramp, (cx - r, cy - r))
    layer = Image.new("RGB", img.size, color)
    return Image.composite(layer, img, mask)


def tracked(d, xy, text, f, fill, track):
    """Draw text with letter-spacing, and return the width used."""
    x, y = xy
    for ch in text:
        use = f
        if ch == "\u20b1" and PESO_FONT_BOLD:
            use = ImageFont.truetype(PESO_FONT_BOLD, f.size)
        d.text((x, y), ch, font=use, fill=fill)
        x += use.getlength(ch) + track
    return x - xy[0]


def main():
    img = Image.new("RGB", (W, H), BG)
    img = blob(img, 100, 20,  620, (66, 46, 57), 255, 1.5)
    img = blob(img, 700, 700, 560, (31, 37, 48), 255, 1.5)
    img = blob(img, 430, 120, 420, (96, 42, 48), 150, 2.1)
    d = ImageDraw.Draw(img)

    # Right rail, as on the cover slide.
    rail_x = 880
    d.rectangle([rail_x, 0, W, H], fill=PANEL)
    d.line([rail_x, 0, rail_x, H], fill=(38, 38, 44), width=2)

    pad = 74
    tracked(d, (pad, 92), "LIVE PRESENTATION SYSTEM", font(21), ACCENT, 6.2)

    d.text((pad, 168), "THE DECK THAT", font=font(66), fill=WHITE)
    tracked(d, (pad, 246), "FOLLOWS YOU", font(66), ACCENT, 0)

    d.line([pad, 356, rail_x - 96, 356], fill=RULE, width=2)

    body = font(25, bold=False)
    d.text((pad, 388), "Put it on a projector, let the room scan a code,", font=body, fill=MUTED)
    d.text((pad, 424), "and every phone follows the slide you are on.", font=body, fill=MUTED)

    tracked(d, (pad, 500), "SELF-CONTAINED HTML · NO APP, NO SIGN-IN", font(18), (156, 156, 162), 4.2)
    d.text((pad, 532), "Your phone is the remote: notes, timer,", font=font(24), fill=WHITE)
    d.text((pad, 566), "pointer", font=font(24), fill=WHITE)

    # Rail: the three numbers that matter.
    rx = rail_x + 56
    rows = [("~80 ms", "STAGE TO PHONE"),
            ("3", "AUDIENCE MODES"),
            ("1 file", "NOTHING TO INSTALL")]
    y = 128
    for i, (big, cap) in enumerate(rows):
        tracked(d, (rx, y), big, font(56 if len(big) < 7 else 46), WHITE if i == 0 else (210, 64, 73), 0)
        tracked(d, (rx, y + 72), cap, font(15 if len(cap) > 18 else 17), DIM, 3.2)
        y += 148
        if i < 2:
            d.line([rx, y - 40, W - 56, y - 40], fill=(45, 45, 52), width=1)

    img.save(OUT, "JPEG", quality=88, optimize=True, progressive=True)
    print("%s  %d bytes  peso-fallback=%s" % (OUT.name, OUT.stat().st_size, PESO_FONT_BOLD))


if __name__ == "__main__":
    main()
