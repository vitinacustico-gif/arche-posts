#!/usr/bin/env python3
"""Fábrica GTA 6 — gera as peças de um dia a partir de uma pauta JSON.

uso:  GTA6_FONT_KEY=<chave> python3 gta6/fabrica/gerar.py gta6/pautas/AAAA-MM-DD.json [--so 03,05]
      (sem GTA6_FONT_KEY, lê a chave de ~/.gta6_fontkey)

Saídas:
  gta6/midia/<data>/<id>.jpg            post único (1080x1350)
  gta6/midia/<data>/<id>_NN.jpg         slides de carrossel (1080x1350)
  gta6/midia/<data>/<id>.mp4 + _capa.jpg  Reel (1080x1920, 30 fps, com trilha sintetizada)
  gta6/calendario.json                  atualizado com os itens do dia (data, hora, formato, arquivos, legenda)

Toda a arte é gerada por código (sem imagem de terceiros). A fonte de títulos (Pricedown, licença
Typodermic) fica criptografada no repositório e só é aberta com a chave privada do Victor.
"""
import json, math, os, pathlib, random, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FAB = pathlib.Path(__file__).resolve().parent
RAIZ = FAB.parent
CFG = json.load(open(FAB / "config.json", encoding="utf-8"))
C = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in CFG["cores"].items()}
FPS = 30


# ───────────────────────── fontes ─────────────────────────
def _fonte_titulo():
    destino = pathlib.Path(tempfile.gettempdir()) / "gta6_titulo.ttf"
    if destino.exists() and destino.stat().st_size > 1000:
        return str(destino)
    chave = os.environ.get("GTA6_FONT_KEY")
    if not chave:
        p = pathlib.Path.home() / ".gta6_fontkey"
        chave = p.read_text().strip() if p.exists() else None
    if not chave:
        # sem a chave (ex.: tarefa agendada), usa a Anton (licença OFL, livre) no lugar da Pricedown
        print("aviso: sem GTA6_FONT_KEY, títulos em Anton", file=sys.stderr)
        return str(FAB / "fonts/Anton-400.ttf")
    subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-in", str(FAB / "fonts/pricedown.enc"),
                    "-out", str(destino), "-pass", "pass:" + chave], check=True)
    os.chmod(destino, 0o600)
    return str(destino)


TIT = _fonte_titulo()
INTER = {w: str(FAB / f"fonts/Inter-{w}.ttf") for w in ("400", "700", "900")}
_cache = {}


def ft(caminho, tam):
    k = (caminho, int(tam))
    if k not in _cache:
        _cache[k] = ImageFont.truetype(caminho, int(tam))
    return _cache[k]


# ───────────────────────── fundo Vice (gerado por código) ─────────────────────────
def _hex_lerp(stops, n):
    """stops: [(pos 0..1, (r,g,b)), ...] → array n x 3"""
    xs = np.linspace(0, 1, n)
    out = np.zeros((n, 3), np.float32)
    for c in range(3):
        out[:, c] = np.interp(xs, [s[0] for s in stops], [s[1][c] for s in stops])
    return out


def _palmeira(d, base_x, base_y, topo_x, topo_y, escala, cor=(7, 2, 12, 255), seed=0):
    rnd = random.Random(seed)
    # tronco: curva quadrática com espessura decrescente
    cx, cy = (base_x + topo_x) / 2 + 60 * escala * (1 if topo_x > base_x else -1), (base_y + topo_y) / 2
    for i in range(80):
        u = i / 79
        x = (1 - u) ** 2 * base_x + 2 * (1 - u) * u * cx + u ** 2 * topo_x
        y = (1 - u) ** 2 * base_y + 2 * (1 - u) * u * cy + u ** 2 * topo_y
        r = (26 - 14 * u) * escala
        d.ellipse([x - r, y - r, x + r, y + r], fill=cor)
    # folhas: arcos caídos, afinando na ponta
    for k in range(9):
        ang = -math.pi + k * (math.pi / 8) + rnd.uniform(-0.12, 0.12)
        comp = (230 + rnd.uniform(-30, 40)) * escala
        caida = (90 + rnd.uniform(0, 70)) * escala
        pts_sup, pts_inf = [], []
        for j in range(24):
            u = j / 23
            px = topo_x + math.cos(ang) * comp * u
            py = topo_y + math.sin(ang) * comp * u * 0.55 + caida * u ** 2
            w = 20 * escala * (1 - u) ** 0.8 + 1
            nx, ny = -math.sin(ang), math.cos(ang)
            pts_sup.append((px + nx * w, py + ny * w))
            pts_inf.append((px - nx * w, py - ny * w))
        d.polygon(pts_sup + pts_inf[::-1], fill=cor)
    d.ellipse([topo_x - 22 * escala, topo_y - 18 * escala, topo_x + 22 * escala, topo_y + 18 * escala], fill=cor)


