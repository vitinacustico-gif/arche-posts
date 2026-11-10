#!/usr/bin/env python3
"""Diz qual data a fábrica deve gerar agora e lista os títulos recentes (para não repetir).
uso: python3 gta6/fabrica/status.py   → imprime JSON {"hoje", "gerar", "faltam_dias", "recentes"}"""
import datetime, json, pathlib, zoneinfo

RAIZ = pathlib.Path(__file__).resolve().parents[1]
CFG = json.load(open(RAIZ / "fabrica/config.json", encoding="utf-8"))
hoje = datetime.datetime.now(zoneinfo.ZoneInfo("America/Sao_Paulo")).date()
cal_p = RAIZ / "calendario.json"
cal = json.load(open(cal_p, encoding="utf-8")) if cal_p.exists() else []
por_dia = {}
for c in cal:
    por_dia[c["data"]] = por_dia.get(c["data"], 0) + 1
gerar = None
for k in range(1, 4):  # mantém até 3 dias prontos à frente
    d = (hoje + datetime.timedelta(days=k)).isoformat()
    if por_dia.get(d, 0) < 10:
        gerar = d
        break
lanc = datetime.date.fromisoformat(CFG["lancamento"])
alvo = datetime.date.fromisoformat(gerar) if gerar else None
recentes = [f'{c["data"]} {c["formato"]}: {c["titulo"]}' for c in cal if c["data"] >= (hoje - datetime.timedelta(days=7)).isoformat()]
print(json.dumps({"hoje": hoje.isoformat(), "gerar": gerar,
                  "faltam_dias_no_dia_gerado": (lanc - alvo).days if alvo else None,
                  "dias_prontos": {d: n for d, n in sorted(por_dia.items()) if d >= hoje.isoformat()},
                  "recentes": recentes}, ensure_ascii=False, indent=1))
