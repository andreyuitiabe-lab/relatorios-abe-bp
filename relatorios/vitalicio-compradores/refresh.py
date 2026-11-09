#!/usr/bin/env python3
"""
Quem compra vitalício — Black November 2026 × BNO25 (mesmos dias) × BP10.

Usage:
  python refresh.py          # atualiza data.json (passo padrão)
  python refresh.py --push   # atualiza + git add/commit/push — só com ok do André

Queries rodam via cliente Python do BigQuery (ADC, igual ao ~/bin/bqq).
Saída (data.json) só tem agregados — nenhuma linha por pessoa sai daqui.
"""

import json, re, subprocess, sys, datetime, warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
OUT = HERE / "data.json"
SQL = (HERE / "queries" / "base_compradores.sql").read_text(encoding="utf-8")
SQL_CONV = (HERE / "queries" / "conversas_zenvia.sql").read_text(encoding="utf-8")
SQL_ABERTAS = (HERE / "queries" / "conversas_abertas.sql").read_text(encoding="utf-8")
SQL_DEALS = (HERE / "queries" / "deals_pipedrive.sql").read_text(encoding="utf-8")

# ─── janelas ─────────────────────────────────────────────────────────────────
# BNO26 vai de 01/11 até ontem (BRT); BNO25 usa os mesmos dias do mês em 2025.
HOJE = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3)).date()
FIM_BNO26 = min(HOJE - datetime.timedelta(days=1), datetime.date(2026, 11, 30))
JANELAS = {
    "ini_bno26": "2026-11-01", "fim_bno26": FIM_BNO26.isoformat(),
    "ini_bno25": "2025-11-01", "fim_bno25": FIM_BNO26.replace(year=2025).isoformat(),
    # BP10: venda 16/07 → 15/09 (marketing); o Comercial seguiu até 30/09
    "ini_bp10": "2026-07-16", "fim_bp10": "2026-09-30",
    "ini_consumo": "2025-07-01",  # cobre o D-90 da janela mais antiga (BNO25)
}
PERIODOS = ["BNO26", "BNO25", "BP10"]
CANAIS = ["Comercial", "Digital"]

# ─── BQ helper ───────────────────────────────────────────────────────────────
def bq_df(sql: str) -> pd.DataFrame:
    warnings.filterwarnings("ignore")
    from google.cloud import bigquery
    client = bigquery.Client(project="bp-datawarehouse")
    return client.query(sql).result().to_dataframe()

# ─── dimensões ───────────────────────────────────────────────────────────────
TIER = {"black": "Black", "best": "Premium", "better": "Intermediário", "good": "Essencial"}

def utm_grupo(u):
    """Campanha do UTM da venda. No Comercial é o último anúncio/CRM que a pessoa clicou."""
    if u is None or pd.isna(u) or str(u).strip() == "":
        return "Sem UTM"
    s = str(u)
    lo = s.lower()
    if "[bno26] [vit]" in lo or "bno26_vit" in lo or lo == "jornada_remarketing_bno26":
        return "BNO26 · Vitalício"
    if "bno26" in lo:
        return "BNO26 · outras linhas"
    if lo.startswith(("pmax_", "campaign_", "kw_")):
        return "Google"
    if s.isdigit():
        return "Disparo CRM"
    return "Campanhas anteriores"

