#!/usr/bin/env python3
"""Próximos horários de Reel ainda vazios (hoje e amanhã), para a fábrica de Reels.
Saída: {"agora", "slots": [{"data","hora","id"}...], "stories_livres": {data: n}, "recentes": [títulos], "proxima_serie"}"""
import datetime, json, pathlib, sys, zoneinfo

RAIZ = pathlib.Path(__file__).resolve().parents[2]
CFG = json.loads((RAIZ / "gta6/fabrica/config.json").read_text(encoding="utf-8"))
R = CFG["reels"]
cal = json.loads((RAIZ / "gta6/calendario.json").read_text(encoding="utf-8"))
BR = zoneinfo.ZoneInfo("America/Sao_Paulo")
agora = datetime.datetime.now(BR)
margem = agora + datetime.timedelta(minutes=int(sys.argv[1]) if len(sys.argv) > 1 else 45)
ocupado = {(c["data"], c["hora"][:5]) for c in cal}
# horários da fábrica diária (posts/carrosséis/série) ficam reservados mesmo antes de o dia ser gerado
reservado = set(CFG["horarios"]) | {CFG["serie"]["hora_normal"]}
livres = []
for dd in range(0, 3):
    d = (agora.date() + datetime.timedelta(days=dd)).isoformat()
    if d < R["de"]:
        continue
    for h in R["slots"]:
        quando = datetime.datetime.fromisoformat(f"{d}T{h}:00").replace(tzinfo=BR)
        if quando < margem or (d, h) in ocupado or h in reservado:
            continue
        livres.append({"data": d, "hora": h, "id": "R" + h.replace(":", "")})
livres = livres[: R["por_execucao"]]
stories = {}
for dd in range(0, 3):
    d = (agora.date() + datetime.timedelta(days=dd)).isoformat()
    do_dia = [c for c in cal if c["data"] == d]
    feed = len(do_dia) + sum(1 for s in livres if s["data"] == d)
    st = sum(1 for c in do_dia if c.get("story") and c.get("postar_story", True))
    stories[d] = max(0, min(R["stories_max_dia"], R["limite_api_24h"] - feed) - st)
recentes = [f'{c["data"]} {c["hora"]} {c["formato"]}: {c["titulo"]}' for c in cal if c["data"] >= (agora.date() - datetime.timedelta(days=2)).isoformat()]
print(json.dumps({"agora": agora.strftime("%Y-%m-%d %H:%M"), "slots": livres, "stories_livres": stories, "recentes": recentes[-60:]}, ensure_ascii=False, indent=1))
