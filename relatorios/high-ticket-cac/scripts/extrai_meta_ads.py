"""Extrai spend Meta a NIVEL DE ANUNCIO nas janelas das 9 campanhas.

Por que separado do extrai_meta_api.py: aquele varre 3 anos inteiros no nivel de campanha
(barato). Este desce ao anuncio, que multiplica o volume por ~20x, entao roda so dentro das
janelas das campanhas. E o que responde "qtd. de ads" da lista original do pedido, e habilita
CAC e ticket por criativo.

⚠️ A Travessia (abr-mai/2023) fica de fora: a Marketing API guarda 37 meses (desde 17/08/2023).

Uso: python scripts/extrai_meta_ads.py [--out dados/meta_ads_diario.csv]
"""
import argparse
import csv
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from extrai_meta_api import API, carrega_token, contas, get, puxa  # reuso da camada robusta
import urllib.parse

JANELAS = [
    ("TRA",   date(2023, 4, 1),  date(2023, 5, 31)),
    ("TRA2",  date(2024, 4, 1),  date(2024, 5, 31)),
    ("BNO24", date(2024, 11, 1), date(2024, 11, 30)),
    ("BIT",   date(2025, 4, 9),  date(2025, 5, 31)),
    ("BNO25", date(2025, 11, 1), date(2025, 11, 30)),
    ("DBI",   date(2026, 2, 4),  date(2026, 3, 31)),
    ("CDL",   date(2026, 5, 5),  date(2026, 6, 30)),
    ("BP10",  date(2026, 6, 11), date(2026, 9, 15)),
    ("ODI",   date(2026, 7, 17), date(2026, 9, 16)),
]

COLUNAS = ["sigla", "dt", "id_conta", "nm_conta", "id_campanha", "nm_campanha",
           "id_anuncio", "nm_anuncio", "vl_spend", "qt_impressoes", "qt_cliques"]

# O limite de 37 meses e movel; calculado na hora para nao chumbar data.
LIMITE_API = date.today().replace(year=date.today().year - 3)


def puxa_ads(conta, ini, fim, token):
    """Mesma logica de puxa(), mas level=ad e sem time_increment (agregado na janela).

    Sem quebra diaria: para contar anuncios e medir CAC por criativo o que importa e o
    total da janela, e o payload cai ~30x.
    """
    p = {"level": "ad", "time_range": json.dumps({"since": ini.isoformat(), "until": fim.isoformat()}),
         "fields": "campaign_id,campaign_name,ad_id,ad_name,spend,impressions,clicks",
         "limit": "500", "access_token": token}
    url = f"{API}/{conta}/insights?" + urllib.parse.urlencode(p)
    linhas = []
    while url:
        d = get(url)
        if d is None:
            return None
        linhas.extend(d.get("data", []))
        url = d.get("paging", {}).get("next")
    return linhas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dados/meta_ads_diario.csv")
    args = ap.parse_args()

    token = carrega_token()
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    trava = threading.Lock()
    todas = contas(token)

    with open(args.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUNAS)

        def varre(conta):
            id_conta, nm_conta = conta
            for sigla, ini, fim in JANELAS:
                if fim < LIMITE_API:
                    continue  # fora do alcance da API (Travessia 2023)
                linhas = puxa_ads(id_conta, ini, fim, token)
                if linhas is None:
                    print(f"    !! falhou {nm_conta[:24]} {sigla}", flush=True)
                    continue
                uteis = [r for r in linhas if float(r.get("spend", 0) or 0) > 0]
                with trava:
                    for r in uteis:
                        w.writerow([sigla, ini.isoformat(), id_conta, nm_conta,
                                    r.get("campaign_id"), r.get("campaign_name"),
                                    r.get("ad_id"), r.get("ad_name"),
                                    r.get("spend"), r.get("impressions"), r.get("clicks")])
                    fh.flush()
                    print(f"{nm_conta[:30]:32s} {sigla:6s} {len(uteis):6d} anuncios com verba", flush=True)

        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(varre, todas))


if __name__ == "__main__":
    main()