def feats(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    for col in ["qt_dias_ult_lead", "qt_dias_cliente", "vl_horas_90d", "cd_income_decile",
                "qt_vitalicio_antes", "qt_compras_antes", "vl_payment_gross"]:
        d[col] = d[col].astype(float)
    d["canal"] = np.where(d.bl_is_commercial_channel.fillna(False).astype(bool), "Comercial", "Digital")
    d["tier"] = d.nm_gateway_plan.map(TIER).fillna("Originais/Econômico")
    prod = d.nm_gateway_product.fillna("").str.lower()
    d["membro_fundador"] = prod.str.contains("membro fundador")
    d["combo_livro"] = prod.str.contains(r"cole[cç][aã]o brasil|estante")
    d["rel"] = np.select(
        [d.qt_vitalicio_antes > 0, d.bl_membro_ativo.fillna(False).astype(bool),
         d.bl_ex_membro.fillna(False).astype(bool), d.qt_compras_antes > 0],
        ["Já tinha vitalício (upgrade)", "Assinante ativo", "Ex-assinante", "Só comprou produto avulso"],
        "Nunca comprou")
    dl = d.qt_dias_ult_lead
    tag = d.nm_tag_ult_lead.fillna("")
    d["lead"] = np.select(
        [d.nm_tag_ult_lead.isna(), (dl <= 30) & tag.str.startswith("lp-"), dl <= 30, dl <= 180],
        ["Nunca foi lead", "Captura na página de venda (≤30d)", "Lead novo (≤30d)", "Lead de 31–180d"],
        "Lead de mais de 180d")
    dc = d.qt_dias_cliente
    d["tempo_cliente"] = np.select(
        [dc.isna(), dc <= 365, dc <= 3 * 365], ["Cliente novo", "Menos de 1 ano", "1 a 3 anos"], "3 anos ou mais")
    h = d.vl_horas_90d.fillna(0)
    d["consumo"] = np.select([h <= 0, h < 1, h < 10], ["Nada", "Menos de 1h", "1 a 10h"], "10h ou mais")
    dec = d.cd_income_decile.fillna(-1)
    d["renda"] = np.select([dec <= 0, dec <= 6, dec <= 8], ["Sem dado", "Decil 1–6", "Decil 7–8"], "Decil 9–10")
    cart = d.nm_cartao.fillna("")
    d["cartao"] = np.select(
        [cart.isin(["6_black", "5_amex", "4_platinum"]), cart != ""],
        ["Black, Amex ou Platinum", "Gold ou inferior"], "Sem dado")
    d["pagamento"] = d.nm_payment_method.map(
        {"credit_card": "Cartão", "pix": "Pix", "billet": "Boleto", "nupay": "NuPay"}).fillna("Outro")
    d["genero"] = d.nm_genero.fillna("Sem dado")
    d["utm"] = d.nm_pptc_utm_campaign.map(utm_grupo)
    return d

# ordem fixa das categorias (cor segue a entidade, nunca o rank)
DIMS = {
    "rel": ["Nunca comprou", "Ex-assinante", "Assinante ativo", "Já tinha vitalício (upgrade)", "Só comprou produto avulso"],
    "tier": ["Essencial", "Premium", "Black", "Originais/Econômico"],
    "lead": ["Lead novo (≤30d)", "Captura na página de venda (≤30d)", "Lead de 31–180d", "Lead de mais de 180d", "Nunca foi lead"],
    "tempo_cliente": ["Cliente novo", "Menos de 1 ano", "1 a 3 anos", "3 anos ou mais"],
    "consumo": ["Nada", "Menos de 1h", "1 a 10h", "10h ou mais"],
    "renda": ["Decil 1–6", "Decil 7–8", "Decil 9–10", "Sem dado"],
    "cartao": ["Gold ou inferior", "Black, Amex ou Platinum", "Sem dado"],
    "pagamento": ["Cartão", "Pix", "NuPay", "Boleto", "Outro"],
    "genero": ["Masculino", "Feminino", "Sem dado"],
}

# ─── conversas (Zenvia) ──────────────────────────────────────────────────────
ORIGEM_CONVERSA = [
    "Botão de disparo",
    "Link WhatsApp (LP/anúncio)",
    "Vendedor abriu (hotlead)",
    "Chatbot sem histórico",
    "Contato espontâneo",
    "Botão no portal",
    "Conversa já aberta",
    "Sem conversa antes",
]

def origem_conversa(r) -> str:
    """Classifica pela 1ª interação. No chatbot (FLOW) o 1º comment guarda o que a pessoa mandou."""
    if r.nm_lead_source != "FLOW":
        return "Vendedor abriu (hotlead)"
    m = re.search(r"#### USER: (.*?)(?: ####|$)", r.txt or "")
    if not m:
        return "Chatbot sem histórico"
    u = m.group(1).strip()
    if re.search(r"portal", u, re.I):
        return "Botão no portal"
    if re.match(r"^Ol[áa]", u) and re.search(r"gostaria|saber mais|quero|tenho interesse|acabei", u, re.I):
        return "Link WhatsApp (LP/anúncio)"
    letras = re.sub(r"[^A-Za-zÀ-ú]", "", u)
    if letras and sum(c.isupper() for c in letras) / len(letras) > 0.8 and len(u) <= 40:
        return "Botão de disparo"
    return "Contato espontâneo"

ESPONTANEO = ["Pergunta sobre a oferta", "Só cumprimento", "Veio de outra área da BP",
              "Resposta ao chatbot", "Botão no portal"]

def espontaneo(r) -> str | None:
    """Subtipo do contato que não veio de botão, link ou vendedor (só agregado: o texto não sai daqui)."""
    tipo = origem_conversa(r)
    if tipo == "Botão no portal":
        return tipo
    if tipo != "Contato espontâneo":
        return None
    u = re.search(r"#### USER: (.*?)(?: ####|$)", r.txt or "").group(1).strip()
    if re.search(r"app|plataforma|clube|já faço parte|preenchi", u, re.I):
        return "Veio de outra área da BP"
    if re.search(r"vital|promo|plano|custa|preço|valor|informa|saber", u, re.I):
        return "Pergunta sobre a oferta"
    if re.fullmatch(r"(ol[áa]|oi|bom dia|boa tarde|boa noite)[\s,!.]*(bom dia|boa tarde|boa noite)?[\s!.]*", u, re.I):
        return "Só cumprimento"
    return "Resposta ao chatbot"

def conversas(b26: pd.DataFrame) -> dict:
    """Origem da 1ª conversa (a mais antiga iniciada nos 30 dias antes) de cada compra da BNO26, por canal.
    Sem conversa iniciada na janela: se houve mensagem nos 30 dias antes em qualquer conversa da pessoa
    (e-mail ou telefone), é conversa já aberta; senão, não houve conversa registrada antes da compra."""
    c = bq_df(SQL_CONV.format(**JANELAS))
    c = c[c.rn == 1].sort_values("dt_approach_start").groupby("id_transaction").first()
    origem = c.apply(origem_conversa, axis=1)
    ab = bq_df(SQL_ABERTAS.format(**JANELAS)).set_index("id_transaction")
    com_msg = ab.msgs_30d.fillna(0).astype(float) > 0
    resto = np.where(b26.id_transaction.map(com_msg).fillna(False).astype(bool),
                     "Conversa já aberta", "Sem conversa antes")
    o = b26.id_transaction.map(origem).fillna(pd.Series(resto, index=b26.index))
    esp = b26.id_transaction.map(c.apply(espontaneo, axis=1))
    com = b26.canal == "Comercial"
    return {"cats": ORIGEM_CONVERSA,
            "espontaneo": {"cats": ESPONTANEO, "n": [int(((esp == k) & com).sum()) for k in ESPONTANEO]},
            **{cn: [int(((o == k) & (b26.canal == cn)).sum()) for k in ORIGEM_CONVERSA] for cn in CANAIS}}

# ─── deals da Pipedrive ──────────────────────────────────────────────────────
HOTLEAD_GRUPO = {
    "OPORTUNIDADE DE VENDA - NOVA COMPRA": "Oportunidade pós-compra",
    "OPORTUNIDADE DE VENDA - RENOVAÇÃO": "Oportunidade pós-compra",
    "ABANDONO DE CARRINHO - NOVA COMPRA": "Recuperação de compra nova",
    "COMPRA NEGADA - NOVA COMPRA": "Recuperação de compra nova",
    "PIX EXPIRADO - RENOVAÇÃO": "Renovação que falhou",
    "COMPRA NEGADA - RENOVAÇÃO": "Renovação que falhou",
    "BOLETO EXPIRADO - RENOVAÇÃO": "Renovação que falhou",
}
CANAL_DEAL = ["Chat", "Hotlead", "Lista", "Sem deal"]

def produto_curto(p, vit) -> str:
    p = str(p).lower()
    for k, v in [("cole", "Coleção Brasil"), ("black", "Black"), ("premium", "Premium"), ("essencial", "Essencial"),
                 ("básico", "Essencial"), ("basico", "Essencial"), ("originais", "Originais"), ("econ", "Econômico"),
                 ("clube", "Clube do Livro")]:
        if k in p:
            return v + (" Vitalício" if vit and v not in ("Coleção Brasil", "Clube do Livro") else "")
    return "Outro"

def deals(b26: pd.DataFrame) -> dict:
    """Canal do deal que levou cada venda do Comercial e o detalhe dos hotleads."""
    x = bq_df(SQL_DEALS.format(**JANELAS))
    x = x[x.id_transaction.isin(b26[b26.canal == "Comercial"].id_transaction)].copy()
    x["vl"] = x.vl_payment_gross.astype(float)
    x["canal_deal"] = x.nm_commercial_channel.fillna("sem deal").str.capitalize()
    canal = [{"k": c, "n": int((x.canal_deal == c).sum()),
              "receita": round(float(x.loc[x.canal_deal == c, "vl"].sum()), 2)} for c in CANAL_DEAL]
    h = x[x.canal_deal == "Hotlead"].copy()
    h["grupo"] = h.nm_hotlead_type.map(HOTLEAD_GRUPO).fillna("Outro hotlead")
    h["h_deal"] = (h.dt_ordered_at - h.dt_deal).dt.total_seconds() / 3600
    h["prazo"] = pd.cut(h.h_deal, [-1e9, 24, 168, 1e9], labels=["Até 24h", "1 a 7 dias", "Mais de 7 dias"])
    h["src"] = [produto_curto(p, v) for p, v in zip(h.src_produto, h.src_vit.fillna(False))]
    grupos = []
    for g in ["Oportunidade pós-compra", "Recuperação de compra nova", "Renovação que falhou"]:
        y = h[h.grupo == g]
        grupos.append({
            "grupo": g, "n": int(len(y)), "receita": round(float(y.vl.sum()), 2),
            "tipos": [{"k": t.capitalize().replace(" - ", " · "), "n": int(n)} for t, n in y.nm_hotlead_type.value_counts().items()],
            "origem_reembolsada": int((y.src_status == "refunded").sum()),
            "origem_vitalicio": int(y.src_vit.fillna(False).astype(bool).sum()),
            "destino_black": int((y.nm_gateway_plan == "black").sum()),
            "origem_top": [{"k": k, "n": int(n)} for k, n in y.src.value_counts().head(3).items()],
            "prazo": [int((y.prazo == p).sum()) for p in ["Até 24h", "1 a 7 dias", "Mais de 7 dias"]],
        })
    return {"canal": canal, "hotlead": grupos, "prazos": ["Até 24h", "1 a 7 dias", "Mais de 7 dias"]}

# ─── agregações ──────────────────────────────────────────────────────────────
def kpi(x: pd.DataFrame) -> dict:
    return {"vendas": int(len(x)), "pessoas": int(x.id_person.nunique()),
            "receita": round(float(x.vl_payment_gross.sum()), 2),
            "ticket": round(float(x.vl_payment_gross.mean()), 2) if len(x) else 0.0}

def composicao(d: pd.DataFrame, dim: str) -> dict:
    cats = DIMS[dim]
    linhas = []
    for p in PERIODOS:
        for c in CANAIS:
            x = d[(d.nm_periodo == p) & (d.canal == c)]
            n = x[dim].value_counts()
            rec = x.groupby(dim).vl_payment_gross.sum()
            linhas.append({
                "periodo": p, "canal": c, "total": int(len(x)),
                "n": [int(n.get(k, 0)) for k in cats],
                "receita": [round(float(rec.get(k, 0)), 2) for k in cats],
            })
    return {"cats": cats, "linhas": linhas}

def contagem(x: pd.DataFrame, col: str, top: int = 12) -> list:
    v = x[col].fillna("(vazio)").value_counts().head(top)
    return [{"k": str(k), "n": int(n)} for k, n in v.items()]

def diaria(d: pd.DataFrame) -> dict:
    dias = list(range(1, FIM_BNO26.day + 1))
    out = {"dias": dias}
    for p in ["BNO26", "BNO25"]:
        for c in CANAIS:
            x = d[(d.nm_periodo == p) & (d.canal == c)]
            por_dia = pd.to_datetime(x.dt_venda).dt.day.value_counts()
            out[f"{p}_{c}"] = [int(por_dia.get(k, 0)) for k in dias]
    return out

def pct(a, b):
    return 100.0 * a / b if b else 0.0

def br(v, casas=0):
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def reais(v):
    return f"R$ {br(v / 1000)} mil" if v < 1e6 else f"R$ {br(v / 1e6, 2)} mi"

def achados(d: pd.DataFrame, k: dict, conv: dict, dl: dict) -> list:
    """Frases dos achados geradas a partir dos números (o texto acompanha o refresh)."""
    a = []
    com = d[(d.nm_periodo == "BNO26") & (d.canal == "Comercial")]
    n = len(com)
    utm_vit = pct((com.utm == "BNO26 · Vitalício").sum(), n)
    lead_vit = pct(((com.lead == "Lead novo (≤30d)") & com.nm_tag_ult_lead.fillna("").str.startswith("BNO26")).sum(), n)
    base = pct(com.rel.isin(["Assinante ativo", "Ex-assinante", "Já tinha vitalício (upgrade)"]).sum(), n)
    cc = dict(zip(conv["cats"], conv["Comercial"]))
    botao = pct(cc["Botão de disparo"] + cc["Chatbot sem histórico"], n)
    a.append(
        f"<b>De onde vem a venda de vitalício do Comercial:</b> {br(utm_vit)}% das vendas vieram com UTM da campanha VIT, "
        f"mas só {br(lead_vit)}% eram lead novo da VIT. {br(base)}% já eram da base (assinante, ex-assinante ou vitalício). "
        f"Em cerca de {br(botao)}% das vendas, a conversa com o vendedor começou com a pessoa respondendo a um botão de disparo de WhatsApp.")
    hot = {c["k"]: c for c in dl["canal"]}["Hotlead"]
    op = {g["grupo"]: g for g in dl["hotlead"]}["Oportunidade pós-compra"]
    a.append(
        f"<b>Hotlead leva {br(pct(hot['n'], n))}% das vendas do Comercial</b> ({br(hot['n'])} vendas, {reais(hot['receita'])}). "
        f"O maior grupo é a oportunidade pós-compra ({br(op['n'])}): a pessoa compra algo no digital, o bot abre o deal e o vendedor sobe o plano. "
        f"{br(op['destino_black'])} delas viraram Black Vitalício, e em {br(op['origem_reembolsada'])} a compra original foi reembolsada (troca).")
    b26, b25 = k["BNO26"], k["BNO25"]
    c26, c25 = b26["Comercial"], b25["Comercial"]
    g26, g25 = b26["Digital"], b25["Digital"]
    t26 = b26["Total"]; t25 = b25["Total"]

    a.append(
        f"<b>{br(t26['vendas'])} vitalícios ({reais(t26['receita'])})</b> de 01/11 a {FIM_BNO26:%d/%m}, contra "
        f"{br(t25['vendas'])} ({reais(t25['receita'])}) nos mesmos dias da BNO25. O digital passou de "
        f"{br(g25['vendas'])} para <b>{br(g26['vendas'])}</b> vendas e hoje é "
        f"{br(pct(g26['vendas'], t26['vendas']))}% do volume.")

    var_v = pct(c26["vendas"] - c25["vendas"], c25["vendas"])
    var_r = pct(c26["receita"] - c25["receita"], c25["receita"])
    bl = lambda p: d[(d.nm_periodo == p) & (d.canal == "Comercial")]
    blk26 = pct((bl("BNO26").tier == "Black").sum(), len(bl("BNO26")))
    blk25 = pct((bl("BNO25").tier == "Black").sum(), len(bl("BNO25")))
    a.append(
        f"<b>Comercial: {'mais' if var_v >= 0 else 'menos'} vendas ({'+' if var_v >= 0 else ''}{br(var_v)}%) e "
        f"{'mais' if var_r >= 0 else 'menos'} receita ({'+' if var_r >= 0 else ''}{br(var_r)}%)</b>. "
        f"O ticket foi de R$ {br(c25['ticket'])} para R$ {br(c26['ticket'])}: o Black era "
        f"{br(blk25)}% das vendas do Comercial na BNO25 e agora é {br(blk26)}%.")

    def share(p, c, dim, cat):
        x = d[(d.nm_periodo == p) & (d.canal == c)]
        return pct((x[dim] == cat).sum(), len(x))
    novo_dig = share("BNO26", "Digital", "rel", "Nunca comprou")
    ex_dig = share("BNO26", "Digital", "rel", "Ex-assinante")
    a.append(
        f"<b>O digital traz gente nova:</b> {br(novo_dig)}% dos compradores digitais nunca tinham comprado nada "
        f"da BP e {br(ex_dig)}% são ex-assinantes. No Comercial, os mesmos grupos somam "
        f"{br(share('BNO26','Comercial','rel','Nunca comprou'))}% e {br(share('BNO26','Comercial','rel','Ex-assinante'))}%.")

    at26 = share("BNO26", "Comercial", "rel", "Assinante ativo")
    at25 = share("BNO25", "Comercial", "rel", "Assinante ativo")
    at10 = share("BP10", "Comercial", "rel", "Assinante ativo")
    def blk_at(p):
        x = bl(p); x = x[x.rel == "Assinante ativo"]
        return pct((x.tier == "Black").sum(), len(x))
    a.append(
        f"<b>O Comercial converte menos assinante ativo, e esse grupo leva menos Black:</b> assinantes ativos são "
        f"{br(at26)}% das vendas do Comercial, contra {br(at25)}% na BNO25 e {br(at10)}% no BP10. Entre eles, o Black caiu "
        f"de {br(blk_at('BNO25'))}% para {br(blk_at('BNO26'))}% das compras.")

    x = d[(d.nm_periodo == "BNO26")]
    vit = x[(x.lead == "Lead novo (≤30d)")]
    d03 = pct((vit.qt_dias_ult_lead <= 3).sum(), len(vit))
    a.append(
        f"<b>Lead novo compra rápido:</b> {br(len(vit))} vendas vieram de quem cadastrou lead nos 30 dias anteriores "
        f"(a maioria na LP de vitalício da BNO26), e {br(d03)}% delas fecharam em até 3 dias do cadastro.")

    z = pct((x.consumo == "Nada").sum(), len(x))
    zat = x[x.rel == "Assinante ativo"]
    a.append(
        f"<b>Pouca gente chega assistindo:</b> {br(z)}% dos compradores não têm nenhuma sessão na plataforma "
        f"nos 90 dias antes da compra. Mesmo entre os assinantes ativos, "
        f"{br(pct((zat.consumo == 'Nada').sum(), len(zat)))}% não assistiram nada.")
    return a

# ─── build ───────────────────────────────────────────────────────────────────
def build() -> dict:
    print(f"  base de compradores ({JANELAS['ini_bno26']} → {JANELAS['fim_bno26']})...", flush=True)
    raw = bq_df(SQL.format(**JANELAS))
    d = feats(raw)

    # Big Picture Membro Fundador: lançamento à parte que caiu na 1ª semana da BNO25.
    # Fica fora da comparação; os números dele vão separados.
    mf = d[d.membro_fundador]
    d = d[~d.membro_fundador]

    k = {}
    for p in PERIODOS:
        k[p] = {c: kpi(d[(d.nm_periodo == p) & (d.canal == c)]) for c in CANAIS}
        k[p]["Total"] = kpi(d[d.nm_periodo == p])

    b26 = d[d.nm_periodo == "BNO26"]
    tier_ticket = []
    for c in CANAIS:
        for t in DIMS["tier"]:
            x = b26[(b26.canal == c) & (b26.tier == t)]
            if len(x):
                tier_ticket.append({"canal": c, "tier": t, "n": int(len(x)),
                                    "ticket": round(float(x.vl_payment_gross.mean()), 2),
                                    "mediana": round(float(x.vl_payment_gross.median()), 2),
                                    "receita": round(float(x.vl_payment_gross.sum()), 2)})

    print("  conversas na Zenvia...", flush=True)
    conv = conversas(b26)
    print("  deals da Pipedrive...", flush=True)
    dl = deals(b26)
    com = b26[b26.canal == "Comercial"]
    cruz = (pd.crosstab(com.lead, com.rel).reindex(index=DIMS["lead"], columns=DIMS["rel"]).fillna(0).astype(int))

    novos = b26[b26.lead == "Lead novo (≤30d)"]
    dias_lead = novos.qt_dias_ult_lead.clip(upper=30)
    faixas = ["Mesmo dia", "1 a 3 dias", "4 a 7 dias", "8 a 30 dias"]
    fx = pd.cut(dias_lead, [-1, 0, 3, 7, 30], labels=faixas)

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "janelas": JANELAS,
        "kpi": k,
        "membro_fundador_bno25": kpi(mf[mf.nm_periodo == "BNO25"]),
        "diaria": diaria(d),
        "dims": {dim: composicao(d, dim) for dim in DIMS},
        "tier_ticket": tier_ticket,
        "bno26": {
            "utm_comercial": contagem(com.assign(u=com.utm), "u"),
            "utm_digital": contagem(b26[b26.canal == "Digital"], "utm"),
            "publisher_digital": contagem(b26[b26.canal == "Digital"], "nm_pptc_tracking_publisher"),
            "tags_lead_novo": [
                {"k": t, "Comercial": int(((novos.nm_tag_ult_lead == t) & (novos.canal == "Comercial")).sum()),
                 "Digital": int(((novos.nm_tag_ult_lead == t) & (novos.canal == "Digital")).sum())}
                for t in novos.nm_tag_ult_lead.value_counts().head(8).index
            ],
            "tags_captura": contagem(b26[b26.lead == "Captura na página de venda (≤30d)"], "nm_tag_ult_lead"),
            "dias_lead": {c: [int(((fx == f) & (novos.canal == c)).sum()) for f in faixas] for c in CANAIS},
            "dias_lead_faixas": faixas,
            "uf": [{"k": u, "Comercial": int(((b26.cd_address_state == u) & (b26.canal == "Comercial")).sum()),
                    "Digital": int(((b26.cd_address_state == u) & (b26.canal == "Digital")).sum())}
                   for u in b26.cd_address_state.value_counts().head(10).index],
            "comercial_lead_x_rel": {"linhas": DIMS["lead"], "colunas": DIMS["rel"], "n": cruz.values.tolist()},
            "combo_livro_comercial": int(com.combo_livro.sum()),
            "conversa": conv,
            "deals": dl,
        },
        "achados": achados(d, k, conv, dl),
    }

# ─── main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    push = "--push" in sys.argv
    print("Refreshing vitalicio-compradores from BigQuery...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m", f"data: vitalicio-compradores refresh {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
