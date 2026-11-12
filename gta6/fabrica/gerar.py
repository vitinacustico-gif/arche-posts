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
import datetime, json, math, os, pathlib, random, subprocess, sys, tempfile, wave
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


def _fundo_foto(caminho, W, H, escurecer=0.62, foco=0.5):
    """Foto oficial/licenciada em tela cheia com tratamento Vice e véu para leitura do título."""
    foto = Image.open(caminho).convert("RGB")
    r = max(W / foto.width, H / foto.height)
    foto = foto.resize((int(foto.width * r) + 1, int(foto.height * r) + 1), Image.LANCZOS)
    l = int((foto.width - W) * foco); t = (foto.height - H) // 2
    foto = foto.crop((l, t, l + W, t + H))
    arr = np.asarray(foto).astype(np.float32)
    arr = (arr - 128) * 1.08 + 128
    grad = np.linspace(0, 1, H)[:, None, None]
    tint = (1 - grad) * np.array([120, 50, 200]) + grad * np.array([255, 80, 150])
    arr = arr * 0.82 + (arr * tint / 255 * 1.4) * 0.18
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    veu = np.zeros((H, 1, 4), np.uint8)
    topo = int(H * 0.62)
    veu[:topo, 0, 3] = (255 * escurecer * (1 - np.linspace(0, 1, topo) ** 1.6)).astype(np.uint8)
    base = int(H * 0.22)
    veu[H - base:, 0, 3] = (190 * np.linspace(0, 1, base) ** 1.3).astype(np.uint8)
    veu[:, 0, :3] = (8, 2, 14)
    img.alpha_composite(Image.fromarray(np.repeat(veu, W, 1), "RGBA"))
    return img


ANTON = str(FAB / "fonts/Anton-400.ttf")


def _texto_rico(d, x, y, larg, texto, tam, cor=(28, 24, 22), cor_neg=None, esp=1.32):
    """Escreve texto com **negrito** e quebra de linha automática. Devolve o y final."""
    fr, fn = ft(INTER["400"], tam), ft(INTER["700"], tam)
    pal, neg = [], False
    for w in texto.split():
        ini = w.startswith("**"); fim = w.endswith("**") and len(w) > 2
        if ini: neg = True
        limpo = w.strip("*")
        pal.append((limpo, neg))
        if fim: neg = False
    linhas, atual, lw = [], [], 0
    for w, n in pal:
        f = fn if n else fr
        wl = f.getlength(w + " ")
        if atual and lw + f.getlength(w) > larg:
            linhas.append(atual); atual, lw = [], 0
        atual.append((w, n)); lw += wl
    if atual: linhas.append(atual)
    for ln in linhas:
        cx = x
        for w, n in ln:
            f = fn if n else fr
            d.text((cx, y), w, font=f, fill=(cor_neg or cor) if n else cor)
            cx += f.getlength(w + " ")
        y += int(tam * esp)
    return y


