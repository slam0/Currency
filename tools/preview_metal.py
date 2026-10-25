#!/usr/bin/env python3
"""Podgląd motywu Aluminium (makieta rysowana w Pillow tymi samymi kolorami i wymiarami co w aplikacji).
Użycie: python3 tools/preview_metal.py wyjście.png   (potrzebne: Pillow, numpy, skompilowane wl_seg.c jako libwlseg.so)"""
import ctypes, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
SS = 4            # supersampling
PT = 2            # punkty -> piksele (retina)
K = SS * PT
W, H = 320, 480
FONT_DIR = "/usr/share/fonts/opentype/inter/"

def font(name, size):
    try:
        return ImageFont.truetype(FONT_DIR + name, int(size * K))
    except OSError:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(size * K))

def lib():
    for p in ("/tmp/claude-0/libwlseg.so", os.path.join(HERE, "..", "libwlseg.so")):
        if os.path.exists(p):
            l = ctypes.CDLL(p)
            l.wl_seg_poly.argtypes = [ctypes.c_int] + [ctypes.c_float] * 6 + [ctypes.POINTER(ctypes.c_float)]
            l.wl_seg_mask.argtypes = [ctypes.c_int]
            l.wl_seg_layout.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.POINTER(ctypes.c_float)]
            return l
    raise SystemExit("brak libwlseg.so (gcc -shared -fPIC wl_seg.c -o libwlseg.so)")

def px(v): return int(round(v * K))

def vgrad(w, h, stops):
    """stops: [(pozycja 0..1, (r,g,b[,a]))]"""
    ys = np.linspace(0, 1, h)
    chans = len(stops[0][1])
    out = np.zeros((h, w, chans), dtype=np.float32)
    for c in range(chans):
        out[:, :, c] = np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops])[:, None]
    return out

def to_img(a):
    a = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA" if a.shape[2] == 4 else "RGB")

def brushed_noise(w, h, amp, seed=7, length=60):
    rng = np.random.RandomState(seed)
    n = rng.randn(h, w).astype(np.float32)
    k = np.ones(length, dtype=np.float32) / length
    out = np.empty_like(n)
    for y in range(h):
        out[y] = np.convolve(n[y], k, mode="same")
    out = out / (out.std() + 1e-6)
    return out * amp

def brushed(w, h, stops, amp=5.0, seed=7, length=60):
    base = vgrad(w, h, stops)
    nz = brushed_noise(w, h, amp, seed, length)
    base[:, :, :3] += nz[:, :, None]
    return to_img(np.dstack([base[:, :, :3], np.full((h, w), 255, np.float32)]) if base.shape[2] == 3 else base)

def rrect_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], px(r), fill=255)
    return m

def paste_rrect(img, box, r, fill_img, shadow=None):
    x, y, w, h = [px(v) for v in box]
    if shadow:
        dy, blur, alpha = shadow
        sh = Image.new("L", img.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle([x, y + px(dy), x + w, y + px(dy) + h], px(r), fill=int(255 * alpha))
        sh = sh.filter(ImageFilter.GaussianBlur(px(blur)))
        img.paste((0, 0, 0), (0, 0), sh)
    img.paste(fill_img.resize((w, h)), (x, y), rrect_mask(w, h, r))

def stroke_rrect(d, box, r, color, width=1.0):
    x, y, w, h = [px(v) for v in box]
    d.rounded_rectangle([x, y, x + w, y + h], px(r), outline=color, width=max(1, px(width)))

# ---------------- elementy ----------------

def screw(img, cx, cy, diam, angle):
    r = px(diam / 2)
    cx, cy = px(cx), px(cy)
    # cień/rowek
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([cx - r - px(0.8), cy - r - px(0.2), cx + r + px(0.8), cy + r + px(1.4)], fill=(255, 255, 255, 150))
    d.ellipse([cx - r - px(0.6), cy - r - px(0.6), cx + r + px(0.6), cy + r + px(0.6)], fill=(60, 66, 76, 235))
    # kopuła: gradient promienisty
    size = 2 * r
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    dx = (xx - r) / r; dy = (yy - r) / r
    # światło z lewej góry
    dist = np.sqrt((dx + 0.35) ** 2 + (dy + 0.4) ** 2)
    t = np.clip(dist / 1.3, 0, 1)
    c0 = np.array([252, 253, 254], np.float32); c1 = np.array([120, 127, 138], np.float32)
    col = c0[None, None, :] * (1 - t[:, :, None]) + c1[None, None, :] * t[:, :, None]
    dome = to_img(np.dstack([col, np.full((size, size), 255, np.float32)]))
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255)
    img.paste(dome, (cx - r, cy - r), m)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(70, 76, 88, 255), width=max(1, px(0.6)))
    # krzyżak
    a = math.radians(angle)
    for k in range(2):
        ang = a + k * math.pi / 2
        ux, uy = math.cos(ang), math.sin(ang)
        L = r * 0.72
        wd = max(1.5, px(0.85)) / 2
        px_, py_ = -uy * wd, ux * wd
        pts = [(cx - ux * L + px_, cy - uy * L + py_), (cx + ux * L + px_, cy + uy * L + py_),
               (cx + ux * L - px_, cy + uy * L - py_), (cx - ux * L - px_, cy - uy * L - py_)]
        d.polygon(pts, fill=(58, 64, 76, 255))
        # jasna krawędź dolna
        d.line([(cx - ux * L - px_ + 1, cy - uy * L - py_ + 1.5), (cx + ux * L - px_ + 1, cy + uy * L - py_ + 1.5)], fill=(255, 255, 255, 120), width=1)

