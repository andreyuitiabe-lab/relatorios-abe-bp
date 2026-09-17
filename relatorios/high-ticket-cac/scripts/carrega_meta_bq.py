"""Carrega o CSV da Marketing API em bp-staging.dbt_abe.tb_ht_meta_spend.

O CSV vem de extrai_meta_api.py (campanha x dia x conta, ago/2023 -> hoje). No BQ ele vira
a fonte de spend Meta da analise -- o mart dtm_analytics_facebook_ads_funnel so comeca em
ago/2025 e nao cobre TRA2/BNO24/BIT.

Uso: python scripts/carrega_meta_bq.py [dados/meta_spend_diario.csv]
"""
import sys

import pandas as pd
from google.cloud import bigquery

TABELA = "bp-staging.dbt_abe.tb_ht_meta_spend"


def main():
    caminho = sys.argv[1] if len(sys.argv) > 1 else "dados/meta_spend_diario.csv"
    df = pd.read_csv(caminho)
    df["dt"] = pd.to_datetime(df["dt"]).dt.date
    for c in ["id_conta", "nm_conta", "id_campanha", "nm_campanha", "nm_objetivo"]:
        df[c] = df[c].astype("string")  # id_campanha vem numerico do CSV
    for c in ["vl_spend", "qt_impressoes", "qt_cliques", "qt_leads", "qt_compras"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[df["vl_spend"].fillna(0) > 0]  # linha sem verba nao interessa

    cli = bigquery.Client(project="bp-staging")
    cfg = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        schema=[
            bigquery.SchemaField("dt", "DATE"),
            bigquery.SchemaField("id_conta", "STRING"),
            bigquery.SchemaField("nm_conta", "STRING"),
            bigquery.SchemaField("id_campanha", "STRING"),
            bigquery.SchemaField("nm_campanha", "STRING"),
            bigquery.SchemaField("nm_objetivo", "STRING"),
            bigquery.SchemaField("vl_spend", "FLOAT64"),
            bigquery.SchemaField("qt_impressoes", "INT64"),
            bigquery.SchemaField("qt_cliques", "INT64"),
            bigquery.SchemaField("qt_leads", "INT64"),
            bigquery.SchemaField("qt_compras", "INT64"),
        ],
    )
    cli.load_table_from_dataframe(df, TABELA, job_config=cfg).result()
    print(f"{len(df):,} linhas -> {TABELA} "
          f"({df['dt'].min()} a {df['dt'].max()}, R$ {df['vl_spend'].sum():,.0f})")


if __name__ == "__main__":
    main()