def documento(item, saida):
    """Post 'comunicado oficial': papel sobre a mesa, texto formal, motivo GTA 6, carimbo, foto 3x4 e assinatura."""
    import random
    from PIL import ImageFilter
    W, H = 1080, 1350
    rnd = random.Random(item["id"])
    fundo = _fundo_foto(RAIZ.parent / item["imagem"], W, H, 0.9, item.get("foco", 0.5)).filter(ImageFilter.GaussianBlur(6))
    fundo.alpha_composite(Image.new("RGBA", (W, H), (6, 3, 10, 120)))
    PW, PH = 900, 1110
    papel = Image.new("RGBA", (PW, PH), (242, 234, 219, 255))
    ruido = (np.random.default_rng(7).normal(0, 7, (PH, PW))).clip(-18, 18)
    arr = np.asarray(papel).astype(float); arr[..., :3] += ruido[..., None]
    gy = np.linspace(-1, 1, PH)[:, None]; gx = np.linspace(-1, 1, PW)[None, :]
    arr[..., :3] -= (np.sqrt(gx ** 2 + gy ** 2) * 16)[..., None]
    papel = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(papel)
    tinta, verm, cinza = (26, 22, 20), (196, 28, 36), (110, 104, 98)
    # cabeçalho
    tf = ft(_fonte_titulo(), 64)
    d.text((60, 52), "NERD", font=tf, fill=tinta); d.text((60, 118), "GTA", font=tf, fill=verm)
    fl = ft(INTER["700"], 20)
    for k, l in enumerate(item.get("local", ["VICE CITY", "LEONIDA", "EUA"])):
        tx = "  ".join(l); d.text((PW - 60 - fl.getlength(tx), 66 + k * 32), tx, font=fl, fill=cinza)
    d.line([(60, 210), (PW - 60, 210)], fill=tinta, width=3)
    # título
    tam = 120
    while ft(ANTON, tam).getlength(item["titulo_doc"]) > PW - 120 and tam > 60: tam -= 4
    fa = ft(ANTON, tam)
    d.text((60, 228), item["titulo_doc"], font=fa, fill=tinta)
    y = 228 + int(tam * 1.32)
    d.rectangle([60, y, PW - 60, y + 7], fill=verm); y += 44
    # corpo
    y = _texto_rico(d, 60, y, PW - 150, item["corpo"], 36, cor=tinta, cor_neg=(12, 10, 9))
    y += 22; d.line([(60, y), (PW - 120, y)], fill=cinza, width=2); y += 26
    for rot, val, destaque in item["campos"]:
        fr, fv = ft(INTER["400"], 36), ft(INTER["900"], 38)
        d.text((60, y), rot, font=fr, fill=tinta)
        d.text((60 + fr.getlength(rot + " "), y - 1), val, font=fv, fill=verm if destaque else tinta)
        y += 56
    y += 10; d.line([(60, y), (PW - 160, y)], fill=cinza, width=2); y += 22
    d.text((60, y), item.get("rodape_doc", "Agradecemos a compreensão."), font=ft(INTER["400"], 28), fill=(70, 64, 60))
    y_fim = y + 40
    # foto 3x4 (recorte no rosto: foco_3x4 = [x, y, zoom])
    fw, fh = 156, 200
    fx, fy = 60, PH - fh - 52
    src = Image.open(RAIZ.parent / item["foto_3x4"]).convert("RGB")
    cxr, cyr, zm = item.get("foco_3x4", [0.5, 0.4, 0.8])
    ch_ = int(src.height * zm); cw_ = int(ch_ * fw / fh)
    l = int(min(max(src.width * cxr - cw_ / 2, 0), src.width - cw_)); t = int(min(max(src.height * cyr - ch_ / 2, 0), src.height - ch_))
    ph = src.crop((l, t, l + cw_, t + ch_)).resize((fw, fh), Image.LANCZOS)
    ph = Image.blend(ph, Image.new("RGB", (fw, fh), (120, 100, 80)), 0.15)
    d.rectangle([fx - 8, fy - 8, fx + fw + 8, fy + fh + 8], fill=(250, 246, 238), outline=cinza, width=2)
    papel.paste(ph, (fx, fy))
    # assinatura cursiva com laços
    sx, sy = 270, PH - 128
    pts = []
    for k in range(140):
        t = k / 139
        pts.append((sx + 10 + t * 250 - 16 * math.sin(t * 30), sy - 34 + 20 * math.cos(t * 30) * (0.6 + 0.4 * math.sin(t * 5)) - 10 * t))
    d.line(pts, fill=(28, 40, 120), width=4, joint="curve")
    d.line([(sx + 40, sy - 8), (sx + 290, sy - 24)], fill=(28, 40, 120), width=3)
    d.line([(sx, sy + 8), (sx + 310, sy + 8)], fill=cinza, width=2)
    fs = ft(INTER["700"], 20)
    for k, l2 in enumerate(item.get("assinatura", ["JOGADOR", "EM MODO GTA VI"])):
        d.text((sx, sy + 20 + k * 30), "  ".join(l2), font=fs, fill=cinza)
    # selo da página no canto
    d.rounded_rectangle([PW - 175, PH - 175, PW - 60, PH - 60], 18, outline=(170, 162, 152), width=4)
    fng = ft(INTER["900"], 42)
    d.text((PW - 117.5 - fng.getlength("NG") / 2, PH - 142), "NG", font=fng, fill=(170, 162, 152))
    # carimbo: lado direito, logo abaixo do rodapé do texto
    ftc = ft(ANTON, 84)
    txt = item["carimbo"]
    cw = int(ftc.getlength(txt)) + 70; chh = 140
    car = Image.new("RGBA", (cw, chh), (0, 0, 0, 0)); dc = ImageDraw.Draw(car)
    dc.rounded_rectangle([4, 4, cw - 5, chh - 5], 14, outline=verm + (255,), width=8)
    dc.rounded_rectangle([18, 18, cw - 19, chh - 19], 8, outline=verm + (255,), width=3)
    dc.text((35, 12), txt, font=ftc, fill=verm + (255,))
    a = np.asarray(car).copy(); m = np.random.default_rng(3).random(a.shape[:2]) < 0.22
    a[..., 3] = np.where(m, (a[..., 3] * 0.35).astype(np.uint8), a[..., 3]); car = Image.fromarray(a, "RGBA").rotate(12, expand=True, resample=Image.BICUBIC)
    if car.width > PW - 300:
        car = car.resize((PW - 300, int(car.height * (PW - 300) / car.width)), Image.LANCZOS)
    cy = min(y_fim - 30, PH - 175 - car.height - 10)
    papel.alpha_composite(car, (PW - car.width - 50, max(cy, 0)))
    # papel na mesa
    rot = papel.rotate(item.get("giro", -1.6), expand=True, resample=Image.BICUBIC)
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ox, oy = (W - rot.width) // 2, 118
    sm = Image.new("RGBA", rot.size, (0, 0, 0, 170)); sm.putalpha(rot.getchannel("A").point(lambda v: 170 if v else 0))
    sombra.alpha_composite(sm, (ox + 14, oy + 22))
    fundo.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(18)))
    fundo.alpha_composite(rot, (ox, oy))
    moldura(fundo, tag=item.get("tag", "COMUNICADO"))
    arq = saida / f"{item['id']}.jpg"
    fundo.convert("RGB").save(arq, quality=91)
    return [arq]


