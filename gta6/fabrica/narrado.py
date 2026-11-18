"""Reel narrado v2: voz (gta6/narracao/<pauta>-<id>/NN.mp3) + linha do tempo de cenas com camadas e efeitos:
fundo desfocado em parallax, imagem principal com Ken Burns, zoom-punch e whip nos cortes, tremida de câmera,
RGB split (glitch), light leak, grão e vinheta, título com pop, legenda palavra por palavra (karaokê),
barra de progresso, marcadores de cena e cartão final de link na bio."""
import pathlib, subprocess, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def _audio(mp3, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def _linhas(txt, maxc=13):
    pal, lin, cur = txt.split(), [], ""
    for p in pal:
        if cur and len(cur) + 1 + len(p) > maxc:
            lin.append(cur); cur = p
        else:
            cur = (cur + " " + p).strip()
    if cur: lin.append(cur)
    return lin


def _fala_ativa(v, sr):
    """início e fim reais da voz dentro do mp3 (corta silêncio)."""
    e = np.convolve(np.abs(v), np.ones(441) / 441, "same")
    idx = np.where(e > 0.02)[0]
    if len(idx) == 0: return 0.15, len(v) / sr - 0.2
    return idx[0] / sr, idx[-1] / sr


class Karaoke:
    """Legenda palavra por palavra: 3 a 4 palavras por vez, palavra atual em amarelo."""
    def __init__(self, g, texto, t_ini, t_fim, W, peso="900", tam=74, acento=None, caixa=False):
        self.g, self.W = g, W
        self.acento, self.caixa = acento or g.C["amarelo"], caixa
        self.pal = texto.split()
        pesos = np.array([len(p) + 2 for p in self.pal], float)
        cum = np.concatenate([[0], np.cumsum(pesos)]) / pesos.sum()
        self.t = t_ini + cum * (t_fim - t_ini)
        self.f = g.ft(g.INTER[peso], tam)
        self.grupos, gr, larg = [], [], 0
        for i, p in enumerate(self.pal):
            w = self.f.getlength(p + " ")
            if gr and (larg + w > W - 160 or len(gr) == 4):
                self.grupos.append(gr); gr, larg = [], 0
            gr.append(i); larg += w
        if gr: self.grupos.append(gr)

    def desenha(self, img, t, y):
        atual = int(np.searchsorted(self.t, t, side="right") - 1)
        atual = max(0, min(atual, len(self.pal) - 1))
        gr = next(g_ for g_ in self.grupos if atual in g_)
        txt = [self.pal[i] for i in gr]
        larg = sum(self.f.getlength(p + " ") for p in txt) - self.f.getlength(" ")
        x = (self.W - larg) / 2
        d = ImageDraw.Draw(img)
        if self.caixa:
            hh = self.f.getbbox("ÁGjp")
            d.rounded_rectangle([x - 28, y + hh[1] - 18, x + larg + 28, y + hh[3] + 18], 18, fill=(0, 0, 0, 200))
        for i, p in zip(gr, txt):
            cor = self.acento if i == atual else (255, 255, 255)
            dy = -10 * max(0, 1 - (t - self.t[i]) / 0.12) if i == atual else 0
            for ox, oy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, 3), (-3, 3), (3, -3)):
                d.text((x + ox, y + oy + dy), p, font=self.f, fill=(10, 4, 16, 255))
            d.text((x, y + dy), p, font=self.f, fill=cor + (255,))
            x += self.f.getlength(p + " ")


