"""Reel narrado: voz (ElevenLabs, arquivos em gta6/narracao/<pauta>-<id>/NN.mp3), imagens oficiais com movimento,
texto grande por cena, legenda da fala, barra de progresso, cortes com flash e cartão final de link na bio."""
import pathlib, subprocess, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw


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


def reel_narrado(item, saida, g):
    W, H, FPS, SR = 1080, 1920, g.FPS, g.SR
    pasta = g.RAIZ / "narracao" / f'{item["_pauta"]}-{item["id"]}'
    cenas = item["roteiro"]
    vozes = [_audio(pasta / f"{k + 1:02d}.mp3", SR) for k in range(len(cenas))]
    PAD, FIM = 0.22, 1.7
    t0, durs = [], []
    acc = 0.12
    for v in vozes:
        t0.append(acc); d = len(v) / SR + PAD; durs.append(d); acc += d
    t_fim = acc; total = t_fim + FIM
    # áudio: voz + trilha baixa + passagem nos cortes
    n = int(total * SR)
    voz = np.zeros(n, np.float32)
    for v, t in zip(vozes, t0):
        i = int(t * SR); voz[i:i + len(v)] += v[: n - i]
    eventos = [(t, "passagem") for t in t0[1:]] + [(t_fim, "impacto")]
    mus = g.trilha(total, bpm=112, seed=len(item["id"]) + 5, eventos=eventos)[:, 0][:n]
    # abaixa a música quando há voz (ducking simples)
    envv = np.convolve(np.abs(voz), np.ones(2400) / 2400, "same")
    duck = np.where(envv > 0.01, 0.16, 0.42)
    duck = np.convolve(duck, np.ones(4800) / 4800, "same")
    mix = voz * 1.0 + mus * duck
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
    tmp = pathlib.Path(tempfile.mkdtemp())
    wav = tmp / "a.wav"
    a = (np.stack([mix, mix], 1) * 32767).astype(np.int16)
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.tobytes())
    # camadas fixas por cena
    veu = np.zeros((H, 1, 4), np.uint8); veu[..., :3] = (8, 2, 14)
    yy = np.linspace(0, 1, H)
    veu[:, 0, 3] = (np.clip((yy - 0.45) / 0.55, 0, 1) ** 1.1 * 225 + np.clip((0.18 - yy) / 0.18, 0, 1) * 150 + 35).clip(0, 255).astype(np.uint8)
    veu = Image.fromarray(np.repeat(veu, W, 1), "RGBA")
    bases, titulos, legendas = [], [], []
    for k, c in enumerate(cenas):
        src = Image.open(g.RAIZ.parent / c["imagem"]).convert("RGB")
        r = max(W * 1.22 / src.width, H * 1.22 / src.height)
        bases.append(src.resize((int(src.width * r) + 2, int(src.height * r) + 2), Image.BILINEAR))
        titulos.append(g.bloco_titulo(_linhas(c["tela"]), W - 110, tam=150, tam_min=70, altura_max=430, destaque=[len(_linhas(c["tela"])) - 1]))
        legendas.append(g.bloco_texto(c["fala"], W - 170, 44, "700", caixa=True))
    cta = g.bloco_titulo(item.get("cta", ["LINK", "NA BIO"]), W - 140, tam=190, destaque=[len(item.get("cta", ["LINK", "NA BIO"])) - 1])
    cta_sub = g.bloco_texto(item.get("cta_sub", "Grupo VIP de ofertas, landing e guia do GTA 6"), W - 200, 46, "700")
    fh = g.ft(g.INTER["900"], 40)
    arq = saida / f"{item['id']}.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-maxrate", "6M", "-bufsize", "12M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", *g.SEM_METADADOS, "-movflags", "+faststart", str(arq)],
                           stdin=subprocess.PIPE)
    capa = None
    nf = int(total * FPS)
    for f in range(nf):
        t = f / FPS
        k = max(i for i in range(len(cenas)) if t >= t0[i] or i == 0) if t < t_fim else len(cenas) - 1
        lt = (t - t0[k]) / durs[k] if t < t_fim else 1.0
        b = bases[k]
        # movimento: alterna zoom-in, zoom-out e panorâmica
        modo = k % 3
        if modo == 0: s = 1.0 - 0.16 * lt; px, py = 0.5, 0.45
        elif modo == 1: s = 0.84 + 0.16 * lt; px, py = 0.5, 0.5
        else: s = 0.88; px, py = 0.3 + 0.4 * lt, 0.5
        if t >= t_fim:
            s = 0.84 - 0.04 * min(1, (t - t_fim) / FIM)
        cw, ch = int(b.width * 0.82 * s), int(b.height * 0.82 * s)
        x = int((b.width - cw) * px); y = int((b.height - ch) * py)
        img = b.crop((x, y, x + cw, y + ch)).resize((W, H), Image.BILINEAR).convert("RGBA")
        img.alpha_composite(veu)
        if t < t_fim:
            ti = titulos[k]
            kk = min(1, (t - t0[k]) / 0.22) if k > 0 or t > 0.05 else 1
            e = 1 - (1 - max(kk, 0)) ** 3
            sc = 1.25 - 0.25 * e
            tb = ti.resize((max(1, int(ti.width * sc)), max(1, int(ti.height * sc))))
            ytit = int(H * 0.30 - ti.height / 2)
            g.colar(img, tb, (W - tb.width) / 2, ytit + (ti.height - tb.height) / 2, alpha=min(1, 0.35 + kk))
            lg = legendas[k]
            ka = min(1, max(0, (t - t0[k] - 0.1) / 0.2))
            g.colar(img, lg, (W - lg.width) / 2, H - 470 - lg.height / 2 + 20 * (1 - ka), alpha=ka)
            if k > 0 and t - t0[k] < 0.1:
                img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(150 * (1 - (t - t0[k]) / 0.1)))))
        else:
            img.alpha_composite(Image.new("RGBA", (W, H), (8, 2, 14, 120)))
            kk = min(1, (t - t_fim) / 0.25)
            sc = 1.2 - 0.2 * (1 - (1 - kk) ** 3)
            cb = cta.resize((int(cta.width * sc), int(cta.height * sc)))
            yc = int(H * 0.36 - cta.height / 2)
            g.colar(img, cb, (W - cb.width) / 2, yc + (cta.height - cb.height) / 2, alpha=min(1, kk * 1.6))
            g.colar(img, cta_sub, (W - cta_sub.width) / 2, yc + cta.height + 40, alpha=min(1, max(0, (t - t_fim - 0.2) / 0.3)))
        d = ImageDraw.Draw(img)
        d.text((60, 90), g.CFG["handle"], font=fh, fill=(255, 255, 255, 235))
        d.rectangle([0, 0, int(W * min(1, t / total)), 10], fill=g.C["magenta"] + (255,))
        rgb = img.convert("RGB")
        if capa is None and t >= 0.5:
            capa = rgb
        enc.stdin.write(rgb.tobytes())
    enc.stdin.close(); enc.wait()
    capa_arq = saida / f"{item['id']}_capa.jpg"
    capa.save(capa_arq, quality=88)
    item["_thumb_ms"] = 500
    return [arq, capa_arq]
