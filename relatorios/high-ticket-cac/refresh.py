#!/usr/bin/env python3
"""Gera data.json do relatório high-ticket (CAC e saturação).

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Fontes:
  - queries/*.sql            -> BigQuery (via bqq, nunca `bq query`: a credencial do bq CLI
                                expira ~diariamente e falha em sessão não-interativa)
  - bp-staging.dbt_abe.tb_ht_meta_spend -> spend Meta desde ago/2023, carregado por
                                scripts/carrega_meta_bq.py a partir da Marketing API.
                                Rodar `python scripts/extrai_meta_api.py` + o carregador
                                antes deste script quando quiser atualizar a mídia.
  - tb_ht_sheet_meta_ads     -> planilha histórica do time de tráfego em nível de anúncio
                                (01/06/2022 -> 16/04/2026), carregada de um XLSX BAIXADO por
                                scripts/carrega_planilha_ads.py. É a única fonte de contagem de
                                anúncio para TRA, TRA2, BNO24 e BIT. ⚠️ Não atualiza sozinha:
                                rebaixar o arquivo e recarregar quando precisar de dado novo.
  - MIDIA_PLANILHA           -> a Travessia de 2023 é anterior ao alcance da API (37 meses);
                                o custo dela vem da planilha do time de tráfego e está
                                fixado aqui de propósito, com a fonte marcada no data.json.
"""

import datetime
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).parent
OUT = AQUI / "data.json"

# Travessia 2023: captação 178.970,39 + nutrição 35.845,38 + venda 655.000,00.
# Planilha oficial do time de tráfego (aba matriz, coluna TRA-2023), registrada em
# wiki-brasil-paralelo/campanhas-contexto.md. Ela confirma o faturamento medido aqui
# (planilha R$ 8,10 mi vs warehouse R$ 8,01 mi, 1,2%), o que dá confiança no custo.
MIDIA_PLANILHA = {"TRA": 869_815.77}

# Preços de disparo usados no custo de CRM (fonte canônica: wiki zenvia-custos.md, que corrige
# o antigo R$ 0,33 para 0,323). E-mail é contratado — o R$ 0,0008 é diluição por envio, não
# custo marginal. Push e in-app entram como zero (inclusos na plataforma).
PRECO_DISPARO = {"whatsapp": 0.323, "email": 0.0008, "app_push": 0.0, "inapp": 0.0}

# Comissão do Comercial sobre a venda (premissa do André, set/2026). É PISO: não inclui folha
# nem ferramenta. Consequência a manter à vista no relatório: com custo proporcional à receita,
# o ROAS do Comercial é 1/0,09 = 11,11x POR CONSTRUÇÃO — só o CAC dele é informativo.
COMISSAO_COMERCIAL = 0.09


def bqq(sql_path: Path) -> pd.DataFrame:
    """Roda um .sql pelo bqq e devolve DataFrame."""
    destino = AQUI / "dados" / f"{sql_path.stem}.csv"
    destino.parent.mkdir(exist_ok=True)
    r = subprocess.run(["bqq", str(sql_path), "-o", str(destino)],
                       capture_output=True, text=True, cwd=AQUI)
    if r.returncode != 0:
        raise RuntimeError(f"{sql_path.name}: {r.stderr.strip()[:400]}")
    return pd.read_csv(destino)


def bqq_inline(sql: str) -> pd.DataFrame:
    tmp = AQUI / "dados" / "_tmp.sql"
    tmp.parent.mkdir(exist_ok=True)
    tmp.write_text(sql)
    try:
        return bqq(tmp)
    finally:
        tmp.unlink(missing_ok=True)


def nn(v):
    """NaN/NaT -> None, para o JSON não virar 'NaN' (que quebra o fetch)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (pd.Timestamp, datetime.date)):
        return str(v)
    return v.item() if hasattr(v, "item") else v


Q_SERIE_ANUAL = """
WITH ht AS (
  SELECT EXTRACT(YEAR FROM dt_ordered_at) AS ano,
         SUM(IF(vl_payment_gross > 1000, vl_payment_gross, 0)) AS vl_ht,
         COUNT(DISTINCT IF(vl_payment_gross > 1000, id_gateway_customer, NULL)) AS qt_compradores
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved' AND bl_is_renovation = FALSE AND dt_ordered_at >= '2022-01-01'
  GROUP BY 1
),
base AS (
  SELECT EXTRACT(YEAR FROM dt_dates) AS ano, AVG(qt_paying_active_members) AS qt_base
  FROM `bp-datawarehouse.datamart.cbo_daily_members` GROUP BY 1
)
SELECT ano, ROUND(vl_ht) AS vl_ht, qt_compradores, ROUND(qt_base) AS qt_base,
       ROUND(vl_ht / qt_base, 2) AS vl_ht_por_membro