# ───────────── estilos visuais (para o feed não ficar com tudo igual) ─────────────
ESTILOS = ["neon", "manchete", "cinema", "tweet", "impacto"]
EST = {
    "neon":     dict(acento="amarelo", barra="magenta", sombra=(8, 2, 14), leak=(70, 25, 60), grade=None, kfonte=("900", 74), kcaixa=False),
    "manchete": dict(acento=(255, 214, 0), barra=(225, 29, 46), sombra=(0, 0, 0), leak=None, grade="frio", kfonte=("900", 70), kcaixa=True),
    "cinema":   dict(acento="ciano", barra="laranja", sombra=(0, 0, 0), leak=(80, 45, 10), grade="filme", kfonte=("700", 62), kcaixa=False),
    "tweet":    dict(acento=(29, 155, 240), barra=(29, 155, 240), sombra=(0, 0, 0), leak=None, grade=None, kfonte=("900", 70), kcaixa=True),
    "impacto":  dict(acento=(170, 255, 60), barra=(170, 255, 60), sombra=(0, 0, 0), leak=(30, 60, 0), grade="contraste", kfonte=("900", 78), kcaixa=False),
}


def escolher_estilo(item):
    """Estilo fixo se a pauta mandar ("estilo"); senão gira pela meia hora, então dois Reels seguidos nunca ficam iguais."""
    e = item.get("estilo")
    if e in ESTILOS:
        return e
    h = item.get("hora") or "00:00"
    try:
        n = int(h[:2]) * 2 + int(h[3:5]) // 30
    except ValueError:
        n = sum(map(ord, item.get("id", "")))
    return ESTILOS[n % len(ESTILOS)]


def _cor(g, c):
    return g.C[c] if isinstance(c, str) else c


def _fit(g, fonte, linhas, larg, tam, tam_min=60):
    while tam > tam_min and max(g.ft(fonte, tam).getlength(l) for l in linhas) > larg:
        tam = int(tam * 0.94)
    return g.ft(fonte, tam), tam


