"""Roda no workbench (tem acesso ao Pexels): baixa as fotos do plano, gera os 300 slides e as prévias.
Uso: build.run(fonte_display, pasta_saida, so=None)"""
import os, io, json, requests, concurrent.futures as cf
from PIL import Image
import render

UA = {"User-Agent": "Mozilla/5.0"}


def baixar(pid, cache):
    path = os.path.join(cache, f"{pid}.jpg")
    if os.path.exists(path) and os.path.getsize(path) > 20000:
        return pid, path
    u = f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=1600"
    try:
        r = requests.get(u, timeout=60, headers=UA)
        if r.status_code != 200 or len(r.content) < 20000:
            return pid, None
        Image.open(io.BytesIO(r.content)).verify()
        open(path, "wb").write(r.content)
        return pid, path
    except Exception:
        return pid, None


def baixar_todas(plano, cache):
    os.makedirs(cache, exist_ok=True)
    ids = sorted({p for c in plano for p in c["fotos"]})
    with cf.ThreadPoolExecutor(12) as ex:
        res = dict(ex.map(lambda p: baixar(p, cache), ids))
    return {p: v for p, v in res.items() if v}, [p for p, v in res.items() if not v]


def run(plano, fonte_disp, fonte_body, fonte_meta, saida, cache, disp_lh=1.02, so=None):
    F = render.fonts(fonte_disp, fonte_body, fonte_meta, disp_lh)
    ok, falhas = baixar_todas(plano, cache)
    gerados = []
    for c in plano:
        if so and c["id"] not in so:
            continue
        pasta = os.path.join(saida, c["id"]); os.makedirs(pasta, exist_ok=True)
        imgs = []
        cap = render.render_cover(Image.open(ok[c["fotos"][0]]), c["capa"], F, 10)
        imgs.append(cap)
        for i, (head, body) in enumerate(c["slides_texto"], start=2):
            imgs.append(render.render_slide(Image.open(ok[c["fotos"][i - 1]]), head, body, i, 10, F))
        for i, im in enumerate(imgs, start=1):
            im.save(os.path.join(pasta, f"{i:02d}.jpg"), quality=88, optimize=True, progressive=True)
        sheet = Image.new("RGB", (5 * 432, 2 * 540))
        for i, im in enumerate(imgs):
            sheet.paste(im.resize((432, 540)), ((i % 5) * 432, (i // 5) * 540))
        os.makedirs(os.path.join(saida, "previa"), exist_ok=True)
        sheet.save(os.path.join(saida, "previa", f"{c['id']}.jpg"), quality=82)
        gerados.append(c["id"])
    return gerados, falhas
