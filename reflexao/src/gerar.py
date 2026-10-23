"""Gera os slides localmente a partir do plano.json e das fotos já baixadas (branch fotos-reflexao).
Uso: python3 gerar.py <pasta_fotos> <fonte_display> <pasta_saida> [ids...]"""
import os, sys, json
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import render

INTER_B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
INTER_M = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"


def main(fotos, fonte, saida, so=None, lh=1.02):
    plano = json.load(open(os.path.join(os.path.dirname(__file__), "plano.json")))
    F = render.fonts(fonte, INTER_B, INTER_M, lh)
    os.makedirs(os.path.join(saida, "previa"), exist_ok=True)
    for c in plano:
        if so and c["id"] not in so:
            continue
        ph = [Image.open(os.path.join(fotos, f"{p}.jpg")) for p in c["fotos"]]
        imgs = [render.render_cover(ph[0], c["capa"], F, 10)]
        for i, (head, body) in enumerate(c["slides_texto"], start=2):
            imgs.append(render.render_slide(ph[i - 1], head, body, i, 10, F))
        pasta = os.path.join(saida, c["id"]); os.makedirs(pasta, exist_ok=True)
        for i, im in enumerate(imgs, start=1):
            im.save(os.path.join(pasta, f"{i:02d}.jpg"), quality=88, optimize=True, progressive=True)
        sheet = Image.new("RGB", (5 * 432, 2 * 540))
        for i, im in enumerate(imgs):
            sheet.paste(im.resize((432, 540)), ((i % 5) * 432, (i // 5) * 540))
        sheet.save(os.path.join(saida, "previa", f"{c['id']}.jpg"), quality=82)
        print("ok", c["id"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], set(sys.argv[4:]) or None, float(os.environ.get('LH', '1.02')))
