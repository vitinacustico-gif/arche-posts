"""Renderiza os slides da série "reflexão" (1080x1350, padrão do carrossel aprovado em 16/10/2026).
Foto tratada (P&B quente + grão) dissolvendo no preto, título vermelho na fonte de display da Arche,
texto em Inter Bold, contador no topo e @archeagencia no rodapé."""
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
import random, re

W, H = 1080, 1350
RED = (229, 21, 45); WHITE = (244, 244, 244); GREY = (160, 160, 160); BG = (6, 6, 6)
M = 84


def grade(img, w, h, focus=0.45):
    img = ImageOps.fit(img.convert("RGB"), (w, h), centering=(0.5, focus))
    g = ImageOps.grayscale(img)
    g = ImageEnhance.Contrast(g).enhance(1.25)
    g = ImageEnhance.Brightness(g).enhance(0.78)
    tint = ImageOps.colorize(g, black=(8, 6, 6), white=(236, 226, 218), mid=(110, 92, 86))
    random.seed(3)
    noise = Image.effect_noise((w, h), 40).convert("RGB")
    return Image.blend(tint, noise, 0.06)


def fade(h, start):
    m = Image.new("L", (1, h), 255)
    for y in range(start, h):
        t = (y - start) / max(1, (h - start))
        m.putpixel((0, y), int(255 * (1 - t) ** 1.6))
    return m.resize((W, h))


def wrap(d, text, f, maxw):
    out = []
    for para in text.split("\n"):
        if not para.strip():
            out.append(""); continue
        cur = ""
        for w in para.split(" "):
            t = (cur + " " + w).strip()
            if d.textlength(t, font=f) <= maxw or not cur:
                cur = t
            else:
                out.append(cur); cur = w
        out.append(cur)
    return out


def chrome(c, idx, total, F):
    m = Image.new("L", (1, 190))
    for y in range(190):
        m.putpixel((0, y), int(170 * (1 - y / 190) ** 1.5))
    c.paste(Image.new("RGB", (W, 190), (0, 0, 0)), (0, 0), m.resize((W, 190)))
    d = ImageDraw.Draw(c)
    d.rectangle((M, 72, M + 56, 78), fill=RED)
    n = f"{idx:02d}/{total:02d}"
    d.text((W - M - d.textlength(n, font=F["meta"]), 60), n, font=F["meta"], fill=GREY)
    t = "@archeagencia"
    d.text(((W - d.textlength(t, font=F["meta"])) / 2, H - 84), t, font=F["meta"], fill=GREY)


def cover_words(text):
    """'TEXTO *VERMELHO*. AQUI' -> [(palavra, vermelho?, cola_na_anterior?)]"""
    words = []
    for m in re.finditer(r"\S+", text):
        w = m.group(0)
        parts = re.split(r"(\*)", w)
        glue = False
        for p in parts:
            if p == "*":
                words.append(("*", None, None)); continue
            if p:
                words.append((p, None, glue)); glue = True
    out, red = [], False
    for w, _, g in words:
        if w == "*":
            red = not red; continue
        out.append((w, red, g))
    return out


def render_cover(photo, text, F, total, focus=0.45):
    c = Image.new("RGB", (W, H), BG)
    c.paste(grade(photo, W, H, focus), (0, 0), fade(H, int(H * 0.30)))
    d = ImageDraw.Draw(c)
    units = []
    for w, r, g in cover_words(text):
        if g and units:
            units[-1].append((w, r))
        else:
            units.append([(w, r)])
    maxw, maxh = W - 2 * M, int(H * 0.56)
    size = 150
    while True:
        f = F["disp"](size)
        sp = d.textlength(" ", font=f)
        uw = lambda u: sum(d.textlength(w, font=f) for w, _ in u)
        lines, cur, curw = [], [], 0
        for u in units:
            ww = uw(u)
            if cur and curw + sp + ww > maxw:
                lines.append(cur); cur, curw = [], 0
            curw += (sp if cur else 0) + ww; cur.append(u)
        if cur:
            lines.append(cur)
        lh = int(size * F["disp_lh"])
        widest = max(sum(uw(u) for u in l) + sp * (len(l) - 1) for l in lines)
        if (lh * len(lines) <= maxh and widest <= maxw) or size <= 60:
            break
        size -= 4
    y = H - 215 - lh * len(lines)
    for l in lines:
        x = M
        for u in l:
            for w, r in u:
                d.text((x, y), w, font=f, fill=RED if r else WHITE)
                x += d.textlength(w, font=f)
            x += sp
        y += lh
    d.text((M, H - 150), "ARRASTE PARA O LADO  →", font=F["metab"], fill=GREY)
    chrome(c, 1, total, F)
    return c


def render_slide(photo, head, body, idx, total, F, focus=0.45):
    c = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(c)
    maxw = W - 2 * M
    hs, bs = 92, 44
    while True:
        fh, fb = F["disp"](hs), F["body"](bs)
        hl = wrap(d, head, fh, maxw); bl = wrap(d, body, fb, maxw)
        widest = max(d.textlength(l, font=fh) for l in hl)
        hlh, blh, gap = int(hs * F["disp_lh"]), int(bs * 1.28), int(bs * 0.6)
        th = len(hl) * hlh + 46 + sum(gap if l == "" else blh for l in bl)
        if (th <= H - 140 - 470 and widest <= maxw) or bs <= 32:
            break
        bs -= 2; hs = max(56, hs - 4)
    ytext = H - 140 - th
    ph_h = ytext + 120
    c.paste(grade(photo, W, ph_h, focus), (0, 0), fade(ph_h, int(ph_h * 0.45)))
    d = ImageDraw.Draw(c)
    y = ytext
    for l in hl:
        d.text((M, y), l, font=fh, fill=RED); y += hlh
    y += 46
    for l in bl:
        if l == "":
            y += gap; continue
        d.text((M, y), l, font=fb, fill=WHITE); y += blh
    chrome(c, idx, total, F)
    return c


def fonts(disp_path, body_path, meta_path, disp_lh=1.02):
    return {"disp": lambda s: ImageFont.truetype(disp_path, s),
            "body": lambda s: ImageFont.truetype(body_path, s),
            "meta": ImageFont.truetype(meta_path, 28),
            "metab": ImageFont.truetype(body_path, 28),
            "disp_lh": disp_lh}
