#!/usr/bin/env python3
"""Rysuje ikonę i ekrany startowe aplikacji (Resources/*.png). Wymaga Pillow: pip install pillow."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Resources")
FONT_DIR = "/usr/share/fonts/opentype/inter/"
NAME = "Waluty"
FOOT = "nazarOvsky 2024-2026"
ACCENT_T, ACCENT_B = (250, 251, 252), (160, 167, 178)       # srebrny chrom (motyw Aluminium)

def font(name, size):
    for p in (FONT_DIR + name, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()

def vgrad(size, top, bot):
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return g.resize((w, h))

def rounded_mask(size, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=255)
    return m

def coin(base, cx, cy, r, glyph, top, bot, rim_top, rim_bot, gfont):
    """moneta z metaliczną obwódką i błyszczącą górą"""
    S = base.size[0]
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    # cień
    sh = Image.new("L", base.size, 0)
    ImageDraw.Draw(sh).ellipse([cx - r, cy - r + r * 0.10, cx + r, cy + r + r * 0.10], fill=190)
    sh = sh.filter(ImageFilter.GaussianBlur(S * 0.012))
    base.paste((0, 0, 0), (0, 0), sh)
    # obwódka
    rim = vgrad((S, S), rim_top, rim_bot)
    m = Image.new("L", base.size, 0)
    ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    base.paste(rim, (0, 0), m)
    # tarcza
    r2 = r * 0.86
    face = vgrad((S, S), top, bot)
    m2 = Image.new("L", base.size, 0)
    ImageDraw.Draw(m2).ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=255)
    base.paste(face, (0, 0), m2)
    # połysk
    gl = Image.new("L", base.size, 0)
    gd = ImageDraw.Draw(gl)
    gd.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=255)
    cut = Image.new("L", base.size, 0)
    ImageDraw.Draw(cut).ellipse([cx - r2 * 1.5, cy - r2 * 0.25, cx + r2 * 1.5, cy + r2 * 2.2], fill=255)
    gl = ImageChops.subtract(gl, cut).filter(ImageFilter.GaussianBlur(S * 0.004))
    base.paste((255, 255, 255), (0, 0), gl.point(lambda v: int(v * 0.45)))
    # znak
    d = ImageDraw.Draw(base)
    bb = d.textbbox((0, 0), glyph, font=gfont)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx, ty = cx - tw / 2 - bb[0], cy - th / 2 - bb[1]
    d.text((tx, ty + S * 0.006), glyph, font=gfont, fill=(255, 255, 255))
    d.text((tx, ty), glyph, font=gfont, fill=(70, 77, 90))

def brushed_bg(S):
    """szczotkowane aluminium: pionowy gradient i poziome smugi"""
    g = vgrad((S, S), (214, 218, 224), (112, 119, 131))
    a = np.asarray(g).astype(np.float32)
    rng = np.random.RandomState(5)
    n = rng.randn(S, S).astype(np.float32)
    k = np.ones(90, dtype=np.float32) / 90
    for y in range(S):
        n[y] = np.convolve(n[y], k, mode="same")
    n = n / (n.std() + 1e-6) * 5.0
    a = np.clip(a + n[:, :, None], 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGB")

def screw(img, cx, cy, r):
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r - 3, cy - r - 1, cx + r + 3, cy + r + 5], fill=(255, 255, 255))
    d.ellipse([cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2], fill=(70, 76, 88))
    size = int(2 * r)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    dist = np.sqrt(((xx - r) / r + 0.35) ** 2 + ((yy - r) / r + 0.4) ** 2)
    t = np.clip(dist / 1.3, 0, 1)[:, :, None]
    col = np.array([252, 253, 254], np.float32) * (1 - t) + np.array([120, 127, 138], np.float32) * t
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255)
    img.paste(Image.fromarray(col.astype(np.uint8), "RGB"), (int(cx - r), int(cy - r)), m)
    w = max(2, int(r * 0.18))
    d.rectangle([cx - r * 0.7, cy - w, cx + r * 0.7, cy + w], fill=(58, 64, 76))
    d.rectangle([cx - w, cy - r * 0.7, cx + w, cy + r * 0.7], fill=(58, 64, 76))

def make_icon(S=1024):
    img = brushed_bg(S)
    gfont = font("Inter-Black.otf", int(S * 0.34))
    # tylna moneta (dolar), przednia (euro) - srebrne, z metaliczną obwódką
    coin(img, S * 0.60, S * 0.38, S * 0.25, "$", (232, 235, 240), (150, 157, 168), (250, 251, 252), (110, 117, 128), gfont)
    coin(img, S * 0.40, S * 0.60, S * 0.28, "€", ACCENT_T, ACCENT_B, (255, 255, 255), (118, 125, 136), gfont)
    # śrubki w rogach
    for (x, y) in ((0.09, 0.09), (0.91, 0.09), (0.09, 0.91), (0.91, 0.91)):
        screw(img, S * x, S * y, S * 0.028)
    # szklany połysk na górnej połowie
    gloss = Image.new("L", (S, S), 0)
    gd = ImageDraw.Draw(gloss)
    gd.ellipse([-S * 0.35, -S * 1.05, S * 1.35, S * 0.52], fill=255)
    gloss = gloss.filter(ImageFilter.GaussianBlur(S * 0.004))
    img.paste((255, 255, 255), (0, 0), gloss.point(lambda v: int(v * 0.30)))
    return img

def save_resized(img, size, name):
    img.resize((size, size), Image.LANCZOS).convert("RGB").save(os.path.join(OUT, name))

def make_splash(icon, W, H):
    cx, cy = W / 2, H * 0.40
    img = Image.new("RGB", (W, H), (14, 14, 14))
    d = ImageDraw.Draw(img)
    n = 24
    R = math.hypot(W, H)
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = 2 * math.pi * (i + 1) / n
        if i % 2 == 0:
            d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=(70, 70, 72))
    # delikatne przyciemnienie rogów
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-W * 0.4, -H * 0.2, W * 1.4, H * 1.2], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(W * 0.15))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.composite(img, dark, vig.point(lambda v: int(120 + v * 135 / 255)))
    # ikona z zaokrąglonymi rogami i odbiciem
    sz = int(W * 0.37)
    ic = icon.resize((sz, sz), Image.LANCZOS)
    m = rounded_mask((sz, sz), int(sz * 0.22))
    x0, y0 = int(cx - sz / 2), int(cy - sz / 2)
    refl = ic.transpose(Image.FLIP_TOP_BOTTOM)
    fade = vgrad((sz, sz), (110, 110, 110), (0, 0, 0)).convert("L")
    rm = ImageChops.multiply(ImageChops.multiply(m.transpose(Image.FLIP_TOP_BOTTOM), fade), Image.new("L", (sz, sz), 255))
    refl_layer = Image.new("RGB", (sz, sz))
    refl_layer.paste(refl, (0, 0))
    img.paste(refl_layer.crop((0, 0, sz, int(sz * 0.45))), (x0, y0 + sz - int(sz * 0.12)), rm.crop((0, 0, sz, int(sz * 0.45))).point(lambda v: int(v * 0.5)))
    img.paste(ic, (x0, y0), m)
    d = ImageDraw.Draw(img)
    tf = font("Inter-BlackItalic.otf", int(W * 0.15))
    bb = d.textbbox((0, 0), NAME, font=tf)
    ty = int(cy + sz / 2 + H * 0.045)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0] + 2, ty + 3 - bb[1]), NAME, font=tf, fill=(0, 0, 0))
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], ty - bb[1]), NAME, font=tf, fill=(255, 255, 255))
    ff = font("Inter-Medium.otf", int(W * 0.033))
    spaced = " ".join(FOOT) if False else FOOT
    track = int(W * 0.006)
    widths = [d.textlength(ch, font=ff) + track for ch in spaced]
    total = sum(widths) - track
    x = cx - total / 2
    y = H - int(H * 0.045) - int(W * 0.033)
    for ch, w in zip(spaced, widths):
        d.text((x, y), ch, font=ff, fill=(235, 235, 235))
        x += w
    return img

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    icon = make_icon(1024)
    save_resized(icon, 114, "Icon@2x.png")
    save_resized(icon, 57, "Icon.png")
    save_resized(icon, 58, "Icon-Small@2x.png")
    save_resized(icon, 29, "Icon-Small.png")
    s = make_splash(icon, 640, 960)
    s.save(os.path.join(OUT, "Default@2x.png"))
    s.resize((320, 480), Image.LANCZOS).save(os.path.join(OUT, "Default.png"))
    make_splash(icon, 640, 1136).save(os.path.join(OUT, "Default-568h@2x.png"))
    icon.resize((512, 512), Image.LANCZOS).convert("RGB").save(os.path.join(OUT, "..", "icon-512.png"))
    print("gotowe")