class Cena:
    """Fundo pôr do sol de Vice. render(t) devolve uint8 HxWx3; parado (t=0) serve para imagens."""

    def __init__(self, W, H, horizonte=0.70, sol=0.27, escurecer=0.5, seed=7, grao=7.0):
        self.W, self.H = W, H
        self.hy = int(H * horizonte)
        rnd = np.random.default_rng(seed)
        ceu = _hex_lerp([(0, (14, 4, 26)), (0.42, (52, 12, 72)), (0.74, (170, 30, 110)), (1.0, (255, 112, 70))], self.hy)
        mar = _hex_lerp([(0, (70, 14, 70)), (0.35, (34, 8, 46)), (1, (9, 3, 15))], H - self.hy)
        grad = np.concatenate([ceu, mar], 0)
        self.base = np.repeat(grad[:, None, :], W, 1)
        # estrelas
        for _ in range(int(W * H / 9000)):
            x, y = rnd.integers(0, W), rnd.integers(0, int(self.hy * 0.55))
            b = rnd.uniform(90, 220)
            self.base[y, x] = np.maximum(self.base[y, x], b)
        # sol (disco com degradê) — guardado como máscara + cor
        self.r = int(W * sol)
        self.sx, self.sy = W // 2, self.hy - int(self.r * 0.55)
        yy, xx = np.mgrid[0:H, 0:W]
        dist = np.sqrt((xx - self.sx) ** 2 + (yy - self.sy) ** 2)
        self.disco = np.clip((self.r - dist) / 2.0, 0, 1).astype(np.float32)
        self.disco[self.hy:] = 0
        tons = _hex_lerp([(0, C["amarelo"]), (0.55, C["laranja"]), (1, C["magenta"])], 2 * self.r + 1)
        idx = np.clip(yy - (self.sy - self.r), 0, 2 * self.r).astype(int)
        self.cor_sol = tons[idx]
        self.brilho = np.exp(-((dist - self.r * 0.6).clip(0)) / (self.r * 0.9))[..., None] * np.array([90, 30, 60], np.float32)
        self.brilho[self.hy:] *= 0.35
        # palmeiras (camada RGBA fixa)
        pal = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(pal)
        e = W / 1080
        _palmeira(d, -40 * e, H + 40, 150 * e, self.hy - 210 * e, 1.15 * e, seed=1)
        _palmeira(d, 40 * e, H + 40, 250 * e, self.hy - 60 * e, 0.8 * e, seed=2)
        _palmeira(d, W + 50 * e, H + 40, W - 170 * e, self.hy - 240 * e, 1.2 * e, seed=3)
        _palmeira(d, W - 40 * e, H + 40, W - 270 * e, self.hy - 70 * e, 0.75 * e, seed=4)
        self.pal_a = (np.asarray(pal)[..., 3:4] / 255.0).astype(np.float32)
        self.pal_rgb = np.asarray(pal)[..., :3].astype(np.float32)
        # véu escuro em cima (legibilidade) + vinheta
        v = np.ones((H, 1), np.float32)
        topo = int(H * 0.62)
        v[:topo, 0] = 1 - escurecer * (1 - np.linspace(0, 1, topo) ** 1.6)
        r2 = ((xx - W / 2) / (W / 2)) ** 2 * 0.5 + ((yy - H * 0.5) / (H / 2)) ** 2 * 0.5
        self.vinheta = (v[:, :1] * (1 - 0.35 * np.clip(r2, 0, 1.3) ** 1.4))[..., None].astype(np.float32)
        self.grao = [rnd.normal(0, grao, (H // 2, W // 2)).astype(np.float32) for _ in range(4)]
        self.yy = yy

    def render(self, t=0.0):
        img = self.base.copy()
        # listras do sol descendo devagar (efeito synthwave)
        rel = (self.yy - self.sy) / self.r
        fase = (t * 0.18) % 1.0
        faixa = ((rel * 7 + fase * 7) % 1.0)
        corte = (rel > -0.15) & (faixa < np.clip((rel + 0.15) * 0.75, 0, 0.55))
        m = self.disco * (~corte)
        img = img * (1 - m[..., None]) + self.cor_sol * m[..., None]
        img = img + self.brilho
        # reflexo no mar: riscos horizontais que tremulam
        h0 = self.hy
        n = self.H - h0
        linhas = np.arange(n)
        larg = self.r * (1 - linhas / n) ** 1.2 * (0.7 + 0.3 * np.sin(linhas * 0.37 + t * 3.1))
        on = (np.sin(linhas * 0.55 - t * 2.2) > 0.15) & (linhas < n * 0.75)
        for i in np.nonzero(on)[0]:
            w = int(larg[i])
            if w < 6:
                continue
            y = h0 + i
            a = 0.55 * (1 - i / n)
            img[y, self.sx - w:self.sx + w] = img[y, self.sx - w:self.sx + w] * (1 - a) + np.array(C["rosa"], np.float32) * a
        img = img * (1 - self.pal_a) + self.pal_rgb * self.pal_a
        img = img * self.vinheta
        g = Image.fromarray(self.grao[int(t * 12) % 4]).resize((self.W, self.H))
        img = img + np.asarray(g, np.float32)[..., None]
        return np.clip(img, 0, 255).astype(np.uint8)


# ───────────────────────── texto ─────────────────────────
COLA = (("R$ ", "R$\u00a0"), ("Series X|S", "Series\u00a0X|S"), (" %", "\u00a0%"))


def quebra(texto, fonte, largura):
    for x, y in COLA:
        texto = texto.replace(x, y)
    linhas, atual = [], ""
    for p in [w for w in texto.split(" ") if w]:
        teste = (atual + " " + p).strip()
        if fonte.getlength(teste) <= largura or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def bloco_titulo(linhas, largura_max, tam=170, tam_min=60, altura_max=None, destaque=(), cor=None, sombra=True, alinhar="center"):
    """Linhas em Pricedown, maiúsculas, branco com contorno preto e sombra magenta. Devolve RGBA."""
    linhas = [l.upper() for l in linhas]
    while True:
        f = ft(TIT, tam)
        sw = max(3, int(tam * 0.055))
        ws = [f.getbbox(l, stroke_width=sw) for l in linhas]
        larg = max(b[2] - b[0] for b in ws)
        lh = int(tam * 0.98)
        alt = lh * len(linhas) + int(tam * 0.25)
        if (larg <= largura_max and (altura_max is None or alt <= altura_max)) or tam <= tam_min:
            break
        tam = int(tam * 0.94)
    off = int(tam * 0.07)
    img = Image.new("RGBA", (larg + 2 * sw + off + 8, alt + off + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, l in enumerate(linhas):
        b = ws[i]
        x = ((img.width - off - (b[2] - b[0])) / 2 if alinhar == "center" else sw) - b[0]
        y = i * lh + sw - f.getbbox("H")[1] + 4
        if sombra:
            d.text((x + off, y + off), l, font=f, fill=C["magenta"] + (255,), stroke_width=sw, stroke_fill=C["magenta"] + (255,))
        fill = (C["amarelo"] if i in destaque else (cor or C["branco"])) + (255,)
        d.text((x, y), l, font=f, fill=fill, stroke_width=sw, stroke_fill=(0, 0, 0, 255))
    return img


def bloco_texto(texto, largura, tam=44, peso="700", cor=(255, 255, 255), alinhar="center", espaco=1.28, sombra=True, caixa=True):
    f = ft(INTER[peso], tam)
    linhas = []
    for par in texto.split("\n"):
        linhas += quebra(par, f, largura) or [""]
    lh = int(tam * espaco)
    pad = int(tam * 0.55) if caixa else 0
    real = max(f.getlength(l) for l in linhas)
    larg_img = int(real + 2 * pad) if alinhar == "center" else largura + 2 * pad
    img = Image.new("RGBA", (larg_img, lh * len(linhas) + 12 + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if caixa:
        d.rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=int(tam * 0.6), fill=(10, 3, 18, 150))
    for i, l in enumerate(linhas):
        w = f.getlength(l)
        x = pad + ((real - w) / 2 if alinhar == "center" else 0)
        y = pad + i * lh + int(tam * 0.08)
        if sombra:
            d.text((x + 2, y + 3), l, font=f, fill=(0, 0, 0, 170))
        d.text((x, y), l, font=f, fill=cor + (255,))
    return img


def pilula(texto, tam=30, fundo=None, cor=(255, 255, 255), pad=(26, 14)):
    f = ft(INTER["900"], tam)
    w = int(f.getlength(texto))
    b = f.getbbox("ÁG")
    h = b[3] - b[1]
    img = Image.new("RGBA", (w + 2 * pad[0], h + 2 * pad[1]), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=img.height // 2, fill=(fundo or C["magenta"]) + (255,))
    d.text((pad[0], pad[1] - b[1]), texto, font=f, fill=cor + (255,))
    return img


def colar(base, camada, x, y, alpha=1.0):
    if alpha < 1:
        a = camada.getchannel("A").point(lambda v: int(v * alpha))
        camada = camada.copy()
        camada.putalpha(a)
    base.alpha_composite(camada, (int(x), int(y)))


def moldura(img, tag=None, contador=None, link=True):
    """O mockup da casa: @ no topo, selo à direita, rodapé de página de fã e 'link na bio'."""
    W, H = img.size
    d = ImageDraw.Draw(img)
    f = ft(INTER["900"], 34)
    d.ellipse([64, 70, 86, 92], fill=C["magenta"] + (255,))
    d.text((100, 62), CFG["handle"], font=f, fill=(255, 255, 255, 255))
    if contador:
        p = pilula(contador, 26, fundo=(20, 8, 30))
        colar(img, p, W - 64 - p.width, 58)
    elif tag:
        p = pilula(tag.upper(), 26)
        colar(img, p, W - 64 - p.width, 58)
    f2 = ft(INTER["700"], 24)
    d.text((64, H - 70), "PÁGINA DE FÃ • NÃO OFICIAL", font=f2, fill=(255, 255, 255, 150))
    if link:
        p = pilula("LINK NA BIO", 24, fundo=(255, 255, 255), cor=(12, 4, 20), pad=(22, 12))
        colar(img, p, W - 64 - p.width, H - 84)
    return img


# ───────────────────────── formatos ─────────────────────────
_cenas = {}


def cena(W, H, **kw):
    k = (W, H, tuple(sorted(kw.items())))
    if k not in _cenas:
        _cenas[k] = Cena(W, H, **kw)
    return _cenas[k]


def post(item, saida):
    W, H = 1080, 1350
    img = Image.fromarray(cena(W, H, horizonte=0.76, sol=0.24, escurecer=0.55).render(0)).convert("RGBA")
    tipo = item.get("tipo", "frase")
    tit = bloco_titulo(item["linhas"], W - 140, tam=item.get("tam", 170), altura_max=560, destaque=item.get("destaque", []))
    pecas = [tit]
    if item.get("texto"):
        pecas.append(bloco_texto(item["texto"], W - 180, 44, "700"))
    if tipo == "enquete":
        ops = []
        for letra, txt in zip("AB", item["opcoes"]):
            p = pilula(f"{letra}  {txt.upper()}", 38, fundo=(C["magenta"] if letra == "A" else (46, 14, 70)), pad=(36, 22))
            ops.append(p)
        lin = Image.new("RGBA", (W - 120, max(o.height for o in ops)), (0, 0, 0, 0))
        x = (lin.width - sum(o.width for o in ops) - 30) // 2
        for o in ops:
            lin.alpha_composite(o, (x, 0)); x += o.width + 30
        pecas.append(lin)
    if item.get("sub"):
        pecas.append(bloco_texto(item["sub"], W - 200, 38, "400", cor=(255, 230, 245)))
    gap = 34
    total = sum(p.height for p in pecas) + gap * (len(pecas) - 1)
    y = max(170, (int(H * 0.70) - total) // 2 + 40)
    for p in pecas:
        colar(img, p, (W - p.width) / 2, y); y += p.height + gap
    if item.get("fonte"):
        d = ImageDraw.Draw(img)
        f = ft(INTER["400"], 24)
        tx = "Fonte: " + item["fonte"]
        d.text(((W - f.getlength(tx)) / 2, H - 130), tx, font=f, fill=(255, 255, 255, 170))
    moldura(img, tag=item.get("tag", {"noticia": "NOTÍCIA", "enquete": "ENQUETE", "contagem": "CONTAGEM"}.get(tipo, "GTA 6")))
    arq = saida / f"{item['id']}.jpg"
    img.convert("RGB").save(arq, quality=90)
    return [arq]


def carrossel(item, saida):
    W, H = 1080, 1350
    slides = item["slides"]
    # Instagram aceita até 10 itens por carrossel: sem slide de fecho se não couber
    com_fecho = len(slides) + 2 <= 10
    n = len(slides) + (2 if com_fecho else 1)
    if n > 10:
        raise SystemExit(f"carrossel {item['id']} com {n} slides (máx. 10)")
    arqs = []
    # capa
    img = Image.fromarray(cena(W, H, horizonte=0.76, sol=0.24, escurecer=0.55).render(0)).convert("RGBA")
    tit = bloco_titulo(item["capa"], W - 140, tam=175, altura_max=600, destaque=item.get("destaque", []))
    pecas = [tit]
    if item.get("sub"):
        pecas.append(bloco_texto(item["sub"], W - 200, 40, "700"))
    pecas.append(pilula("ARRASTA PRO LADO  >>", 28, fundo=(255, 255, 255), cor=(12, 4, 20)))
    total = sum(p.height for p in pecas) + 36 * (len(pecas) - 1)
    y = max(170, (int(H * 0.72) - total) // 2 + 40)
    for p in pecas:
        colar(img, p, (W - p.width) / 2, y); y += p.height + 36
    moldura(img, contador=f"01/{n:02d}", link=False)
    arqs.append(saida / f"{item['id']}_01.jpg"); img.convert("RGB").save(arqs[-1], quality=90)
    # miolo: fundo mais escuro, sol baixo
    fundo = cena(W, H, horizonte=0.86, sol=0.17, escurecer=0.72).render(0.4)
    for i, s in enumerate(slides, start=2):
        img = Image.fromarray(fundo).convert("RGBA")
        num = bloco_titulo([f"{i - 1:02d}"], 400, tam=150, destaque=[0], alinhar="left")
        tit = bloco_titulo(quebra_titulo(s["titulo"]), W - 150, tam=110, tam_min=56, altura_max=360, alinhar="left")
        corpo = bloco_texto(s["texto"], W - 230, 44, "700", alinhar="left") if s.get("texto") else None
        y = 190
        colar(img, num, 70, y); y += num.height + 10
        colar(img, tit, 70 - 6, y); y += tit.height + 28
        if corpo:
            colar(img, corpo, 58, y)
        moldura(img, contador=f"{i:02d}/{n:02d}", link=False)
        arqs.append(saida / f"{item['id']}_{i:02d}.jpg"); img.convert("RGB").save(arqs[-1], quality=90)
    if not com_fecho:
        return arqs
    # fecho
    img = Image.fromarray(cena(W, H, horizonte=0.76, sol=0.24, escurecer=0.55).render(0.8)).convert("RGBA")
    fecho = item.get("fecho", {"titulo": ["SALVA", "ESSE POST"], "texto": "E manda pro parça que vai jogar com você no dia 19."})
    pecas = [bloco_titulo(fecho["titulo"], W - 140, tam=160, destaque=[len(fecho["titulo"]) - 1]),
             bloco_texto(fecho["texto"], W - 200, 42, "700"),
             pilula("GRUPO VIP + OFERTAS: LINK NA BIO", 28)]
    total = sum(p.height for p in pecas) + 36 * 2
    y = (int(H * 0.72) - total) // 2 + 40
    for p in pecas:
        colar(img, p, (W - p.width) / 2, y); y += p.height + 36
    moldura(img, contador=f"{n:02d}/{n:02d}", link=False)
    arqs.append(saida / f"{item['id']}_{n:02d}.jpg"); img.convert("RGB").save(arqs[-1], quality=90)
    return arqs


def quebra_titulo(t):
    palavras = t.split()
    if len(palavras) <= 2:
        return [t]
    meio = len(palavras) // 2
    return [" ".join(palavras[:meio]), " ".join(palavras[meio:])]


# ───────────────────────── Reel ─────────────────────────
SR = 48000


def trilha(dur, bpm=104, seed=3, eventos=()):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    beat = 60 / bpm
    m = np.zeros(n, np.float32)

    def env(k, tau):
        return np.exp(-np.arange(k) / SR / tau)

    def add(x, t0, g):
        i = int(t0 * SR)
        if i >= n:
            return
        x = x[: n - i] * g
        m[i:i + len(x)] += x

    hz = lambda k: 440 * 2 ** ((k - 69) / 12)
    acordes = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]
    b = 0
    while b * beat < dur:
        tb = b * beat
        k = int(0.32 * SR); tt = np.arange(k) / SR
        add(np.sin(2 * np.pi * np.cumsum(48 + 120 * np.exp(-tt * 28)) / SR) * env(k, 0.11), tb, 0.55)
        if b % 2 == 1:
            k = int(0.2 * SR); add(rng.standard_normal(k) * env(k, 0.05), tb, 0.12)
        for e in (0, 0.5):
            k = int(0.04 * SR); x = rng.standard_normal(k) * env(k, 0.008); add(np.diff(x, prepend=0), tb + e * beat, 0.05)
        raiz, notas = acordes[(b // 4) % 4]
        k = int(beat * 0.9 * SR); tt = np.arange(k) / SR
        saw = sum(np.sin(2 * np.pi * hz(raiz - 12) * h * tt) / h for h in range(1, 6))
        add(saw * np.minimum(1, tt / 0.01) * env(k, 0.25), tb, 0.16)
        if b % 4 == 0:
            k = int(beat * 4 * SR); tt = np.arange(k) / SR
            pad = sum(np.sin(2 * np.pi * hz(x + 12) * (1 + d) * tt) for x in notas for d in (-0.003, 0.003))
            fade = np.minimum(1, tt / 0.4) * np.minimum(1, (tt[-1] - tt) / 0.4)
            add(pad * fade, tb, 0.025)
        b += 1
    for (te, tipo) in eventos:
        if tipo == "impacto":
            k = int(0.45 * SR); tt = np.arange(k) / SR
            add(np.tanh(np.sin(2 * np.pi * np.cumsum(50 + 60 * np.exp(-tt * 20)) / SR) * env(k, 0.14) * 1.5), te, 0.35)
        elif tipo == "passagem":
            k = int(0.7 * SR); x = rng.standard_normal(k); u = np.linspace(0, 1, k)
            e = np.where(u < 0.6, (u / 0.6) ** 2.2, ((1 - u) / 0.4) ** 1.6)
            x = np.convolve(x, np.ones(6) / 6, "same") * e
            add(x, te - 0.42, 0.2)
    m[:240] *= np.linspace(0, 1, 240)
    f = int(0.6 * SR); m[-f:] *= np.linspace(1, 0, f)
    m = m / (np.abs(m).max() + 1e-9) * 0.89
    return np.stack([m, m], 1)


def reel(item, saida):
    W, H = 1080, 1920
    dur = float(item.get("dur", 9.0))
    sc = cena(W, H, horizonte=0.74, sol=0.30, escurecer=0.5, grao=2.5)
    linhas = item["linhas"]
    blocos = [bloco_titulo([l], W - 130, tam=item.get("tam", 230), tam_min=80, destaque=([0] if i in item.get("destaque", []) else [])) for i, l in enumerate(linhas)]
    # todas as linhas no mesmo tamanho (o menor que coube)
    sub = bloco_texto(item["sub"], W - 180, 50, "700") if item.get("sub") else None
    t_lin = [0.45 * i for i in range(len(blocos))]
    t_sub = (t_lin[-1] + 0.6) if sub else None
    t_fim = dur - 2.6
    cta = item.get("cta", ["LINK", "NA BIO"])
    cta_bloco = bloco_titulo(cta, W - 140, tam=190, destaque=[len(cta) - 1])
    cta_sub = bloco_texto(item.get("cta_sub", "Grupo VIP de ofertas e o guia do GTA 6"), W - 200, 46, "700")
    eventos = [(t, "impacto") for t in t_lin[1:]] + [(t_fim, "passagem")]
    altura = sum(b.height for b in blocos) + (sub.height + 40 if sub else 0)
    y0 = max(300, int(H * 0.40 - altura / 2))
    tmp = pathlib.Path(tempfile.mkdtemp())
    wav = tmp / "a.wav"
    a = (trilha(dur, eventos=eventos) * 32767).astype(np.int16)
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.tobytes())
    arq = saida / f"{item['id']}.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-maxrate", "5M", "-bufsize", "10M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(arq)],
                           stdin=subprocess.PIPE)
    capa_t = (t_sub or t_lin[-1]) + 0.5
    capa = None
    for f in range(int(dur * FPS)):
        t = f / FPS
        img = Image.fromarray(sc.render(t)).convert("RGBA")
        if t < t_fim:
            y = y0
            for b, tl in zip(blocos, t_lin):
                k = 1.0 if tl == 0 else min(1, max(0, (t - tl) / 0.22))
                if k > 0:
                    e = 1 - (1 - k) ** 3
                    s = 1.28 - 0.28 * e
                    bb = b.resize((int(b.width * s), int(b.height * s))) if s != 1 else b
                    colar(img, bb, (W - bb.width) / 2, y + (b.height - bb.height) / 2, alpha=min(1, k * 1.6))
                y += b.height
            if sub and t >= t_sub:
                k = min(1, (t - t_sub) / 0.3)
                colar(img, sub, (W - sub.width) / 2, y + 40 + 30 * (1 - k), alpha=k)
            moldura(img, tag=item.get("tag", "GTA 6"), link=False)
        else:
            k = min(1, (t - t_fim) / 0.25)
            s = 1.2 - 0.2 * (1 - (1 - k) ** 3)
            cb = cta_bloco.resize((int(cta_bloco.width * s), int(cta_bloco.height * s)))
            yc = int(H * 0.36 - cta_bloco.height / 2)
            colar(img, cb, (W - cb.width) / 2, yc + (cta_bloco.height - cb.height) / 2, alpha=min(1, k * 1.6))
            colar(img, cta_sub, (W - cta_sub.width) / 2, yc + cta_bloco.height + 40, alpha=min(1, max(0, (t - t_fim - 0.2) / 0.3)))
            moldura(img, tag="SEGUE A PÁGINA", link=False)
        rgb = img.convert("RGB")
        if capa is None and t >= capa_t:
            capa = rgb
        enc.stdin.write(rgb.tobytes())
    enc.stdin.close(); enc.wait()
    capa_arq = saida / f"{item['id']}_capa.jpg"
    (capa or rgb).save(capa_arq, quality=88)
    item["_thumb_ms"] = int(capa_t * 1000)
    return [arq, capa_arq]


# ───────────────────────── legenda + calendário ─────────────────────────
def legenda(item):
    corpo = item["legenda"].strip()
    return f"{corpo}\n\n{CFG['cta_padrao']}\n\n{CFG['rodape_legenda']}\n{CFG['hashtags']}"


def main():
    pauta_p = pathlib.Path(sys.argv[1])
    so = None
    if "--so" in sys.argv:
        so = set(sys.argv[sys.argv.index("--so") + 1].split(","))
    pauta = json.load(open(pauta_p, encoding="utf-8"))
    data = pauta["data"]
    saida = RAIZ / "midia" / data
    saida.mkdir(parents=True, exist_ok=True)
    cal_p = RAIZ / "calendario.json"
    cal = json.load(open(cal_p, encoding="utf-8")) if cal_p.exists() else []
    horas = CFG["horarios"]
    for n, item in enumerate(pauta["itens"]):
        if so and item["id"] not in so:
            continue
        fmt = item["formato"]
        arqs = {"post": post, "carrossel": carrossel, "reel": reel}[fmt](item, saida)
        rel = [str(a.relative_to(RAIZ.parent)) for a in arqs]
        entrada = {"id": f"{data}-{item['id']}", "data": data, "hora": item.get("hora") or horas[n % len(horas)],
                   "formato": fmt, "titulo": " ".join(item.get("linhas") or item.get("capa")),
                   "arquivos": [r for r in rel if not r.endswith("_capa.jpg")],
                   "legenda": legenda(item)}
        if fmt == "reel":
            entrada["capa"] = [r for r in rel if r.endswith("_capa.jpg")][0]
            entrada["thumb_offset_ms"] = item["_thumb_ms"]
        cal = [c for c in cal if c["id"] != entrada["id"]] + [entrada]
        print("ok", entrada["id"], fmt, entrada["hora"], len(entrada["arquivos"]), "arquivo(s)", flush=True)
    cal.sort(key=lambda c: (c["data"], c["hora"]))
    json.dump(cal, open(cal_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