def chrome_button(img, box, r=9):
    x, y, w, h = box
    stops = [(0, (255, 255, 255)), (0.12, (244, 246, 248)), (0.48, (206, 211, 218)), (0.5, (158, 165, 175)), (0.78, (188, 194, 202)), (1, (226, 230, 235))]
    g = brushed(px(w), px(h), stops, amp=2.5, seed=int(x + y), length=40)
    paste_rrect(img, (x, y, w, h), r, g, shadow=(1.2, 1.4, 0.35))
    d = ImageDraw.Draw(img, "RGBA")
    stroke_rrect(d, (x, y, w, h), r, (84, 90, 101, 255), 1.0)
    stroke_rrect(d, (x + 1, y + 1, w - 2, h - 2), r - 1, (255, 255, 255, 190), 0.8)

def text_engraved(img, xy, s, fnt, color, shadow=(255, 255, 255, 220), anchor="la", dy=1.0):
    d = ImageDraw.Draw(img, "RGBA")
    x, y = px(xy[0]), px(xy[1])
    d.text((x, y + px(dy)), s, font=fnt, fill=shadow, anchor=anchor)
    d.text((x, y), s, font=fnt, fill=color, anchor=anchor)

def seg_text(img, L, text, box, on, off, glow=False, slant=0.10):
    bx, by, bw, bh = box
    cells = (ctypes.c_int * 40)(); xs = (ctypes.c_float * 40)(); tw = ctypes.c_float()
    n = L.wl_seg_layout(text.encode("utf-8"), cells, xs, 40, ctypes.byref(tw))
    padl, padr, pady = 10, 14, 7
    availw = bw - padl - padr
    availh = bh - 2 * pady
    ch = min(availh, availw / max(tw.value, 0.5))
    t = ch * 0.115
    g = t * 0.10
    x0 = bx + bw - padr - tw.value * ch
    y0 = by + (bh - ch) / 2
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    offl = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer); do = ImageDraw.Draw(offl)
    cy = y0 + ch / 2
    def shear(xp, yp): return (px(xp + (-slant) * (yp - cy)), px(yp))
    pts = (ctypes.c_float * 12)()
    for i in range(n):
        c = cells[i]; cx_ = x0 + xs[i] * ch
        if chr(c).isdigit() or c == ord('-'):
            mask = L.wl_seg_mask(c)
            for s in range(7):
                L.wl_seg_poly(s, cx_, y0, 0.56 * ch, ch, t, g, pts)
                poly = [shear(pts[2 * k], pts[2 * k + 1]) for k in range(6)]
                if c != ord('-'): do.polygon(poly, fill=off)
                if mask & (1 << s): dl.polygon(poly, fill=on)
        elif c in (ord('.'), ord(',')):
            d_ = t * 1.15
            bxx = cx_ + (0.17 * ch - d_) / 2; byy = y0 + ch - d_
            poly = [shear(bxx, byy), shear(bxx + d_, byy), shear(bxx + d_, byy + d_), shear(bxx, byy + d_)]
            dl.polygon(poly, fill=on)
            if c == ord(','):
                tail = [shear(bxx + d_ * 0.2, byy + d_), shear(bxx + d_, byy + d_), shear(bxx + d_ * 0.2 - d_ * 0.45, byy + d_ + d_ * 1.0)]
                dl.polygon(tail, fill=on)
    if glow:
        gl = layer.filter(ImageFilter.GaussianBlur(px(5)))
        img.alpha_composite(gl) if img.mode == "RGBA" else img.paste(gl, (0, 0), gl)
    else:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sh.paste((0, 0, 0, 55), (px(0.8), px(1.2)), layer.split()[3])
        sh = sh.filter(ImageFilter.GaussianBlur(px(0.6)))
        img.alpha_composite(sh)
    img.alpha_composite(offl)
    img.alpha_composite(layer)