def _titulo_manchete(g, texto, W, rotulo):
    lin = [l.upper() for l in _linhas(texto, 16)]
    f, tam = _fit(g, g.INTER["900"], lin, W - 220, 96, 54)
    lh = int(tam * 1.08); pad = 34
    larg = int(max(f.getlength(l) for l in lin)) + 2 * pad
    pl = g.pilula(rotulo, 30, fundo=(12, 12, 12), pad=(22, 12))
    img = Image.new("RGBA", (max(larg, pl.width) + 12, pl.height + 14 + lh * len(lin) + 2 * pad), (0, 0, 0, 0))
    img.alpha_composite(pl, (0, 0))
    d = ImageDraw.Draw(img); y0 = pl.height + 14
    d.rectangle([0, y0, larg, img.height - 1], fill=(225, 29, 46, 255))
    d.rectangle([0, y0, 12, img.height - 1], fill=(255, 214, 0, 255))
    for i, l in enumerate(lin):
        d.text((pad + 8, y0 + pad + i * lh - f.getbbox("H")[1] // 2), l, font=f, fill=(255, 255, 255, 255))
    return img


def _titulo_cinema(g, texto, W):
    lin = [l.upper() for l in _linhas(texto, 20)][:2]
    f, tam = _fit(g, g.ANTON, lin, W - 140, 130, 60)
    lh = int(tam * 1.12)
    img = Image.new("RGBA", (W, lh * len(lin) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, l in enumerate(lin):
        x = (W - f.getlength(l)) / 2
        d.text((x, i * lh), l, font=f, fill=(245, 240, 230, 255) if i < len(lin) - 1 else _cor(g, "ciano") + (255,))
    return img


def _titulo_tweet(g, texto, W):
    cw = W - 100; pad = 48
    fn, fu, ft_ = g.ft(g.INTER["900"], 42), g.ft(g.INTER["400"], 32), g.ft(g.INTER["900"], 84)
    t = texto[:1].upper() + texto[1:].lower() if texto.isupper() else texto
    lin = g.quebra(t, ft_, cw - 2 * pad)
    lh = 100
    h = pad + 96 + 26 + lh * len(lin) + pad
    img = Image.new("RGBA", (cw, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, cw - 1, h - 1], 36, fill=(255, 255, 255, 250))
    d.ellipse([pad, pad, pad + 96, pad + 96], fill=g.C["magenta"] + (255,))
    fa = g.ft(g.INTER["900"], 38); d.text((pad + 48 - fa.getlength("NG") / 2, pad + 26), "NG", font=fa, fill=(255, 255, 255, 255))
    d.text((pad + 120, pad + 8), "Nerd GTA", font=fn, fill=(15, 20, 25, 255))
    nx = pad + 120 + fn.getlength("Nerd GTA") + 12
    d.ellipse([nx, pad + 16, nx + 30, pad + 46], fill=(29, 155, 240, 255))
    d.line([(nx + 8, pad + 31), (nx + 13, pad + 37), (nx + 23, pad + 24)], fill=(255, 255, 255, 255), width=4)
    d.text((pad + 120, pad + 56), g.CFG["handle"], font=fu, fill=(83, 100, 113, 255))
    for i, l in enumerate(lin):
        d.text((pad, pad + 96 + 26 + i * lh), l, font=ft_, fill=(15, 20, 25, 255))
    return img


def _titulo_impacto(g, texto, W, acento):
    lin = [l.upper() for l in _linhas(texto, 9)][:3]
    f, tam = _fit(g, g.ANTON, lin, W - 120, 260, 90)
    lh = int(tam * 1.02); sw = max(5, tam // 24)
    img = Image.new("RGBA", (W, lh * len(lin) + 2 * sw + int(tam * 0.6)), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, l in enumerate(lin):
        x = (W - f.getlength(l)) / 2
        d.text((x, i * lh + sw), l, font=f, fill=(acento if i == len(lin) - 1 else (255, 255, 255)) + (255,), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
    return img.rotate(-4, expand=True, resample=Image.BICUBIC)


def _gradear(arr, modo):
    if modo == "frio":
        m = arr.mean(-1, keepdims=True); arr = arr * 0.72 + m * 0.28
        arr[..., 2] += 8; arr[..., 0] -= 4
    elif modo == "filme":
        lum = arr.mean(-1, keepdims=True) / 255
        arr = arr + (1 - lum) * np.array([-14, 6, 16]) + lum * np.array([18, 6, -12])
    elif modo == "contraste":
        arr = (arr - 128) * 1.18 + 128
    return arr


def reel_narrado(item, saida, g):
    W, H, FPS, SR = 1080, 1920, g.FPS, g.SR
    pasta = g.RAIZ / "narracao" / f'{item["_pauta"]}-{item["id"]}'
    cenas = item["roteiro"]
    def _voz(k):
        mp3 = pasta / f"{k + 1:02d}.mp3"
        if mp3.exists():
            return _audio(mp3, SR)
        d = max(2.2, min(4.5, 0.075 * len(cenas[k]["fala"]) + 0.9))  # sem voz: tempo de leitura
        return np.zeros(int(d * SR), np.float32)
    vozes = [_voz(k) for k in range(len(cenas))]
    sem_voz = all(not (pasta / f"{k + 1:02d}.mp3").exists() for k in range(len(cenas)))
    PAD, FIM = 0.12, 1.6
    t0, durs, falas = [], [], []
    acc = 0.05
    for v in vozes:
        a, b = _fala_ativa(v, SR)
        t0.append(acc); d = len(v) / SR + PAD; durs.append(d); falas.append((acc + a, acc + b)); acc += d
    t_fim = acc; total = t_fim + FIM
    estilo = escolher_estilo(item); E = EST[estilo]; item["_estilo"] = estilo
    acento, barra = _cor(g, E["acento"]), _cor(g, E["barra"])
    rotulo = (item.get("tag") or "GTA 6").upper()
    if rotulo in ("GTA 6", "GTA VI"): rotulo = "AGORA"
    rng = np.random.default_rng(sum(map(ord, item["id"] + item["_pauta"])))
    # ── áudio: voz + trilha com ducking + passagem/impacto nos cortes
    n = int(total * SR)
    voz = np.zeros(n, np.float32)
    for v, t in zip(vozes, t0):
        i = int(t * SR); voz[i:i + len(v)] += v[: n - i]
    eventos = [(t, "passagem") for t in t0[1:]] + [(t_fim, "impacto")]
    mus = g.trilha(total, bpm=118, seed=len(item["id"]) + 7, eventos=eventos)[:, 0][:n]
    envv = np.convolve(np.abs(voz), np.ones(2400) / 2400, "same")
    duck = np.convolve(np.where(envv > 0.01, 0.15, 0.45), np.ones(4800) / 4800, "same")
    if sem_voz:
        duck = np.full(n, 0.9, np.float32)
    mix = voz + mus * duck
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
    tmp = pathlib.Path(tempfile.mkdtemp()); wav = tmp / "a.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes())
    # ── camadas fixas
    yy = np.linspace(0, 1, H)[:, None]; xx = np.linspace(-1, 1, W)[None, :]
    vin = np.clip(1.08 - 0.32 * (xx ** 2 + ((yy - 0.5) * 2) ** 2) ** 1.6, 0.6, 1.08)[..., None]
    grad = np.zeros((H, 1, 4), np.uint8); grad[..., :3] = E["sombra"]
    grad[:, 0, 3] = (np.clip((yy[:, 0] - 0.55) / 0.45, 0, 1) ** 1.4 * 190 + np.clip((0.16 - yy[:, 0]) / 0.16, 0, 1) * 140).astype(np.uint8)
    grad = Image.fromarray(np.repeat(grad, W, 1), "RGBA")
    bases, fundos, titulos, karas = [], [], [], []
    for k, c in enumerate(cenas):
        src = Image.open(g.RAIZ.parent / c["imagem"]).convert("RGB")
        r = max(W * 1.3 / src.width, H * 1.3 / src.height)
        bases.append(src.resize((int(src.width * r) + 2, int(src.height * r) + 2), Image.BILINEAR))
        rf = max(W * 1.2 / src.width, H * 1.2 / src.height)
        fb = src.resize((int(src.width * rf) + 2, int(src.height * rf) + 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(28))
        fundos.append(Image.blend(fb, Image.new("RGB", fb.size, (20, 6, 30)), 0.25))
        if estilo == "manchete":
            titulos.append(_titulo_manchete(g, c["tela"], W, rotulo))
        elif estilo == "cinema":
            titulos.append(_titulo_cinema(g, c["tela"], W))
        elif estilo == "tweet":
            titulos.append(_titulo_tweet(g, c["tela"], W))
        elif estilo == "impacto":
            titulos.append(_titulo_impacto(g, c["tela"], W, acento))
        else:
            lin = _linhas(c["tela"])
            titulos.append(g.bloco_titulo(lin, W - 120, tam=150, tam_min=70, altura_max=420, destaque=[len(lin) - 1]))
        karas.append(Karaoke(g, c["fala"], falas[k][0], falas[k][1], W, E["kfonte"][0], E["kfonte"][1], acento, E["kcaixa"]))
    cta_l = item.get("cta", ["LINK", "NA BIO"])
    cta = g.bloco_titulo(cta_l, W - 140, tam=190, destaque=[len(cta_l) - 1]) if estilo == "neon" else _titulo_impacto(g, " ".join(cta_l), W, acento)
    cta_sub = g.bloco_texto(item.get("cta_sub", "Grupo VIP, ofertas e o guia do GTA 6"), W - 200, 46, "700")
    fh = g.ft(g.INTER["900"], 38); fm = g.ft(g.INTER["900"], 26)
    arq = saida / f"{item['id']}.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "25", "-maxrate", "5M", "-bufsize", "10M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", *g.SEM_METADADOS, "-movflags", "+faststart", str(arq)],
                           stdin=subprocess.PIPE)
    graos = [(rng.normal(0, 9, (H // 2, W // 2)).astype(np.int16)) for _ in range(6)]
    capa = None
    for f in range(int(total * FPS)):
        t = f / FPS
        fim = t >= t_fim
        k = len(cenas) - 1 if fim else max(i for i in range(len(cenas)) if t >= t0[i] or i == 0)
        lt = min(1, (t - t0[k]) / durs[k]) if not fim else 1.0
        dc = max(0.0, t - t0[k])  # tempo desde o corte
        # camada 1: fundo desfocado (parallax lento)
        fb = fundos[k]
        ox = int((fb.width - W) * (0.5 + 0.25 * np.sin(t * 0.6))); oy = int((fb.height - H) * 0.5)
        img = fb.crop((ox, oy, ox + W, oy + H)).convert("RGBA")
        # camada 2: imagem principal com Ken Burns + zoom-punch no corte + tremida
        b = bases[k]
        modo = k % 3
        s = (1.0 - 0.14 * lt) if modo == 0 else (0.86 + 0.14 * lt) if modo == 1 else 0.9
        punch = 0.10 * max(0, 1 - dc / 0.28) ** 2 if k > 0 and not fim else 0
        s = s * (1 - punch)
        if fim: s = 0.82 - 0.05 * min(1, (t - t_fim) / FIM)
        px = 0.5 if modo != 2 else 0.25 + 0.5 * lt
        cw, ch = int(W / 1.3 * (b.width / W) * s * 1.0), 0
        cw = int(b.width * 0.77 * s); ch = int(b.height * 0.77 * s)
        sh = 14 * max(0, 1 - dc / 0.3) if k > 0 else 0
        jx, jy = (rng.normal(0, sh), rng.normal(0, sh)) if sh else (0, 0)
        x = int(np.clip((b.width - cw) * px + jx, 0, b.width - cw)); y = int(np.clip((b.height - ch) * 0.45 + jy, 0, b.height - ch))
        prin = b.crop((x, y, x + cw, y + ch)).resize((W, H), Image.BILINEAR)
        # entrada da cena: a imagem principal “abre” sobre o fundo (máscara que cresce)
        abre = min(1, dc / 0.22) if k > 0 and not fim else 1
        if abre < 1:
            m = Image.new("L", (W, H), 0); e = 1 - (1 - abre) ** 3
            mw, mh = int(W * (0.55 + 0.45 * e)), int(H * (0.55 + 0.45 * e))
            ImageDraw.Draw(m).rounded_rectangle([(W - mw) // 2, (H - mh) // 2, (W + mw) // 2, (H + mh) // 2], int(60 * (1 - e)), fill=255)
            img.paste(prin, (0, 0), m)
        else:
            img = prin.convert("RGBA")
        # whip blur nos primeiros quadros do corte
        if k > 0 and dc < 0.1 and not fim:
            arr = np.asarray(img).astype(np.float32)
            acc_ = sum(np.roll(arr, int(dx), axis=1) for dx in np.linspace(-60, 60, 7)) / 7
            img = Image.fromarray(acc_.astype(np.uint8), "RGBA")
        img.alpha_composite(grad)
        # light leak que atravessa a tela
        arr = np.asarray(img.convert("RGB")).astype(np.int16)
        cx = (t * 0.35 + k * 0.37) % 1.6 - 0.3
        if E["leak"]:
            leak = np.exp(-(((xx - (cx * 2 - 1)) / 0.55) ** 2 + ((yy - 0.25) / 0.35) ** 2))[..., None]
            arr = arr + (leak * np.array(E["leak"])).astype(np.int16)
        if E["grade"]:
            arr = _gradear(arr.astype(np.float32), E["grade"]).astype(np.int16)
        arr = (arr * vin).astype(np.int16)
        # grão
        gr = graos[f % len(graos)]
        arr += np.repeat(np.repeat(gr, 2, 0), 2, 1)[..., None]
        # RGB split no corte
        if k > 0 and dc < 0.12 and not fim:
            off = int(18 * (1 - dc / 0.12))
            arr[..., 0] = np.roll(arr[..., 0], off, 1); arr[..., 2] = np.roll(arr[..., 2], -off, 1)
        img = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
        if not fim:
            # título com pop + leve balanço
            ti = titulos[k]
            kk = min(1, dc / 0.24) if (k > 0 or t > 0.03) else 1
            e = 1 - (1 - kk) ** 3
            sc = 1.3 - 0.3 * e + 0.015 * np.sin(t * 3.2)
            tb = ti.resize((max(1, int(ti.width * sc)), max(1, int(ti.height * sc))))
            if dc < 0.5: tb = tb.rotate(4 * (1 - e) * (-1) ** k, expand=True, resample=Image.BICUBIC)
            d = ImageDraw.Draw(img)
            ykar = H - 560
            if estilo == "cinema":
                d.rectangle([0, 0, W, 210], fill=(0, 0, 0, 255)); d.rectangle([0, H - 340, W, H], fill=(0, 0, 0, 255))
                ytit = H - 340 + (340 - ti.height) // 2 + 6; ykar = H - 520
                g.colar(img, ti, 0, ytit, alpha=min(1, dc / 0.35) if k > 0 or t > 0.03 else 1)
            elif estilo == "manchete":
                xs = int(-ti.width * (1 - e))
                g.colar(img, ti, 60 + xs, int(H * 0.60 - ti.height), alpha=1)
            elif estilo == "tweet":
                yt = 230 + int(60 * (1 - e))
                g.colar(img, ti, (W - ti.width) / 2, yt, alpha=min(1, 0.2 + kk))
            elif estilo == "impacto":
                g.colar(img, tb, (W - tb.width) / 2, int(H * 0.30 - tb.height / 2), alpha=min(1, 0.3 + kk))
            else:
                ytit = int(H * 0.27 - ti.height / 2)
                g.colar(img, tb, (W - tb.width) / 2, ytit + (ti.height - tb.height) / 2, alpha=min(1, 0.3 + kk))
                bw = int((W - 300) * min(1, dc / 0.4))
                d.rectangle([(W - bw) // 2, ytit + ti.height + 24, (W + bw) // 2, ytit + ti.height + 34], fill=barra + (255,))
            # legenda karaokê
            if falas[k][0] - 0.05 <= t <= falas[k][1] + 0.3:
                karas[k].desenha(img, t, ykar)
        else:
            img.alpha_composite(Image.new("RGBA", (W, H), (8, 2, 14, 130)))
            kk = min(1, (t - t_fim) / 0.25)
            sc = 1.25 - 0.25 * (1 - (1 - kk) ** 3)
            cb = cta.resize((int(cta.width * sc), int(cta.height * sc)))
            yc = int(H * 0.36 - cta.height / 2)
            g.colar(img, cb, (W - cb.width) / 2, yc + (cta.height - cb.height) / 2, alpha=min(1, kk * 1.6))
            g.colar(img, cta_sub, (W - cta_sub.width) / 2, yc + cta.height + 40, alpha=min(1, max(0, (t - t_fim - 0.2) / 0.3)))
        # HUD: @, marcadores de cena e barra de progresso
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, int(W * min(1, t / total)), 12], fill=barra + (255,))
        if estilo != "tweet":
            d.text((60, 70), g.CFG["handle"], font=fh, fill=(255, 255, 255, 240))
        for i in range(len(cenas)):
            cx_ = W - 60 - (len(cenas) - 1 - i) * 34
            d.ellipse([cx_ - 9, 86, cx_ + 9, 104], fill=(acento if i == k and not fim else (255, 255, 255)) + ((255,) if i <= k else (90,)))
        if item.get("tag") and not fim and estilo in ("neon", "impacto"):
            p = g.pilula(item["tag"], 26, fundo=barra if estilo == "impacto" else None, cor=(0, 0, 0) if estilo == "impacto" else (255, 255, 255), pad=(20, 10))
            g.colar(img, p, 60, 128)
        rgb = img.convert("RGB")
        if capa is None and t >= 0.45:
            capa = rgb
        enc.stdin.write(rgb.tobytes())
    enc.stdin.close(); enc.wait()
    g.limpar_video(arq)
    capa_arq = saida / f"{item['id']}_capa.jpg"
    capa.save(capa_arq, quality=88)
    item["_thumb_ms"] = 450
    return [arq, capa_arq]