def post(item, saida):
    if item.get("tipo") == "documento":
        return documento(item, saida)
    W, H = 1080, 1350
    if item.get("imagem"):
        img = _fundo_foto(RAIZ.parent / item["imagem"], W, H, item.get("escurecer", 0.62), item.get("foco", 0.5))
    else:
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
    y = 170 if item.get("imagem") else max(170, (int(H * 0.70) - total) // 2 + 40)
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


def carrossel_simples(item, saida):
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


# ───────────────────────── carrossel infinito (panorâmico) ─────────────────────────
def _panorama(N, W=1080, H=1350, seed=11):
    """Fundo contínuo de N slides: céu, skyline de Vice, sol na 1ª emenda, palmeiras nas emendas,
    mar com reflexo e uma linha de neon que atravessa tudo. Periódico: a borda direita do último
    slide encaixa na borda esquerda do primeiro."""
    PW = N * W
    rnd = random.Random(seed)
    hy = int(H * 0.80)
    ceu = _hex_lerp([(0, (12, 3, 22)), (0.45, (46, 10, 66)), (0.8, (150, 26, 100)), (1.0, (255, 104, 72))], hy)
    mar = _hex_lerp([(0, (66, 12, 66)), (0.4, (30, 7, 42)), (1, (9, 3, 15))], H - hy)
    col = np.concatenate([ceu, mar], 0).astype(np.uint8)
    img = Image.fromarray(np.repeat(col[:, None, :], PW, 1)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # estrelas
    for _ in range(int(PW * hy / 14000)):
        x, y = rnd.randrange(PW), rnd.randrange(int(hy * 0.5))
        b = rnd.randint(90, 210); d.point((x, y), fill=(b, b, b, 255))
    # sol listrado na emenda 1|2 (metade em cada slide)
    r = 330; sx, sy = W, hy - int(r * 0.35)
    tons = _hex_lerp([(0, C["amarelo"]), (0.55, C["laranja"]), (1, C["magenta"])], 2 * r)
    for yy in range(sy - r, min(sy + r, hy)):
        rel = (yy - sy) / r
        if rel > -0.15 and ((rel * 7) % 1.0) < min(0.55, (rel + 0.15) * 0.75):
            continue
        half = int(math.sqrt(max(0, r * r - (yy - sy) ** 2)))
        cor = tuple(int(v) for v in tons[min(2 * r - 1, max(0, yy - (sy - r)))])
        d.line([(sx - half, yy), (sx + half, yy)], fill=cor + (255,))
    # skyline periódico
    x = 0
    while x < PW:
        w = rnd.randint(50, 150)
        if x + w > PW - 40:
            w = PW - x
        h = rnd.randint(70, 300) if rnd.random() > 0.15 else rnd.randint(320, 430)
        d.rectangle([x, hy - h, x + w, hy], fill=(16, 5, 28, 255))
        for wy in range(hy - h + 14, hy - 10, 22):
            for wx in range(x + 8, x + w - 8, 18):
                if rnd.random() < 0.28:
                    c = rnd.choice([C["rosa"], C["ciano"], C["amarelo"]])
                    d.rectangle([wx, wy, wx + 6, wy + 9], fill=c + (rnd.randint(90, 200),))
        x += w
    # reflexo no mar
    for i in range(0, H - hy, 5):
        y = hy + i
        for k in range(N):
            if rnd.random() < 0.6:
                cx = k * W + rnd.randint(100, W - 100); ww = rnd.randint(40, 220) * (1 - i / (H - hy))
                d.line([(cx - ww, y), (cx + ww, y)], fill=C["rosa"] + (int(120 * (1 - i / (H - hy))),), width=2)
    # palmeiras nas emendas (metade em cada slide)
    pal = Image.new("RGBA", (PW, H), (0, 0, 0, 0))
    dp = ImageDraw.Draw(pal)
    for k in range(1, N + 1):
        bx = (k * W) % PW
        for desloc, alt, esc, sd in ((-60, 260, 1.0, k), (90, 120, 0.75, k + 50)):
            xb = bx + desloc
            _palmeira(dp, xb - 40, H + 40, xb + (60 if desloc > 0 else -60), hy - alt, esc, seed=sd)
            if xb < 400:  # parte que vaza pela esquerda reaparece no fim (loop)
                _palmeira(dp, xb - 40 + PW, H + 40, xb + PW + (60 if desloc > 0 else -60), hy - alt, esc, seed=sd)
    img.alpha_composite(pal)
    # véu escuro em cima para leitura
    veu = np.zeros((H, 1, 4), np.uint8)
    topo = int(H * 0.66)
    veu[:topo, 0, 3] = (175 * (1 - np.linspace(0, 1, topo) ** 1.5)).astype(np.uint8)
    veu[:, 0, :3] = (8, 2, 14)
    img.alpha_composite(Image.fromarray(np.repeat(veu, PW, 1), "RGBA"))
    # linha de neon contínua (período = 1 slide, então fecha o loop)
    ly = lambda xx: int(H * 0.72 + 26 * math.sin(2 * math.pi * xx / W))
    pts = [(xx, ly(xx)) for xx in range(0, PW + 1, 6)]
    glow = Image.new("RGBA", (PW, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).line(pts, fill=C["magenta"] + (255,), width=22)
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(glow)
    ImageDraw.Draw(img).line(pts, fill=(255, 220, 240, 255), width=5)
    # grão leve
    g = np.random.default_rng(seed).normal(0, 5, (H // 2, 540)).astype(np.float32)
    tile = Image.fromarray(np.clip(128 + g, 0, 255).astype(np.uint8)).resize((1080, H))
    grao = Image.new("RGBA", (PW, H))
    for k in range(N):
        grao.paste(Image.merge("RGBA", (tile, tile, tile, Image.new("L", (1080, H), 18))), (k * W, 0))
    img.alpha_composite(grao)
    return img, ly


# ───────────────────────── panorâmico com fotos reais (banco licenciado) ─────────────────────────
BANCO = RAIZ / "banco" / "fotos"
FORA_DO_BANCO = {"carro-posto-noite"}  # marca em destaque
TEMAS = {
    "miami": ["miami", "ocean", "hotel", "rua"],
    "policia": ["policia"],
    "carro": ["carro", "moto"],
    "jacare": ["jacare"],
    "ceu": ["helicoptero", "miami-aerea", "miami-sunset"],
    "noite": ["motel", "ocean", "hotel", "moto"],
    "luxo": ["iate", "carro-lambo", "miami-roda"],
    "gamer": ["controle", "gamer", "maos"],
}


def _fotos(temas, seed):
    if temas and all(str(t).endswith(".jpg") for t in temas):  # lista explícita (ex.: banco/oficial), na ordem
        return [RAIZ.parent / t for t in temas]
    todas = sorted(p for p in BANCO.glob("*.jpg") if p.stem not in FORA_DO_BANCO)
    if temas:
        pref = tuple(x for t in temas for x in TEMAS.get(t, [t]))
        esc = [p for p in todas if p.stem.startswith(pref)]
        todas = esc + [p for p in todas if p not in esc]
    rnd = random.Random(seed)
    cab = todas[: max(4, len(todas) // 3)] if temas else todas[:]
    rnd.shuffle(cab)
    resto = [p for p in todas if p not in cab]
    rnd.shuffle(resto)
    return cab + resto


def _cobrir(im, w, h):
    r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))


def _panorama_fotos(N, temas=None, W=1080, H=1350, seed=11):
    PW = N * W
    fotos = _fotos(temas, seed)
    passo = int(W * 1.45)
    inclina = 110
    seams = list(range(-int(W * 0.35), PW + passo, passo))
    pano = Image.new("RGB", (PW, H))
    for i in range(len(seams) - 1):
        a, b = seams[i], seams[i + 1]
        x0 = max(0, a - inclina)
        x1 = min(PW, b + inclina)
        foto = Image.open(fotos[i % len(fotos)]).convert("RGB")
        bloco = _cobrir(foto, x1 - x0, H)
        mask = Image.new("L", (x1 - x0, H), 0)
        ImageDraw.Draw(mask).polygon([(a + inclina - x0, 0), (b + inclina - x0, 0), (b - inclina - x0, H), (a - inclina - x0, H)], fill=255)
        pano.paste(bloco, (x0, 0), mask)
    # tratamento único (todas as fotos parecem do mesmo "filme"): contraste, cor e tom Vice
    arr = np.asarray(pano).astype(np.float32)
    arr = (arr - 128) * 1.12 + 128
    cinza = arr.mean(axis=2, keepdims=True)
    arr = cinza + (arr - cinza) * 1.18
    grad = np.linspace(0, 1, H)[:, None, None]
    tint = (1 - grad) * np.array([110, 40, 190]) + grad * np.array([255, 70, 140])
    arr = arr * 0.72 + (arr * tint / 255 * 1.45) * 0.28
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    # emendas em neon
    glow = Image.new("RGBA", (PW, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for x in seams[1:-1]:
        gd.line([(x + inclina, 0), (x - inclina, H)], fill=C["magenta"] + (255,), width=16)
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)
    for x in seams[1:-1]:
        d.line([(x + inclina, 0), (x - inclina, H)], fill=(255, 220, 240, 255), width=3)
    # véu para leitura (topo escuro) e base escura
    veu = np.zeros((H, 1, 4), np.uint8)
    topo = int(H * 0.68)
    veu[:topo, 0, 3] = (205 * (1 - np.linspace(0, 1, topo) ** 1.7)).astype(np.uint8)
    base = H - int(H * 0.82)
    veu[H - base:, 0, 3] = (150 * np.linspace(0, 1, base) ** 1.4).astype(np.uint8)
    veu[:, 0, :3] = (8, 2, 14)
    img.alpha_composite(Image.fromarray(np.repeat(veu, PW, 1), "RGBA"))
    # linha de neon contínua
    ly = lambda xx: int(H * 0.74 + 24 * math.sin(2 * math.pi * xx / W))
    pts = [(xx, ly(xx)) for xx in range(0, PW + 1, 6)]
    g2 = Image.new("RGBA", (PW, H), (0, 0, 0, 0))
    ImageDraw.Draw(g2).line(pts, fill=C["magenta"] + (255,), width=20)
    img.alpha_composite(g2.filter(ImageFilter.GaussianBlur(12)))
    ImageDraw.Draw(img).line(pts, fill=(255, 220, 240, 255), width=5)
    return img, ly


def _grade(n, x0, y0, x1, y1, gap=12):
    """Caixas da tela dividida para n painéis (1 a 6)."""
    w, h = x1 - x0, y1 - y0
    if n == 1:
        return [(x0, y0, x1, y1)]
    if n == 2:
        m = y0 + h // 2
        return [(x0, y0, x1, m - gap // 2), (x0, m + gap // 2, x1, y1)]
    if n == 3:
        m = y0 + int(h * 0.52); c = x0 + w // 2
        return [(x0, y0, x1, m - gap // 2), (x0, m + gap // 2, c - gap // 2, y1), (c + gap // 2, m + gap // 2, x1, y1)]
    cols = 2
    rows = (n + 1) // 2
    ch = (h - gap * (rows - 1)) // rows; cw = (w - gap) // 2
    caixas = []
    for i in range(n):
        r, c = divmod(i, cols)
        if n % 2 and i == n - 1:  # último sozinho ocupa a linha inteira
            caixas.append((x0, y0 + r * (ch + gap), x1, y0 + r * (ch + gap) + ch))
        else:
            caixas.append((x0 + c * (cw + gap), y0 + r * (ch + gap), x0 + c * (cw + gap) + cw, y0 + r * (ch + gap) + ch))
    return caixas


def _painel(img, caixa, foto, rot="", txt="", foco=0.5):
    x0, y0, x1, y1 = caixa
    w, h = x1 - x0, y1 - y0
    src = Image.open(RAIZ.parent / foto).convert("RGB")
    r = max(w / src.width, h / src.height)
    src = src.resize((int(src.width * r) + 1, int(src.height * r) + 1), Image.LANCZOS)
    l = int((src.width - w) * foco); t = (src.height - h) // 2
    ph = src.crop((l, t, l + w, t + h)).convert("RGBA")
    veu = np.zeros((h, 1, 4), np.uint8); veu[..., :3] = (8, 2, 14)
    ini = int(h * 0.35)
    veu[ini:, 0, 3] = (235 * np.linspace(0, 1, h - ini) ** 1.2).astype(np.uint8)
    ph.alpha_composite(Image.fromarray(np.repeat(veu, w, 1), "RGBA"))
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 22, fill=255)
    ph.putalpha(m)
    img.alpha_composite(ph, (x0, y0))
    ImageDraw.Draw(img).rounded_rectangle([x0, y0, x1 - 1, y1 - 1], 22, outline=C["magenta"] + (200,), width=3)
    pad = 24 if w > 600 else 18
    tr = max(30, min(52, int(h * 0.12), int(w * 0.075)))
    tt = max(22, min(32, int(w * 0.05)))
    blocos = []
    if rot:
        blocos.append(bloco_texto(rot, w - 2 * pad, tr, "900", cor=C["amarelo"], alinhar="left", espaco=1.12, caixa=False))
    if txt:
        blocos.append(bloco_texto(txt, w - 2 * pad, tt, "700", alinhar="left", espaco=1.25, caixa=False))
    y = y1 - pad - sum(b.height for b in blocos) - 6 * (len(blocos) - 1)
    for b in blocos:
        colar(img, b, x0 + pad, y); y += b.height + 6


def carrossel_grade(item, saida):
    """Carrossel 'tela dividida': cada slide junta 2 a 6 imagens oficiais com informação em cada painel."""
    W, H = 1080, 1350
    slides = item["slides"]
    fecho = item.get("fecho")
    N = 1 + len(slides) + (1 if fecho else 0)
    if N > 10:
        raise SystemExit(f"carrossel {item['id']} com {N} imagens (máx. 10)")
    arqs = []

    def base():
        im = Image.new("RGBA", (W, H), (11, 4, 16, 255))
        g = np.linspace(0, 1, H)[:, None]
        cor = (np.array([40, 8, 60]) * (1 - g) + np.array([11, 4, 16]) * g)
        im.alpha_composite(Image.fromarray(np.repeat(np.concatenate([cor, np.full((H, 1), 255)], 1)[:, None, :], W, 1).astype(np.uint8), "RGBA"))
        return im

    def salva(im, k, puxa=None):
        if puxa:
            p = pilula(puxa.upper() + "  >>", 28, pad=(26, 14))
            colar(im, p, W - 64 - p.width, H - 150)
        moldura(im, contador=f"{k:02d}/{N:02d}", link=(k == N))
        arqs.append(saida / f"{item['id']}_{k:02d}.jpg")
        im.convert("RGB").save(arqs[-1], quality=90)

    # capa: título + mosaico
    capa = item["capa"]
    im = base()
    t = bloco_titulo(capa["titulo"], W - 120, tam=150, altura_max=330, destaque=capa.get("destaque", [1]))
    colar(im, t, (W - t.width) / 2, 120)
    y = 120 + t.height + 14
    if capa.get("sub"):
        sb = bloco_texto(capa["sub"], W - 160, 34, "700")
        colar(im, sb, (W - sb.width) / 2, y); y += sb.height + 18
    for cx, f in zip(_grade(len(capa["fotos"]), 48, y, W - 48, H - 175), capa["fotos"]):
        _painel(im, cx, f)
    salva(im, 1, item.get("puxa_capa", "Arrasta"))
    # slides
    for i, sl in enumerate(slides, start=2):
        im = base()
        t = bloco_titulo([sl["titulo"]], W - 140, tam=110, tam_min=60, altura_max=140, destaque=[0], alinhar="left")
        colar(im, t, 60, 128)
        y = 128 + t.height + 22
        for cx, pn in zip(_grade(len(sl["paineis"]), 48, y, W - 48, H - 175), sl["paineis"]):
            _painel(im, cx, pn["foto"], pn.get("rot", ""), pn.get("txt", ""), pn.get("foco", 0.5))
        salva(im, i, sl.get("puxa"))
    # fecho
    if fecho:
        im = _fundo_foto(RAIZ.parent / fecho["foto"], W, H, 0.85) if fecho.get("foto") else base()
        im.alpha_composite(Image.new("RGBA", (W, H), (8, 2, 14, 110)))
        ft_ = bloco_titulo(fecho["titulo"], W - 150, tam=170, destaque=[len(fecho["titulo"]) - 1])
        colar(im, ft_, (W - ft_.width) / 2, 300)
        tx = bloco_texto(fecho["texto"], W - 200, 42, "700")
        colar(im, tx, (W - tx.width) / 2, 300 + ft_.height + 30)
        cta = pilula("GRUPO VIP + OFERTAS: LINK NA BIO", 32, pad=(34, 20))
        colar(im, cta, (W - cta.width) / 2, 300 + ft_.height + 70 + tx.height)
        salva(im, N)
    return arqs


def carrossel(item, saida):
    if item.get("estilo") == "grade":
        return carrossel_grade(item, saida)
    W, H = 1080, 1350
    slides = item["slides"]
    com_fecho = len(slides) + 2 <= 10
    N = len(slides) + (2 if com_fecho else 1)
    if N > 10:
        raise SystemExit(f"carrossel {item['id']} com {N} slides (máx. 10)")
    semente = sum(map(ord, item["id"] + item.get("capa", [""])[0]))
    if BANCO.exists() and any(BANCO.glob("*.jpg")):
        pano, ly = _panorama_fotos(N, item.get("fotos"), W, H, seed=semente)
    else:
        pano, ly = _panorama(N, W, H, seed=semente)
    d = ImageDraw.Draw(pano)
    # marcadores numerados na linha de neon, em cima das emendas (metade aparece antes de arrastar)
    for k in range(1, N):
        cx, cy = k * W, ly(k * W)
        d.ellipse([cx - 58, cy - 58, cx + 58, cy + 58], fill=(12, 4, 20, 255), outline=C["amarelo"] + (255,), width=6)
        rot = f"{k:02d}" if k <= len(slides) else "+"
        nb = bloco_titulo([rot], 100, tam=64, sombra=False)
        colar(pano, nb, cx - nb.width / 2, cy - nb.height / 2 + 4)
    # capa
    tit = bloco_titulo(item["capa"], W - 150, tam=175, altura_max=560, destaque=item.get("destaque", []), alinhar="left")
    y = 180
    colar(pano, tit, 64, y); y += tit.height + 20
    if item.get("sub"):
        sb = bloco_texto(item["sub"], W - 220, 42, "700", alinhar="left")
        colar(pano, sb, 52, y); y += sb.height
    seta = pilula(item.get("puxa_capa", "ARRASTA  >>"), 30, fundo=(255, 255, 255), cor=(12, 4, 20), pad=(30, 18))
    colar(pano, seta, W - seta.width - 28, ly(W) - 210)
    # miolo
    for i, s in enumerate(slides, start=1):
        x0 = i * W
        num = bloco_titulo([f"{i:02d}"], 300, tam=140, destaque=[0], alinhar="left")
        tt = bloco_titulo(quebra_titulo(s["titulo"]), W - 150, tam=104, tam_min=54, altura_max=330, alinhar="left")
        yy = 170
        colar(pano, num, x0 + 64, yy); yy += num.height
        colar(pano, tt, x0 + 58, yy); yy += tt.height + 18
        if s.get("texto"):
            cp = bloco_texto(s["texto"], W - 230, 42, "700", alinhar="left")
            colar(pano, cp, x0 + 46, yy); yy += cp.height
        if s.get("puxa") and (i < len(slides) or com_fecho):
            pp = pilula(s["puxa"].upper() + "  >>", 26, pad=(26, 16))
            colar(pano, pp, (i + 1) * W - pp.width - 28, ly((i + 1) * W) - 210)
    # fecho
    if com_fecho:
        x0 = (N - 1) * W
        fecho = item.get("fecho", {"titulo": ["SALVA", "ESSE POST"], "texto": "E manda pro parça que vai jogar com você."})
        ft_ = bloco_titulo(fecho["titulo"], W - 150, tam=160, destaque=[len(fecho["titulo"]) - 1], alinhar="left")
        colar(pano, ft_, x0 + 64, 200)
        tx = bloco_texto(fecho["texto"], W - 230, 42, "700", alinhar="left")
        colar(pano, tx, x0 + 52, 200 + ft_.height + 20)
        cta = pilula("GRUPO VIP + OFERTAS: LINK NA BIO", 28, pad=(30, 18))
        colar(pano, cta, x0 + 64, 200 + ft_.height + 40 + tx.height)
    arqs = []
    for k in range(N):
        sl = pano.crop((k * W, 0, (k + 1) * W, H))
        moldura(sl, contador=f"{k + 1:02d}/{N:02d}", link=False)
        arqs.append(saida / f"{item['id']}_{k + 1:02d}.jpg")
        sl.convert("RGB").save(arqs[-1], quality=90)
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
    if item.get("roteiro"):
        import narrado
        item["_pauta"] = saida.name
        return narrado.reel_narrado(item, saida, sys.modules[__name__])
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
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest",
                            *SEM_METADADOS, "-movflags", "+faststart", str(arq)],
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
CTA_BIO = {
    "grupo": "🔗 Quer as ofertas de PS5, Xbox e acessórios antes de todo mundo? Entra no Grupo VIP grátis pelo link na bio.",
    "guia": "🔗 O guia do GTA 6 em PT-BR está quase pronto. Garante seu lugar na lista de espera pelo link na bio.",
    "ofertas": "🔗 Vai montar o setup pro dia 19? As melhores ofertas estão no link na bio.",
    "comunidade": "🔗 Quer trocar ideia com quem vai jogar no Brasil? A comunidade Nerd GTA está no link na bio.",
}


# arquivos limpos: sem tags de encoder, sem SEI do x264, sem datas
SEM_METADADOS = ["-map_metadata", "-1", "-map_chapters", "-1", "-fflags", "+bitexact", "-flags:v", "+bitexact",
                 "-flags:a", "+bitexact", "-bsf:v", "filter_units=remove_types=6", "-metadata", "encoder=", "-metadata:s", "handler_name="]


def legenda(item, n=0):
    corpo = item["legenda"].strip()
    chave = item.get("cta_bio") or ["grupo", "guia", "ofertas", "comunidade"][n % 4]
    return f"{corpo}\n\n{CTA_BIO[chave]}\n\n{CFG['rodape_legenda']}\n{CFG['hashtags']}"


def story(entrada, saida):
    """Versão 9:16 de cada peça para os stories. Reel: o próprio vídeo. Post/carrossel: a capa sobre fundo desfocado."""
    if entrada["formato"] == "reel":
        return entrada["arquivos"][0]
    from PIL import ImageFilter
    W, H = 1080, 1920
    src = Image.open(RAIZ.parent / entrada["arquivos"][0]).convert("RGB")
    fundo = _cobrir(src, W, H).filter(ImageFilter.GaussianBlur(38))
    fundo = Image.blend(fundo, Image.new("RGB", (W, H), (8, 2, 14)), 0.45).convert("RGBA")
    cw = 900; ch = int(src.height * cw / src.width)
    card = src.resize((cw, ch), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, cw - 1, ch - 1], 36, fill=255)
    card.putalpha(m)
    y = (H - ch) // 2 + 40
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle([(W - cw) // 2, y + 24, (W + cw) // 2, y + ch + 24], 36, fill=(0, 0, 0, 150))
    fundo.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(26)))
    fundo.alpha_composite(card, ((W - cw) // 2, y))
    rot = "CARROSSEL NOVO  >>" if entrada["formato"] == "carrossel" else "POST NOVO"
    pl = pilula(rot, 38)
    colar(fundo, pl, (W - pl.width) / 2, y - pl.height - 34)
    dr = ImageDraw.Draw(fundo)
    f = ft(INTER["900"], 38)
    dr.text(((W - f.getlength(CFG["handle"])) / 2, 120), CFG["handle"], font=f, fill=(255, 255, 255, 235))
    c = pilula("LINK NA BIO", 34, fundo=(255, 255, 255), cor=(12, 4, 20), pad=(34, 20))
    colar(fundo, c, (W - c.width) / 2, min(H - 200, y + ch + 60))
    arq = saida / f'{entrada["id"].split("-")[-1]}_story.jpg'
    fundo.convert("RGB").save(arq, quality=90)
    return str(arq.relative_to(RAIZ.parent))


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
        hora = item.get("hora") or horas[n % len(horas)]
        dia_pub = data
        if hora.startswith("24:"):  # meia-noite do fim do dia → 00:MM do dia seguinte
            dia_pub = (datetime.date.fromisoformat(data) + datetime.timedelta(days=1)).isoformat()
            hora = "00:" + hora[3:]
        entrada = {"id": f"{data}-{item['id']}", "pauta": data, "data": dia_pub, "hora": hora,
                   "formato": fmt, "titulo": item.get("titulo_doc") or " ".join(item.get("linhas") or (item["capa"]["titulo"] if isinstance(item.get("capa"), dict) else item.get("capa"))),
                   "arquivos": [r for r in rel if not r.endswith("_capa.jpg")],
                   "legenda": legenda(item, n)}
        if fmt == "reel":
            entrada["capa"] = [r for r in rel if r.endswith("_capa.jpg")][0]
            entrada["thumb_offset_ms"] = item["_thumb_ms"]
        entrada["story"] = story(entrada, saida)
        cal = [c for c in cal if c["id"] != entrada["id"]] + [entrada]
        print("ok", entrada["id"], fmt, entrada["hora"], len(entrada["arquivos"]), "arquivo(s)", flush=True)
    cal.sort(key=lambda c: (c["data"], c["hora"]))
    json.dump(cal, open(cal_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
