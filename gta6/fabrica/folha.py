#!/usr/bin/env python3
"""Folha de conferência de um dia: 1ª imagem de cada peça (capa do Reel, capa do carrossel, post).
uso: python3 gta6/fabrica/folha.py AAAA-MM-DD saida.jpg"""
import json, pathlib, sys
from PIL import Image, ImageDraw

RAIZ = pathlib.Path(__file__).resolve().parents[1]
data, saida = sys.argv[1], sys.argv[2]
cal = [c for c in json.load(open(RAIZ / "calendario.json", encoding="utf-8")) if c["data"] == data]
thumbs = []
for c in cal:
    p = c.get("capa") or c["arquivos"][0]
    im = Image.open(RAIZ.parent / p).convert("RGB")
    im = im.resize((int(im.width * 480 / im.height), 480))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, 26], fill=(0, 0, 0))
    d.text((6, 6), f'{c["hora"]} {c["formato"]} ({len(c["arquivos"])})', fill=(255, 255, 0))
    thumbs.append(im)
cols = 5
W = max(t.width for t in thumbs) if thumbs else 1
rows = (len(thumbs) + cols - 1) // cols
folha = Image.new("RGB", (cols * (W + 8), rows * 488), (60, 60, 60))
for i, t in enumerate(thumbs):
    folha.paste(t, ((i % cols) * (W + 8), (i // cols) * 488))
folha.save(saida, quality=85)
print(len(thumbs), "peças")
