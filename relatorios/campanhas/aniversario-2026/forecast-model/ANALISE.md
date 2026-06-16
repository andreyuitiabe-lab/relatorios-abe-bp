# Forecast de Campanha — Modelo Parametrizável

**Data:** 15/jun/2026 | **Analista:** André Abe
**Artefato:** [`index.html`](index.html) (calculador interativo) | **Base:** expande a análise de [`../ANALISE.md`](../ANALISE.md)

---

## Pergunta original

Construir um modelo de forecast parametrizável que, dado o **tipo de campanha** e a **meta de receita**, estime: (a) quanto investir em tráfego e (b) qual o potencial de vendas — separando o motor de upsell da base (Vitalício) do motor de aquisição (assinaturas/certificações), respeitando a depleção por cohort.

## Lógica do modelo (2 motores independentes)

**Motor 1 — Upsell Vitalício (receita da base):**
```
Σ_faixa [ base_elegível × conv_faixa × mult_sazonal × fator_depleção × mult_tipo × fator_janela ] × ticket_2300
```
Vitalício é produto de fidelização — comprado por membro maduro. Modelado por faixa de maturidade porque a conversão cresce com o tempo de relacionamento (0-3m: 0,27% → 24m+: 1,50%).

**Motor 2 — Aquisição (receita de leads novos):**
```
leads_aquecimento × conv_lead→comprador(tipo, produção) × ticket_aquisição
```
Documentário inédito puxa **volume** de leads com baixa eficiência; oferta sobre catálogo tem alta eficiência e pouco topo de funil.

**Mix de canal** separa lead pago (custa CPL) de lead CRM/owned (grátis):
`investimento = leads × 70% × CPL`. CPL é **input** do time de mídia (a tabela Meta no BQ está quebrada).

**Cenários:** pessimista = realista × 0,70 | otimista = realista × 1,35 (variância histórica entre campanhas).

---

## Coeficientes — origem e validação

Todos rodados no BigQuery em 15/jun/2026. Queries em [`queries/`](queries/).

| Coeficiente | Valor | Fonte / validação | vs ponto de partida |
|---|---|---|---|
| Base elegível por faixa | 558.091 total | [`01`](queries/01_base_elegivel_atual.sql) | ✅ confirmado (variação <0,5%) |
| Conversão por faixa (jun/jul) | 0,27% → 1,50% | [`03`](queries/03_conversao_faixa_bpday2025.sql), BPDay2025 | ✅ validado no BQ (antes vinha do Notion) |
| **Fator de depleção por ciclo** | **0,60 bruto** | [`02`](queries/02_deplecao_por_cohort.sql), BF24/BF23 | 🆕 **peça nova — validada** |
| Ticket médio Vitalício ponderado | R$ 2.300 | tier mix BPDay2025 | ✅ idêntico |
| Mix de canal pago | ~70% | [`04`](queries/04_mix_canal_leads.sql) | 🔄 ajustado de 65% → 70% (Google/YT pago soma ao Meta) |
| Mix CRM owned (grátis) | ~12% | [`04`](queries/04_mix_canal_leads.sql) | ✅ confirmado (~11%) |
| Ticket aquisição | R$ 280 | proxy ELS Meta Ads R$252 | ⚠️ premissa |
| CPL | R$ 60 (default) | input de mídia | ⚠️ premissa — não medido |

### Resultado da depleção por cohort (achado central)

1. **Penetração de Vitalício dentro da base ativa, por cohort:** 2020 28,0% · 2021 24,7% · 2022 17,7% · 2023 29,9% · 2024 11,7% · 2025 2,6% · 2026 0,7%. As cohorts antigas estão fortemente depletadas; as novas são pool fresco.

2. **Fator de depleção por ciclo (limpo):** a mesma cohort exposta à oferta em BF2024 extraiu **0,59–0,61** do que extraiu em BF2023 (cohorts 2020/2021/2022). → **a oferta extrai ~60% do volume anterior a cada nova campanha sobre a mesma safra.**

3. **Cada campanha vive de pool fresco:** em toda campanha, a cohort mais recente é a que mais rende (BF2023→cohort2023, BF2024→cohort2024, BPDay2025→cohort2025). Confirma que a renovação da base (aquisição) é o que sustenta o upsell no longo prazo.

### Decisão de modelagem importante (dupla contagem da depleção)

