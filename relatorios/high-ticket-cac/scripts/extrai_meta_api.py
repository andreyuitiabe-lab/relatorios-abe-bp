"""Extrai spend Meta por campanha x dia x conta via Marketing API.

A Marketing API guarda 37 meses (em set/2026: desde 2023-08-17), o que cobre todas as
campanhas high-ticket da analise menos a Travessia original (abr-mai/2023). O warehouse
so tem spend Meta desde ago/2025 -- esta e a unica fonte granular para ago/2023 -> jul/2025.

Robustez: a API devolve "Service temporarily unavailable" (code 2 / subcode 1504044) em
janelas pesadas. O script retenta e, se insistir, parte a janela ao meio recursivamente
ate 1 dia. Retoma de onde parou: relê o CSV existente e pula conta x mes ja extraidos.

Uso: python scripts/extrai_meta_api.py [--desde YYYY-MM-DD] [--out dados/meta_spend_diario.csv]
"""
import argparse
import csv
import threading
from concurrent.futures import ThreadPoolExecutor
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

API = "https://graph.facebook.com/v21.0"
ENV = os.path.expanduser("~/meu_projeto/BigQuery/meta_api/.env")
# reach/frequency sao agregacoes caras na API (chegavam a ~1 min por conta x mes) e nao
# entram em nenhuma metrica desta analise -- ficam de fora de proposito.
CAMPOS = "campaign_id,campaign_name,objective,spend,impressions,clicks,actions"
COLUNAS = ["dt", "id_conta", "nm_conta", "id_campanha", "nm_campanha", "nm_objetivo",
           "vl_spend", "qt_impressoes", "qt_cliques", "qt_leads", "qt_compras"]


def carrega_token():
    with open(ENV) as fh:
        for linha in fh:
            if linha.startswith("META_ACCESS_TOKEN"):
                return linha.split("=", 1)[1].strip().strip('"')
    sys.exit("META_ACCESS_TOKEN nao encontrado em " + ENV)


def get(url, tentativas=4):
    """GET com retry. Devolve None se o erro for transitorio e persistir."""
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            corpo = e.read().decode()
            transitorio = ('"code":2' in corpo or '"code":1' in corpo
                           or "limit" in corpo.lower() or e.code >= 500)
            if transitorio and i < tentativas - 1:
                time.sleep(15 * (i + 1))
                continue
            if transitorio:
                return None
            raise RuntimeError(f"{e.code}: {corpo[:300]}")
        except Exception:
            if i == tentativas - 1:
                return None
            time.sleep(10 * (i + 1))
    return None


def puxa(conta, ini, fim, token, prof=0):
    """Insights campanha x dia no periodo. Parte a janela ao meio se a API recusar."""
    p = {"level": "campaign", "time_increment": "1",
         "time_range": json.dumps({"since": ini.isoformat(), "until": fim.isoformat()}),
         "fields": CAMPOS, "limit": "500", "access_token": token}
    url = f"{API}/{conta}/insights?" + urllib.parse.urlencode(p)
    linhas, ok = [], True
    while url:
        d = get(url)
        if d is None:
            ok = False
            break
        linhas.extend(d.get("data", []))
        url = d.get("paging", {}).get("next")
    if ok:
        return linhas
    if ini == fim or prof > 6:
        print(f"    !! desisti de {conta} {ini}..{fim}", flush=True)
        return []
    meio = ini + (fim - ini) // 2
    return (puxa(conta, ini, meio, token, prof + 1)
            + puxa(conta, meio + timedelta(days=1), fim, token, prof + 1))


def contas(token):
    url = f"{API}/me/adaccounts?" + urllib.parse.urlencode(
        {"fields": "id,name", "limit": 200, "access_token": token})
    return [(a["id"], a["name"]) for a in get(url)["data"]]


def meses(desde, ate):
    cur = date(desde.year, desde.month, 1)
    while cur <= ate:
        fim = date(cur.year + (cur.month == 12), cur.month % 12 + 1, 1) - timedelta(days=1)
        yield max(cur, desde), min(fim, ate)
        cur = fim + timedelta(days=1)


def ja_feitos(caminho):
    """(id_conta, YYYY-MM) ja presentes no CSV, para retomar sem refazer."""
    feitos = set()
    if not os.path.exists(caminho):
        return feitos
    with open(caminho) as fh:
        for linha in csv.DictReader(fh):
            feitos.add((linha["id_conta"], linha["dt"][:7]))
    return feitos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2023-08-17")
    ap.add_argument("--ate", default=date.today().isoformat())
    ap.add_argument("--out", default="dados/meta_spend_diario.csv")
    ap.add_argument("--checkpoint", default="dados/meta_checkpoint.csv",
                    help="conta;mes ja varridos (inclusive os vazios)")
    args = ap.parse_args()

    token = carrega_token()
    desde, ate = date.fromisoformat(args.desde), date.fromisoformat(args.ate)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    vistos = ja_feitos(args.out)
    if os.path.exists(args.checkpoint):
        with open(args.checkpoint) as fh:
            vistos |= {tuple(l.strip().split(";")) for l in fh if l.strip()}

    novo = not os.path.exists(args.out) or os.path.getsize(args.out) == 0
    trava = threading.Lock()
    janelas = list(meses(desde, ate))

    with open(args.out, "a", newline="") as fh, open(args.checkpoint, "a") as ck:
        w = csv.writer(fh)
        if novo:
            w.writerow(COLUNAS)

        def varre_conta(conta):
            id_conta, nm_conta = conta
            for ini, fim in janelas:
                if (id_conta, f"{ini:%Y-%m}") in vistos:
                    continue
                linhas = puxa(id_conta, ini, fim, token)
                with trava:
                    for r in linhas:
                        acoes = {a["action_type"]: a["value"] for a in r.get("actions", [])}
                        w.writerow([
                            r["date_start"], id_conta, nm_conta,
                            r.get("campaign_id"), r.get("campaign_name"), r.get("objective"),
                            r.get("spend"), r.get("impressions"), r.get("clicks"),
                            acoes.get("lead"), acoes.get("purchase"),
                        ])
                    fh.flush()
                    ck.write(f"{id_conta};{ini:%Y-%m}\n")
                    ck.flush()
                    print(f"{nm_conta[:32]:34s} {ini:%Y-%m} {len(linhas):6d} linhas", flush=True)

        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(varre_conta, contas(token)))


if __name__ == "__main__":
    main()