def lcd(img, L, text, box, kind="pale", editing=False):
    x, y, w, h = box
    d = ImageDraw.Draw(img, "RGBA")
    # wpuszczona rama: ciemna u góry, jasna na dole
    frame = vgrad(px(w), px(h), [(0, (96, 102, 114)), (1, (214, 219, 226))]).astype(np.float32)
    frame = np.dstack([frame, np.full((px(h), px(w)), 255, np.float32)])
    paste_rrect(img, (x, y, w, h), 9, to_img(frame))
    stroke_rrect(d, (x - 0.5, y - 0.5, w + 1, h + 1), 9.5, (255, 255, 255, 150), 0.8)
    gx, gy, gw, gh = x + 3, y + 3, w - 6, h - 6
    if kind == "pale":
        top, bot, on, off = (166, 184, 148), (194, 209, 172), (26, 34, 24, 255), (26, 34, 24, 26)
    else:
        top, bot, on, off = (10, 14, 14), (24, 30, 30), (255, 150, 30, 255), (255, 150, 30, 22)
    glass = vgrad(px(gw), px(gh), [(0, top), (1, bot)])
    glass = np.dstack([glass, np.full((px(gh), px(gw)), 255, np.float32)])
    paste_rrect(img, (gx, gy, gw, gh), 6.5, to_img(glass))
    # wewnętrzny cień u góry
    sh = vgrad(px(gw), px(gh), [(0, (0, 0, 0, 90)), (0.22, (0, 0, 0, 20)), (0.4, (0, 0, 0, 0)), (1, (0, 0, 0, 0))])
    shi = to_img(sh)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); layer.paste(shi, (px(gx), px(gy)))
    m = Image.new("L", img.size, 0); m.paste(rrect_mask(px(gw), px(gh), 6.5), (px(gx), px(gy)))
    layer.putalpha(ImageChops.multiply(layer.split()[3], m))
    img.alpha_composite(layer)
    seg_text(img, L, text, (gx, gy, gw, gh), on, off, glow=(kind != "pale"))
    # połysk szkła
    gl = vgrad(px(gw), px(gh), [(0, (255, 255, 255, 70)), (0.5, (255, 255, 255, 20)), (0.5001, (255, 255, 255, 0)), (1, (255, 255, 255, 0))])
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); layer.paste(to_img(gl), (px(gx), px(gy)))
    layer.putalpha(ImageChops.multiply(layer.split()[3], m))
    img.alpha_composite(layer)
    stroke_rrect(d, (gx, gy, gw, gh), 6.5, (0, 0, 0, 150), 0.8)

