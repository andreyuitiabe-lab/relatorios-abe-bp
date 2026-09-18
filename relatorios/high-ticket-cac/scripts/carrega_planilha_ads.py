"""Carrega a aba de anuncios da planilha historica do time de trafego no BigQuery.

A planilha `04.2 Midia Paga - Anuncios FACEBOOK` tem nivel de ANUNCIO desde 01/06/2022 —
cobertura que nenhuma outra fonte tem (o warehouse so tem nome de anuncio confiavel desde
mar/2025; a Marketing API alcanca 37 meses e o token caiu em 18/09/2026).

⚠️ E a aba "Venda": so anuncios de fase de VENDA, nao de captacao.
⚠️ E um XLSX baixado, nao a planilha viva — carimbar a data do arquivo ao usar.

Uso: python scripts/carrega_planilha_ads.py <arquivo.xlsx>
"""
import csv
import sys
import time
from pathlib import Path

import openpyxl
import pandas as pd
from google.cloud import bigquery

TABELA = "bp-staging.dbt_abe.tb_ht_sheet_meta_ads"
ABA = "01. Facebook - Ads - Venda"
COLS = ["dt", "nm_anuncio", "vl_spend", "qt_impressoes", "qt_cliques", "qt_compras",
        "vl_receita_pixel", "qt_views_3s", "qt_thruplay", "id_anuncio", "nm_conjunto"]


def xlsx_para_csv(caminho, destino):
    wb = openpyxl.load_workbook(caminho, read_only=True)
    ws = wb[ABA]
    n = 0
    with open(destino, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0 or not row or not row[0]:
                continue
            d = str(row[0])[:10]
            if len(d) != 10 or d[4] != "-":   # descarta linha de totais/vazia
                continue
            w.writerow([d] + [("" if c is None else str(c)) for c in row[1:11]])
            n += 1
    wb.close()
    return n


def main():
    caminho = Path(sys.argv[1] if len(sys.argv) > 1 else
                   Path.home() / "Downloads/04.2 Mídia Paga - Anúncios FACEBOOK.xlsx")
    tmp = "/tmp/meta_ads_planilha.csv"
    t0 = time.time()
    n = xlsx_para_csv(caminho, tmp)
    print(f"{n:,} linhas extraídas da aba {ABA!r} ({time.time()-t0:.0f}s)")

    df = pd.read_csv(tmp)
    df["dt"] = pd.to_datetime(df["dt"]).dt.date
    for c in ["vl_spend", "vl_receita_pixel"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["qt_impressoes", "qt_cliques", "qt_compras", "qt_views_3s", "qt_thruplay"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    for c in ["nm_anuncio", "id_anuncio", "nm_conjunto"]:
        df[c] = df[c].astype("string")

    cli = bigquery.Client(project="bp-staging")
    cfg = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", autodetect=False, schema=[
        bigquery.SchemaField("dt", "DATE"),
        bigquery.SchemaField("nm_anuncio", "STRING"),
        bigquery.SchemaField("vl_spend", "FLOAT64"),
        bigquery.SchemaField("qt_impressoes", "INT64"),
        bigquery.SchemaField("qt_cliques", "INT64"),
        bigquery.SchemaField("qt_compras", "INT64"),
        bigquery.SchemaField("vl_receita_pixel", "FLOAT64"),
        bigquery.SchemaField("qt_views_3s", "INT64"),
        bigquery.SchemaField("qt_thruplay", "INT64"),
        bigquery.SchemaField("id_anuncio", "STRING"),
        bigquery.SchemaField("nm_conjunto", "STRING"),
    ])
    cli.load_table_from_dataframe(df, TABELA, job_config=cfg).result()
    print(f"{len(df):,} linhas -> {TABELA} ({df['dt'].min()} a {df['dt'].max()}, "
          f"R$ {df['vl_spend'].sum():,.0f})")


if __name__ == "__main__":
    main()