FROM ht JOIN base USING (ano) ORDER BY ano
"""

# ⚠️ "Anterior" por DATA da primeira compra, não por `ord`. BP10 (11/06-15/09) e ODI
# (17/07-16/09) se sobrepõem: pelo ordinal, 115 compradores que compraram BP10 DEPOIS do
# ODI contavam como anteriores. Por data, ODI cai de 54,1% para 50,7% e BP10 sobe p/ 6,6%.
Q_REINCIDENCIA = """
WITH c AS (
  SELECT sigla, ord, id_comprador, dt_primeira_compra
  FROM `bp-staging.dbt_abe.tb_ht_compradores` WHERE bl_universo_principal
),
-- para cada comprador da campanha A, a campanha anterior mais recente em que ele comprou
antes AS (
  SELECT
    a.ord, a.sigla, a.id_comprador,
    ARRAY_AGG(b.sigla ORDER BY b.dt_primeira_compra DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_origem
  FROM c AS a
  LEFT JOIN c AS b
    ON b.id_comprador = a.id_comprador
   AND b.sigla <> a.sigla
   AND b.dt_primeira_compra < a.dt_primeira_compra
  GROUP BY 1, 2, 3
),
por_origem AS (
  SELECT ord, sigla, nm_origem, COUNT(*) AS qt
  FROM antes WHERE nm_origem IS NOT NULL
  GROUP BY 1, 2, 3
  QUALIFY ROW_NUMBER() OVER (PARTITION BY sigla ORDER BY COUNT(*) DESC) = 1
),
tot AS (
  SELECT ord, sigla, COUNT(*) AS qt_compradores, COUNTIF(nm_origem IS NOT NULL) AS qt_reincidentes
  FROM antes GROUP BY 1, 2
)
SELECT
  t.ord, t.sigla, t.qt_compradores,
  ROUND(100 * t.qt_reincidentes / t.qt_compradores, 1) AS pct_reincidente,
  o.nm_origem                                          AS nm_origem_principal,
  ROUND(100 * o.qt / t.qt_compradores, 1)              AS pct_origem_principal
FROM tot AS t LEFT JOIN por_origem AS o USING (sigla)
-- o BNO25 saiu do escopo do relatório, mas continua valendo como ORIGEM de reincidência
-- (é a origem principal do DBI) — por isso o filtro é só na linha de saída
WHERE t.sigla <> 'BNO25'
ORDER BY t.ord
"""

# Preço e volume de cada degrau do vitalício nas duas campanhas que o venderam para a base.
# Substituiu o antigo Q_BNO_MIX (BNO24/BNO25/BP10) quando o BNO25 saiu do escopo em 21/09/2026:
# a pergunta "mudamos a oferta?" passa a ser respondida por BNO24 × BP10, que é comparação de
# vitalício contra vitalício — mais limpa do que a anterior, que comparava com uma campanha de
# entrada.
Q_VITALICIO = """
SELECT sigla, nm_plano_principal AS nm_plano,
       COUNT(*) AS qt, ROUND(AVG(vl_receita)) AS vl_ticket, ROUND(SUM(vl_receita)) AS vl_receita
FROM `bp-staging.dbt_abe.tb_ht_compradores`
WHERE bl_universo_principal AND sigla IN ('BNO24', 'BP10')
  AND REGEXP_CONTAINS(LOWER(nm_plano_principal), r'vital')
GROUP BY 1, 2
HAVING qt >= 50
ORDER BY sigla, vl_receita DESC
"""


def build() -> dict:
    print("  consolidado por campanha...", flush=True)
    cons = bqq(AQUI / "queries" / "06_consolidado.sql")
    cons["nm_fonte_midia"] = "api_meta+warehouse"

    print("  economia por canal...", flush=True)
    canal = bqq(AQUI / "queries" / "07_economia_por_canal.sql")
    canal_midia_comp = canal[canal["nm_canal"] == "midia_paga"].set_index("sigla")["qt_compradores"]

    # Travessia: verba da planilha (2023 é anterior ao alcance da Marketing API)
    for sigla, valor in MIDIA_PLANILHA.items():
        m = cons["sigla"] == sigla
        cons.loc[m, "vl_midia"] = valor
        cons.loc[m, "nm_fonte_midia"] = "planilha_trafego"
        cons.loc[m, "vl_cac"] = round(valor / cons.loc[m, "qt_compradores"].iloc[0], 2)
        cons.loc[m, "vl_roas"] = round(cons.loc[m, "vl_receita"].iloc[0] / valor, 2)
        # ⚠️ CAC do canal mídia usa a CONTAGEM real de compradores de mídia, nunca o
        # percentual arredondado do consolidado: 4.856 × 5,3% dava 257,4 em vez de 256,
        # e o CAC saía 0,5% errado e divergente do que o próprio data.json publica em `canais`.
        comp_midia = int(canal_midia_comp[sigla])
        cons.loc[m, "vl_cac_canal_midia"] = round(valor / comp_midia, 2)
    # Travessia: a verba vem da planilha (2023 é anterior ao alcance da Marketing API)
    m = (canal["sigla"] == "TRA") & (canal["nm_canal"] == "midia_paga")
    canal.loc[m, "vl_custo"] = MIDIA_PLANILHA["TRA"]
    canal.loc[m, "nm_natureza_custo"] = "verba total da campanha (planilha do tráfego)"
    canal.loc[m, "vl_cac_canal"] = round(MIDIA_PLANILHA["TRA"] / canal.loc[m, "qt_compradores"].iloc[0], 2)
    canal.loc[m, "vl_roas_canal"] = round(canal.loc[m, "vl_receita"].iloc[0] / MIDIA_PLANILHA["TRA"], 2)

    print("  o que foi vendido em cada campanha...", flush=True)
    produto = bqq(AQUI / "queries" / "08_cac_por_produto.sql")
    # Travessia: verba da planilha (2023 é anterior ao alcance da Marketing API)
    mp = produto["sigla"] == "TRA"
    tot_rec = produto.loc[mp, "vl_receita"].sum()
    tot_comp = produto.loc[mp, "qt_compradores"].sum()
    verba = MIDIA_PLANILHA["TRA"]
    produto.loc[mp, "vl_custo_rateio_receita"] = (verba * produto.loc[mp, "vl_receita"] / tot_rec).round()
    produto.loc[mp, "vl_cac_rateio_receita"] = (
        verba * produto.loc[mp, "vl_receita"] / tot_rec / produto.loc[mp, "qt_compradores"]).round(2)
    produto.loc[mp, "vl_cac_rateio_comprador"] = round(verba / tot_comp, 2)
    produto.loc[mp, "vl_roas_rateio_receita"] = round(tot_rec / verba, 2)
    produto.loc[mp, "vl_roas_rateio_comprador"] = (
        produto.loc[mp, "vl_receita"] / (verba / tot_comp * produto.loc[mp, "qt_compradores"])).round(2)

    print("  receita líquida de aquisição...", flush=True)
    liquido = bqq(AQUI / "queries" / "16_receita_liquida_aquisicao.sql")

    print("  CAC por faixa de valor da venda...", flush=True)
    faixas = bqq(AQUI / "queries" / "15_cac_por_faixa_valor.sql")

    print("  peças criadas (anúncios e e-mails distintos)...", flush=True)
    pecas = bqq(AQUI / "queries" / "12_pecas_criadas.sql")

    print("  quantidade de anúncios...", flush=True)
    anuncios = bqq(AQUI / "queries" / "14_qtd_anuncios_v2.sql")

    print("  funil do Comercial (abordagem → conversa → venda)...", flush=True)
    comercial = bqq(AQUI / "queries" / "10_conversao_comercial.sql")

    print("  testes de atribuição (universo e série da casa)...", flush=True)
    testes = bqq(AQUI / "queries" / "09_testes_atribuicao.sql")

    print("  série anual de high-ticket...", flush=True)
    anual = bqq_inline(Q_SERIE_ANUAL)
    print("  reincidência entre campanhas...", flush=True)
    reinc = bqq_inline(Q_REINCIDENCIA)
    print("  preço e volume do vitalício (BNO24 × BP10)...", flush=True)
    vit = bqq_inline(Q_VITALICIO)

    # merge por sigla, nunca por posição: zip() silenciosamente atribuiria a reincidência
    # à campanha errada se uma das listas mudasse de tamanho ou de ordem
    reinc_por_sigla = reinc.set_index("sigla").to_dict("index")
    comercial_por_sigla = comercial.set_index("sigla").to_dict("index")
    anuncios_por_sigla = anuncios.set_index("sigla").to_dict("index")
    faixa_alto = faixas[faixas["nm_faixa"] == "alto"].set_index("sigla").to_dict("index")
    liq_por_sigla = liquido.set_index("sigla").to_dict("index")
    pecas_por_sigla = pecas.set_index("sigla").to_dict("index")
    campanhas = [{k: nn(v) for k, v in linha.items()} for linha in cons.to_dict("records")]
    for c in campanhas:
        r = reinc_por_sigla.get(c["sigla"], {})
        c["pct_reincidente"] = nn(r.get("pct_reincidente"))
        cm = comercial_por_sigla.get(c["sigla"], {})
        c["qt_conversas"] = nn(cm.get("qt_conversas"))
        c["pct_conv_conversa"] = nn(cm.get("pct_conv_conversa"))
        c["pct_conv_abordagem"] = nn(cm.get("pct_conv_abordagem"))
        an = anuncios_por_sigla.get(c["sigla"], {})
        c["qt_anuncios"] = nn(an.get("qt_anuncios"))
        c["qt_conjuntos"] = nn(an.get("qt_conjuntos"))
        c["qt_ads_venda"] = nn(an.get("qt_ads_venda"))
        c["qt_ads_todas_fases"] = nn(an.get("qt_ads_todas_fases"))
        c["nm_fonte_contagem_ads"] = nn(an.get("nm_fonte_contagem"))
        if c.get("qt_anuncios") and c.get("vl_midia"):
            c["vl_spend_por_anuncio"] = round(c["vl_midia"] / c["qt_anuncios"])
        # ⚠️ contagem de campanhas SÓ Meta, para ficar na mesma unidade da contagem de anúncios.
        # O `qt_campanhas_midia` do consolidado conta Meta+Google+PMax e não é comparável.
        c["qt_campanhas_meta"] = nn(an.get("qt_campanhas_meta"))
        fa = faixa_alto.get(c["sigla"], {})
        c["vl_cac_alto_ticket"] = nn(fa.get("vl_cac_faixa"))
        c["qt_comp_alto_ticket"] = nn(fa.get("qt_compradores"))
        c["vl_ticket_alto"] = nn(fa.get("vl_ticket"))
        lq = liq_por_sigla.get(c["sigla"], {})
        for k in ("vl_custo_aquisicao", "vl_comissao", "vl_custo_crm",
                  "pct_liquido_aquisicao", "vl_liquido_por_comprador", "pct_custo_midia"):
            c[k] = nn(lq.get(k))
        pc = pecas_por_sigla.get(c["sigla"], {})
        for k in ("qt_email_tag", "qt_whatsapp_tag", "qt_push_tag", "qt_pecas_crm_tag",
                  "qt_pecas_crm_por_dia", "qt_entregas_por_peca", "qt_email_janela"):
            c[k] = nn(pc.get(k))
        c["nm_origem_principal"] = nn(r.get("nm_origem_principal"))
        c["pct_origem_principal"] = nn(r.get("pct_origem_principal"))

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "premissas": {
            "comissao_comercial": COMISSAO_COMERCIAL,
            "preco_disparo": PRECO_DISPARO,
            "midia_planilha": MIDIA_PLANILHA,
        },
        "campanhas": campanhas,
        "canais": [{k: nn(v) for k, v in l.items()} for l in canal.to_dict("records")],
        "produtos": [{k: nn(v) for k, v in l.items()} for l in produto.to_dict("records")],
        "faixas": [{k: nn(v) for k, v in l.items()} for l in faixas.to_dict("records")],
        "teste_universo": [{k: nn(v) for k, v in l.items()}
                           for l in testes[testes["nm_teste"] == "teste1_universo"].to_dict("records")],
        "serie_casa": [{k: nn(v) for k, v in l.items()}
                       for l in testes[testes["nm_teste"] == "teste2_serie_casa"].to_dict("records")],
        "anual": [{k: nn(v) for k, v in l.items()} for l in anual.to_dict("records")],
        "vitalicio": [{k: nn(v) for k, v in l.items()} for l in vit.to_dict("records")],
    }


if __name__ == "__main__":
    print("Refreshing high-ticket-cac report data from BigQuery...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']} — {len(data['campanhas'])} campanhas")
        if "--push" in sys.argv:
            subprocess.run(["git", "add", str(OUT)], check=True, cwd=AQUI)
            subprocess.run(["git", "commit", "-m",
                            f"data: high-ticket-cac refresh {datetime.date.today()}"],
                           check=True, cwd=AQUI)
            subprocess.run(["git", "push", "origin", "main"], check=True, cwd=AQUI)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
