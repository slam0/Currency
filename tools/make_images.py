#!/usr/bin/env python3
"""Rysuje ikonę i ekrany startowe aplikacji (Resources/*.png). Wymaga Pillow: pip install pillow."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Resources")
FONT_DIR = "/usr/share/fonts/opentype/inter/"
NAME = "Currency"
FOOT = "nazarOvsky 2024-2026"
ACCENT_T, ACCENT_B = (250, 251, 252), (160, 167, 178)       # srebrny chrom (motyw Aluminium)

TLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "splash-tlo.png")

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

def radial_alpha(size, cx, cy, r0, r1, a0, a1):
    """maska L: krycie a0 w środku do a1 na promieniu r1 (do połysków)"""
    yy, xx = np.mgrid[0:size[1], 0:size[0]].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    t = np.clip((d - r0) / max(1.0, (r1 - r0)), 0, 1)
    return Image.fromarray((a0 + (a1 - a0) * t).clip(0, 255).astype(np.uint8), "L")

def brushed_panel(w, h, top, bot, amp, seed):
    a = np.asarray(vgrad((w, h), top, bot)).astype(np.float32)
    rng = np.random.RandomState(seed)
    n = rng.randn(h, w).astype(np.float32)
    k = np.ones(70, dtype=np.float32) / 70
    for y in range(h):
        n[y] = np.convolve(n[y], k, mode="same")
    n = n / (n.std() + 1e-6) * amp
    return Image.fromarray(np.clip(a + n[:, :, None], 0, 255).astype(np.uint8), "RGB")

def coin(base, cx, cy, r, glyph, gfont, tone):
    """moneta w 3D: cień, grubość krawędzi, ząbkowany rant, wgłębiona obwódka, wytłoczony znak, połysk"""
    S = base.size[0]
    light, dark = tone
    # cień na tle
    sh = Image.new("L", base.size, 0)
    ImageDraw.Draw(sh).ellipse([cx - r * 0.98 + r * 0.10, cy - r * 0.9 + r * 0.22, cx + r * 0.98 + r * 0.10, cy + r * 0.98 + r * 0.30], fill=215)
    sh = sh.filter(ImageFilter.GaussianBlur(S * 0.018))
    base.paste((0, 0, 0), (0, 0), sh)
    # grubość monety: ciemniejszy walec pod spodem
    th = r * 0.085
    edge = vgrad((S, S), (196, 202, 210), (70, 76, 88))
    m = Image.new("L", base.size, 0)
    md = ImageDraw.Draw(m)
    md.ellipse([cx - r, cy - r + th, cx + r, cy + r + th], fill=255)
    base.paste(edge, (0, 0), m)
    # rant: jasny metal i drobne ząbki
    rim = vgrad((S, S), (255, 255, 255), (118, 126, 138))
    m = Image.new("L", base.size, 0)
    ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    base.paste(rim, (0, 0), m)
    d = ImageDraw.Draw(base, "RGBA")
    for i in range(120):
        ang = 2 * math.pi * i / 120
        x0, y0 = cx + math.cos(ang) * r * 0.945, cy + math.sin(ang) * r * 0.945
        x1, y1 = cx + math.cos(ang) * r * 0.995, cy + math.sin(ang) * r * 0.995
        d.line([(x0, y0), (x1, y1)], fill=(40, 46, 58, 70), width=max(2, int(S * 0.0035)))
    # wgłębiona obwódka: ciemna u góry, jasna na dole
    r2 = r * 0.90
    groove = vgrad((S, S), (110, 118, 130), (250, 252, 253))
    m = Image.new("L", base.size, 0)
    ImageDraw.Draw(m).ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=255)
    base.paste(groove, (0, 0), m)
    # tarcza
    r3 = r * 0.855
    face = vgrad((S, S), light, dark)
    m = Image.new("L", base.size, 0)
    ImageDraw.Draw(m).ellipse([cx - r3, cy - r3, cx + r3, cy + r3], fill=255)
    base.paste(face, (0, 0), m)
    # miękkie rozjaśnienie od lewej góry
    hl = radial_alpha(base.size, cx - r * 0.35, cy - r * 0.45, 0, r * 1.1, 150, 0)
    hl = ImageChops.multiply(hl, m)
    base.paste((255, 255, 255), (0, 0), hl)
    # znak: wytłoczony (jasna krawędź u dołu, ciemna u góry)
    bb = d.textbbox((0, 0), glyph, font=gfont)
    tw, th2 = bb[2] - bb[0], bb[3] - bb[1]
    tx, ty = cx - tw / 2 - bb[0], cy - th2 / 2 - bb[1]
    off = max(2, int(S * 0.007))
    d.text((tx, ty + off), glyph, font=gfont, fill=(255, 255, 255, 255))
    d.text((tx, ty - off * 0.5), glyph, font=gfont, fill=(48, 54, 66, 255))
    gm = Image.new("L", base.size, 0)
    ImageDraw.Draw(gm).text((tx, ty), glyph, font=gfont, fill=255)
    gfill = vgrad((S, S), (112, 120, 134), (66, 73, 86))
    base.paste(gfill, (0, 0), gm)
    # połysk: sierp wzdłuż górnej krawędzi tarczy
    gl = Image.new("L", base.size, 0)
    gd = ImageDraw.Draw(gl)
    gd.ellipse([cx - r3, cy - r3, cx + r3, cy + r3], fill=255)
    cut = Image.new("L", base.size, 0)
    ImageDraw.Draw(cut).ellipse([cx - r3 * 1.25, cy - r3 * 0.30, cx + r3 * 1.25, cy + r3 * 1.9], fill=255)
    gl = ImageChops.subtract(gl, cut).filter(ImageFilter.GaussianBlur(S * 0.004))
    base.paste((255, 255, 255), (0, 0), gl.point(lambda v: int(v * 0.55)))
    # cienka linia odbicia światła na prawym dolnym brzegu rantu
    arc = Image.new("L", base.size, 0)
    ImageDraw.Draw(arc).arc([cx - r * 0.985, cy - r * 0.985, cx + r * 0.985, cy + r * 0.985], 20, 80, fill=200, width=max(2, int(S * 0.004)))
    base.paste((255, 255, 255), (0, 0), arc.filter(ImageFilter.GaussianBlur(1.2)))

def inset_panel(img, box, radius):
    """wpuszczona, ciemna szczotkowana płyta: cień wewnętrzny u góry, jasna krawędź u dołu"""
    x0, y0, x1, y1 = [int(v) for v in box]
    w, h = x1 - x0, y1 - y0
    S = img.size[0]
    # jasna krawędź od dołu/prawej (światło z góry-lewej), ciemna od góry/lewej
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 5], radius + 4, fill=(60, 66, 78, 255))
    d.rounded_rectangle([x0 - 2, y0 - 1, x1 + 3, y1 + 4], radius + 3, fill=(255, 255, 255, 255))
    panel = brushed_panel(w, h, (74, 80, 92), (30, 34, 42), 4.0, 11)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius, fill=255)
    img.paste(panel, (x0, y0), m)
    # cień wewnętrzny od góry
    inner = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ig = vgrad((w, h), (0, 0, 0), (0, 0, 0))
    alpha = np.zeros((h, w), np.float32)
    ys = np.arange(h, dtype=np.float32)
    alpha[:, :] = (np.clip(1 - ys / (h * 0.30), 0, 1) ** 2 * 190)[:, None]
    inner = Image.fromarray(np.dstack([np.zeros((h, w, 3), np.uint8), alpha.astype(np.uint8)]), "RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    layer.paste(inner, (x0, y0))
    mm = Image.new("L", img.size, 0)
    mm.paste(m, (x0, y0))
    layer.putalpha(ImageChops.multiply(layer.split()[3], mm))
    img.alpha_composite(layer) if img.mode == "RGBA" else img.paste(layer, (0, 0), layer)

def brushed_bg(S):
    """szczotkowane aluminium: pionowy gradient i poziome smugi"""
    g = vgrad((S, S), (222, 226, 232), (128, 135, 147))
    a = np.asarray(g).astype(np.float32)
    rng = np.random.RandomState(5)
    n = rng.randn(S, S).astype(np.float32)
    k = np.ones(120, dtype=np.float32) / 120
    for y in range(S):
        n[y] = np.convolve(n[y], k, mode="same")
    n = n / (n.std() + 1e-6) * 5.0
    a = np.clip(a + n[:, :, None], 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGB")

def screw(img, cx, cy, r):
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r - 5, cy - r - 2, cx + r + 5, cy + r + 8], fill=(255, 255, 255))
    d.ellipse([cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3], fill=(70, 76, 88))
    size = int(2 * r)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    dist = np.sqrt(((xx - r) / r + 0.35) ** 2 + ((yy - r) / r + 0.4) ** 2)
    t = np.clip(dist / 1.3, 0, 1)[:, :, None]
    col = np.array([252, 253, 254], np.float32) * (1 - t) + np.array([120, 127, 138], np.float32) * t
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255)
    img.paste(Image.fromarray(col.astype(np.uint8), "RGB"), (int(cx - r), int(cy - r)), m)
    w = max(3, int(r * 0.16))
    ang = 0.5
    for k in range(2):
        a = ang + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        L = r * 0.72
        px_, py_ = -uy * w, ux * w
        d.polygon([(cx - ux * L + px_, cy - uy * L + py_), (cx + ux * L + px_, cy + uy * L + py_),
                   (cx + ux * L - px_, cy + uy * L - py_), (cx - ux * L - px_, cy - uy * L - py_)], fill=(58, 64, 76))

def make_icon(S=1024):
    SS = 2
    T = S * SS
    if os.path.exists(TLO):
        # tło ikony: zielone promienie (kwadrat z środkiem promieni), na nich srebrne monety
        bg = Image.open(TLO).convert("RGB")
        w0 = bg.size[0]
        top = 566 - w0 // 2
        img = bg.crop((0, top, w0, top + w0)).resize((T, T), Image.LANCZOS)
        d = ImageDraw.Draw(img, "RGBA")
        gfont = font("Inter-Black.otf", int(T * 0.34))
        coin(img, T * 0.62, T * 0.37, T * 0.21, "$", gfont, ((238, 241, 245), (150, 158, 170)))
        coin(img, T * 0.40, T * 0.60, T * 0.255, "€", font("Inter-Black.otf", int(T * 0.37)), ((250, 251, 252), (166, 174, 186)))
    else:
        img = brushed_bg(T)
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, 0, T - 1, T - 1], outline=(255, 255, 255, 140), width=int(T * 0.004))
        inset_panel(img, (T * 0.115, T * 0.115, T * 0.885, T * 0.885), int(T * 0.075))
        gfont = font("Inter-Black.otf", int(T * 0.30))
        coin(img, T * 0.60, T * 0.385, T * 0.205, "$", gfont, ((238, 241, 245), (150, 158, 170)))
        coin(img, T * 0.40, T * 0.610, T * 0.235, "€", font("Inter-Black.otf", int(T * 0.34)), ((250, 251, 252), (166, 174, 186)))
        for (x, y) in ((0.058, 0.058), (0.942, 0.058), (0.058, 0.942), (0.942, 0.942)):
            screw(img, T * x, T * y, T * 0.026)
    # szklany połysk na górnej połowie
    gloss = Image.new("L", (T, T), 0)
    gd = ImageDraw.Draw(gloss)
    gd.ellipse([-T * 0.35, -T * 1.05, T * 1.35, T * 0.50], fill=255)
    gloss = gloss.filter(ImageFilter.GaussianBlur(T * 0.004))
    img.paste((255, 255, 255), (0, 0), gloss.point(lambda v: int(v * 0.22)))
    return img.resize((S, S), Image.LANCZOS)

def save_resized(img, size, name):
    img.resize((size, size), Image.LANCZOS).convert("RGB").save(os.path.join(OUT, name))


def make_splash(icon, W, H):
    cx, cy = W / 2, H * 0.40
    if os.path.exists(TLO):
        # zielone promienie (własne tło użytkownika, 640x1136; środek promieni na wysokości 566 px)
        bg = Image.open(TLO).convert("RGB")
        k = W / bg.size[0]
        bg = bg.resize((W, int(round(bg.size[1] * k))), Image.LANCZOS)
        center_y = 566 * k
        top = int(round((bg.size[1] - H) / 2))
        img = bg.crop((0, top, W, top + H))
        cy = center_y - top
        d = ImageDraw.Draw(img)
    else:
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

ICONSRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon-zrodlo.png")


def make_icon_user(S=1024):
    """Ikona z własnego obrazu użytkownika (zrzut z monetami na aluminium): kwadratowe wycięcie wokół monet."""
    from PIL import ImageFilter
    im = Image.open(ICONSRC).convert("RGB")
    cx, cy, side = 290, 415, 520
    c = im.crop((cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2))
    return c.resize((S, S), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 60, 2))


CANVA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "splash-canva.png")


def make_splash_canva():
    """Ekran powitalny zaprojektowany przez użytkownika (640x1136). Dla iPhone'a 4 (640x960): przycięcie
    po 88 px z góry i z dołu, a napis stopki jest wycinany po jasności (względem lokalnego tła)
    i przenoszony wyżej."""
    import numpy as np
    from PIL import ImageFilter
    im = Image.open(CANVA).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    y0, y1, off = 1046, 1096, 88
    lum = np.asarray(im.convert("L").crop((0, y0, 640, y1))).astype(np.float32)
    loc = np.asarray(im.convert("L").crop((0, y0, 640, y1)).filter(ImageFilter.MedianFilter(15))).astype(np.float32)
    al = np.clip((lum - loc) / (255 - loc + 1e-3), 0, 1)[:, :, None]
    crop = a[off:off + 960].copy()
    h = y1 - y0
    ny = 960 - 62 - h // 2 - 8
    crop[ny:ny + h] = crop[ny:ny + h] * (1 - al) + 255 * al
    out = Image.fromarray(np.clip(crop, 0, 255).astype(np.uint8))
    out.save(os.path.join(OUT, "Default@2x.png"))
    out.resize((320, 480), Image.LANCZOS).save(os.path.join(OUT, "Default.png"))
    im.save(os.path.join(OUT, "Default-568h@2x.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    icon = make_icon_user(1024) if os.path.exists(ICONSRC) else make_icon(1024)
    save_resized(icon, 114, "Icon@2x.png")
    save_resized(icon, 57, "Icon.png")
    save_resized(icon, 58, "Icon-Small@2x.png")
    save_resized(icon, 29, "Icon-Small.png")
    if os.path.exists(CANVA):
        make_splash_canva()
    else:
        s = make_splash(icon, 640, 960)
        s.save(os.path.join(OUT, "Default@2x.png"))
        s.resize((320, 480), Image.LANCZOS).save(os.path.join(OUT, "Default.png"))
        make_splash(icon, 640, 1136).save(os.path.join(OUT, "Default-568h@2x.png"))
    icon.resize((512, 512), Image.LANCZOS).convert("RGB").save(os.path.join(OUT, "..", "icon-512.png"))
    print("gotowe")
