#!/usr/bin/env python3
"""Agenda no TikTok (via Postiz) os Reels do calendário que ainda não foram agendados.
Roda no GitHub Actions com o segredo POSTIZ_API_KEY. Estado em gta6/tiktok/agendados.json."""
import datetime, json, os, pathlib, re, subprocess, sys, zoneinfo

RAIZ = pathlib.Path(__file__).resolve().parents[2]
CAL = RAIZ / "gta6/calendario.json"
EST = RAIZ / "gta6/tiktok/agendados.json"
BR = zoneinfo.ZoneInfo("America/Sao_Paulo")


def cli(*args):
    r = subprocess.run(["postiz", *args], capture_output=True, text=True)
    saida = r.stdout.strip()
    m = re.search(r"[\[{]", saida)
    if r.returncode != 0 or not m:
        raise RuntimeError(f"postiz {' '.join(args[:2])}: {r.stderr.strip() or saida}")
    return json.loads(saida[m.start():])


def legenda_tiktok(leg):
    corpo = leg.split("\n\nPágina de fã")[0].strip()
    return (corpo + "\n\n#GTA6 #GTAVI #GTA6Brasil #NerdGTA #fyp")[:2150]


def main():
    tk = [i for i in cli("integrations:list") if (i.get("identifier") or "").startswith("tiktok")]
    if not tk:
        sys.exit("Nenhum TikTok conectado no Postiz.")
    tid = tk[0]["id"]
    regras = cli("integrations:settings", tid)
    print("Regras do TikTok no Postiz:", json.dumps(regras.get("output", regras), ensure_ascii=False)[:1500])
    feito = json.loads(EST.read_text()) if EST.exists() else {}
    agora = datetime.datetime.now(BR)
    novos = 0
    for c in json.loads(CAL.read_text(encoding="utf-8")):
        if c["formato"] != "reel" or c["id"] in feito:
            continue
        quando = datetime.datetime.fromisoformat(f'{c["data"]}T{c["hora"]}:00').replace(tzinfo=BR)
        if quando < agora + datetime.timedelta(minutes=10):
            continue
        video = cli("upload", str(RAIZ / c["arquivos"][0]))["path"]
        cfg = {"privacy_level": "PUBLIC_TO_EVERYONE", "duet": True, "stitch": True, "comment": True,
               "content_posting_method": "DIRECT_POST", "autoAddMusic": "no", "brand_content_toggle": False, "brand_organic_toggle": False}
        r = cli("posts:create", "-c", legenda_tiktok(c["legenda"]), "-m", video,
                "-s", quando.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "--settings", json.dumps(cfg), "-i", tid)
        feito[c["id"]] = {"quando": quando.isoformat(), "postiz": r}
        novos += 1
        print("agendado", c["id"], quando.isoformat())
        EST.write_text(json.dumps(feito, ensure_ascii=False, indent=1))
    print(f"{novos} Reel(s) novo(s) agendado(s) no TikTok.")


if __name__ == "__main__":
    main()