def build(out):
    L = lib()
    img = Image.new("RGBA", (px(W), px(H)), (200, 204, 210, 255))
    # tło: szczotkowane aluminium
    bg = brushed(px(W), px(H), [(0, (206, 210, 216)), (1, (186, 190, 197))], amp=4.0, seed=3, length=90)
    img.paste(bg, (0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    # pasek górny (status 20 + nav 44)
    sb = brushed(px(W), px(20), [(0, (60, 64, 72)), (1, (30, 33, 38))], amp=2, seed=1)
    img.paste(sb, (0, 0))
    nav = brushed(px(W), px(44), [(0, (244, 246, 248)), (0.5, (206, 211, 218)), (0.5001, (190, 196, 205)), (1, (160, 166, 176))], amp=3.0, seed=11, length=80)
    img.paste(nav, (0, px(20)))
    d.rectangle([0, px(20), px(W), px(20) + 1], fill=(255, 255, 255, 220))
    d.rectangle([0, px(64) - px(1), px(W), px(64)], fill=(70, 76, 88, 255))
    f_title = font("Inter-Bold.otf", 20)
    text_engraved(img, (W / 2, 42), "Przelicznik", f_title, (58, 62, 70, 255), anchor="mm")
    # przycisk paska
    f_btn = font("Inter-Bold.otf", 12)
    chrome_button(img, (W - 12 - 62, 27, 62, 30), 6)
    text_engraved(img, (W - 12 - 31, 42), "Odśwież", f_btn, (50, 55, 64, 255), anchor="mm")
    # płyta
    px0, py0, pw, ph = 8, 64 + 8, 304, 198
    plate = brushed(px(pw), px(ph), [(0, (248, 249, 250)), (0.5, (226, 229, 234)), (1, (196, 201, 209))], amp=3.5, seed=21, length=100)
    paste_rrect(img, (px0, py0, pw, ph), 14, plate, shadow=(2, 3, 0.45))
    stroke_rrect(d, (px0, py0, pw, ph), 14, (80, 86, 98, 255), 1.0)
    stroke_rrect(d, (px0 + 1, py0 + 1, pw - 2, ph - 2), 13, (255, 255, 255, 230), 1.0)
    for i, (sx, sy) in enumerate([(11, 11), (pw - 11, 11), (11, ph - 11), (pw - 11, ph - 11)]):
        screw(img, px0 + sx, py0 + sy, 9, [20, 70, 110, 160][i])
    f_lab = font("Inter-Bold.otf", 10)
    f_name = font("Inter-Medium.otf", 12)
    f_code = font("Inter-Bold.otf", 20)
    # wiersz 1
    text_engraved(img, (px0 + 26, py0 + 11), "KWOTA", f_lab, (96, 103, 116, 255))
    lcd(img, L, "1 234,56", (px0 + 16, py0 + 26, 190, 46), "pale")
    chrome_button(img, (px0 + 16 + 190 + 8, py0 + 26, 82, 46))
    text_engraved(img, (px0 + 16 + 190 + 8 + 34, py0 + 49), "PLN", f_code, (40, 45, 54, 255), anchor="mm")
    d.polygon([(px(px0 + 16 + 190 + 8 + 66), px(py0 + 47)), (px(px0 + 16 + 190 + 8 + 74), px(py0 + 47)), (px(px0 + 16 + 190 + 8 + 70), px(py0 + 52))], fill=(60, 66, 78, 255))
    text_engraved(img, (px0 + 20, py0 + 76), "złoty polski", f_name, (96, 103, 116, 255))
    # rowek + przycisk zamiany
    gy = py0 + 99
    d.line([(px(px0 + 18), px(gy)), (px(px0 + pw - 18), px(gy))], fill=(120, 126, 138, 255), width=max(1, px(0.5)))
    d.line([(px(px0 + 18), px(gy + 0.8)), (px(px0 + pw - 18), px(gy + 0.8))], fill=(255, 255, 255, 255), width=max(1, px(0.5)))
    chrome_button(img, (px0 + pw / 2 - 26, gy - 15, 52, 30), 15)
    ax = px0 + pw / 2
    for dx, up in ((-7, True), (7, False)):
        cxx = ax + dx
        d.line([(px(cxx), px(gy - 7 if up else gy - 7)), (px(cxx), px(gy + 7))], fill=(52, 58, 68, 255), width=px(2.2))
        if up: d.polygon([(px(cxx), px(gy - 10)), (px(cxx + 5), px(gy - 3)), (px(cxx - 5), px(gy - 3))], fill=(52, 58, 68, 255))
        else: d.polygon([(px(cxx), px(gy + 10)), (px(cxx + 5), px(gy + 3)), (px(cxx - 5), px(gy + 3))], fill=(52, 58, 68, 255))
    # wiersz 2
    text_engraved(img, (px0 + 26, py0 + 116), "WYNIK", f_lab, (96, 103, 116, 255))
    lcd(img, L, "287,73", (px0 + 16, py0 + 131, 190, 46), "pale")
    chrome_button(img, (px0 + 16 + 190 + 8, py0 + 131, 82, 46))
    text_engraved(img, (px0 + 16 + 190 + 8 + 34, py0 + 154), "EUR", f_code, (40, 45, 54, 255), anchor="mm")
    d.polygon([(px(px0 + 16 + 190 + 8 + 66), px(py0 + 152)), (px(px0 + 16 + 190 + 8 + 74), px(py0 + 152)), (px(px0 + 16 + 190 + 8 + 70), px(py0 + 157))], fill=(60, 66, 78, 255))
    text_engraved(img, (px0 + 20, py0 + 181), "euro", f_name, (96, 103, 116, 255))
    # kurs
    text_engraved(img, (W / 2, 64 + 8 + 198 + 18), "1 PLN = 0,2326 EUR", font("Inter-Bold.otf", 15), (58, 62, 70, 255), anchor="mm")
    text_engraved(img, (W / 2, 64 + 8 + 198 + 40), "Kursy z 24 paź 2026 · open.er-api.com", font("Inter-Medium.otf", 12), (96, 103, 116, 255), anchor="mm")
    # nagłówek sekcji
    hy = 64 + 8 + 198 + 56
    hd = brushed(px(W), px(26), [(0, (92, 98, 110)), (1, (56, 61, 70))], amp=2.5, seed=31, length=70)
    img.paste(hd, (0, px(hy)))
    d.rectangle([0, px(hy), px(W), px(hy) + 1], fill=(255, 255, 255, 90))
    d.rectangle([0, px(hy + 26) - 1, px(W), px(hy + 26)], fill=(0, 0, 0, 200))
    screw(img, 13, hy + 13, 7, 30); screw(img, W - 13, hy + 13, 7, 100)
    f_h = font("Inter-Bold.otf", 13)
    text_engraved(img, (28, hy + 13), "Ulubione waluty", f_h, (236, 240, 245, 255), shadow=(0, 0, 0, 200), anchor="lm", dy=-1.0)
    # wiersze
    rows = [("4,30 EUR", "euro · 1 PLN = 0,2326 EUR"), ("3,98 USD", "dolar amerykański · 1 PLN = 0,2511 USD")]
    ry = hy + 26
    for i, (a, b) in enumerate(rows):
        rh = 56
        cell = brushed(px(W), px(rh), [(0, (253, 253, 254)), (0.5, (243, 245, 247)), (0.5001, (235, 238, 242)), (1, (226, 229, 234))], amp=2.5, seed=40 + i, length=90)
        img.paste(cell, (0, px(ry)))
        d.rectangle([0, px(ry), px(W), px(ry) + 1], fill=(255, 255, 255, 230))
        d.rectangle([0, px(ry + rh) - 1, px(W), px(ry + rh)], fill=(150, 156, 166, 255))
        text_engraved(img, (14, ry + 20), a, font("Inter-Bold.otf", 17), (30, 33, 40, 255), anchor="lm")
        text_engraved(img, (14, ry + 40), b, font("Inter-Medium.otf", 13), (98, 106, 120, 255), anchor="lm")
        ry += rh
    # pasek zakładek
    ty = H - 49
    tb = brushed(px(W), px(49), [(0, (232, 235, 239)), (0.5, (190, 196, 205)), (0.5001, (172, 178, 188)), (1, (140, 146, 156))], amp=3.0, seed=51, length=80)
    img.paste(tb, (0, px(ty)))
    d.rectangle([0, px(ty), px(W), px(ty) + 1], fill=(255, 255, 255, 230))
    d.rectangle([0, px(ty) - 1, px(W), px(ty)], fill=(70, 76, 88, 255))
    # zaznaczenie
    sel = Image.new("RGBA", img.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sel)
    sd.rounded_rectangle([px(8), px(ty + 3), px(8 + 90), px(ty + 46)], px(6), fill=(0, 0, 0, 60))
    img.alpha_composite(sel)
    for i, (lab, on) in enumerate((("Przelicznik", True), ("Kursy", False), ("Ustawienia", False))):
        cxx = 8 + 45 + i * 107
        col = (22, 118, 220, 255) if on else (84, 90, 102, 255)
        text_engraved(img, (cxx, ty + 40), lab, font("Inter-Bold.otf", 10), col, anchor="mm", dy=1.0)
        d.rounded_rectangle([px(cxx - 11), px(ty + 8), px(cxx + 11), px(ty + 28)], px(3), fill=col)
    out_img = img.resize((W * PT, H * PT), Image.LANCZOS).convert("RGB")
    out_img.save(out)

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "podglad-aluminium.png")