A conversão de referência (FAIXAS) **já é a BPDay2025** → já embute a depleção acumulada até jun/2025. Aplicar o fator bruto 0,60 sobre ela contaria a depleção duas vezes. Por isso o modelo aplica um fator **incremental abrandado de 0,80** sobre as faixas maduras (12m+) para projetar um ciclo adicional (jun/2026), e 1,0 nas faixas jovens (pool fresco). **Confirmar se 0,80 é a agressividade certa** — é o parâmetro mais sensível do Motor 1.

---

## Validação do modelo contra o histórico (back-test)

| Cenário simulado | Realista do modelo | Histórico real | Avaliação |
|---|---|---|---|
| BPDay junho, só Vitalício, 40d | R$ 10,1M | BPDay2025: R$ 20,3M Vit | Conservador — base hoje mais depletada que jun/2025 |
| Black Friday novembro, só Vitalício, 30d | R$ 34,3M | BF2024: R$ 37,6M / BF2023: R$ 49,5M | ✅ dentro da faixa histórica |

O BPDay 2026 projeta abaixo do BPDay 2025 porque a base elegível já está mais esgotada — coerente com a tendência de queda observada (BF23 R$49,5M → BF24 R$37,6M). O modelo é honesto: a meta de R$15M só Vitalício aparece com gap, sinalizando necessidade de aquisição ou tier Black mais agressivo.

---

## Premissas (rotuladas) e limitações

- ⚠️ **Rebranding de assinaturas:** sem histórico. Ticket de aquisição R$280 e taxa de conversão são estimativas — recalibrar após a primeira campanha.
- ⚠️ **CPL:** parâmetro de entrada, não medido (tabela `bp-lake.facebook_ads.AdInsights` quebrada). Default R$60 documentado como premissa.
- ⚠️ **Multiplicador sazonal de novembro (3,2×):** extrapolado de 2 campanhas BF. Novembro converte muito melhor (oferta + proximidade da renovação anual), mas n=2.
- ⚠️ **ROAS do modelo** é sobre receita total (base + aquisição) ÷ tráfego — não é ROAS direto de pixel. Não comparar 1:1 com o ROAS Meta.
- O modelo não separa Comercial vs Digital no pós-venda (88,5% do incremental Vitalício é Comercial) — captura só a venda de entrada da campanha.

## Como recalibrar após a próxima campanha

1. Rodar [`03`](queries/03_conversao_faixa_bpday2025.sql) com as datas da nova campanha → atualizar `FAIXAS.conv`.
2. Rodar [`02`](queries/02_deplecao_por_cohort.sql) incluindo a nova campanha → reaferir o fator de depleção (0,60 bruto / 0,80 incremental).
3. Medir CPL e ticket de aquisição reais → substituir as premissas no HTML.
4. Comparar forecast vs realizado → ajustar a banda de cenários (hoje −30%/+35%).

## Queries

| Arquivo | O que faz | Status |
|---|---|---|
| [01_base_elegivel_atual.sql](queries/01_base_elegivel_atual.sql) | Base elegível por faixa (jun/2026) | ✅ rodou |
| [02_deplecao_por_cohort.sql](queries/02_deplecao_por_cohort.sql) | Depleção por cohort + fator 0,60 | ✅ rodou |
| [03_conversao_faixa_bpday2025.sql](queries/03_conversao_faixa_bpday2025.sql) | Conversão Vitalício por faixa (jun/jul) | ✅ rodou |
| [04_mix_canal_leads.sql](queries/04_mix_canal_leads.sql) | Mix de canal dos leads de aquecimento | ✅ rodou |

## Wiki a atualizar (André faz)

- `metricas-referencia.md` — adicionar **fator de depleção por cohort 0,60** e penetração de Vitalício por cohort na base ativa (2020 28% → 2026 0,7%).
- `vitalicio.md` — registrar que a oferta extrai ~60% do volume da campanha anterior sobre a mesma cohort; cada campanha vive de pool fresco.
- `regras-negocio.md` — invariante novo: "Depleção de Vitalício é por cohort, não por faixa de maturidade; fator ~0,60 por ciclo."
- `meta-insider-ads.md` ou `dbt-fct-leads-events.md` — UTMs da `lead_registration` ficam no struct `st_utms` (source/medium/campaign); sinais auxiliares `id_fbclid`/`id_gclid`. Mix BPDay2025: 70% pago / 12% CRM / 12% orgânico / 6% sem atribuição.
