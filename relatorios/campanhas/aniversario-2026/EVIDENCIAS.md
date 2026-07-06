# Base de Evidências — Campanha Aniversário BP 2026

Cada afirmação do relatório (`index.html`) ligada ao dado real e à fonte. Projeto BigQuery: `bp-datawarehouse`. Data de referência: 16/jun/2026.

Legenda de status:
- ✅ **Re-validado** — re-rodado e confirmado pelo analista de dados na revisão.
- ☑️ **Validado** — rodado uma vez nesta análise.
- ⚠️ **Premissa/input** — não medido nos dados (input de gestão/mídia ou análogo).

---

## 1. Tamanho e composição da base (Jun/2026)

**Fonte:** `dim_subscriptions` (ativos: nm_status IN active/wo renewal, nm_type=paid, datas válidas) + `fct_transactions` (bl_lifetime_offer p/ vitalícios) + primeira compra (MIN dt_ordered_at). Queries `01_base_ativa_maturidade.sql`, `02_base_elegivel_vitalicio.sql`.

| Faixa | Total ativo | Já com Vitalício | Elegível | % saturado |
|---|---|---|---|---|
| 0-3m | 73.471 | 246 | 73.225 | 0,3% |
| 3-6m | 49.284 | 467 | 48.817 | 0,9% |
| 6-9m | 53.545 | 664 | 52.881 | 1,2% |
| 9-12m | 47.706 | 1.519 | 46.187 | 3,2% |
| 12-18m | 98.481 | 2.175 | 96.306 | 2,2% |
| 18-24m | 67.518 | 7.832 | 59.686 | 11,6% |
| 24m+ | 231.147 | 49.880 | 181.266 | 21,6% |

- **Base ativa total:** 623,6k (re-run posterior: 620,9k — diferença 0,4% por timing). ✅
- **Elegível p/ Vitalício:** 558,3k (re-validado: 558,2k). ✅
- **Universo trabalhável 9m+:** 383,4k ☑️
- **Núcleo 12m+:** 337,3k ☑️
- **Slice premium elegível (plano atual):** Premium GBB (best) ≈ 42k; Black recorrente ≈ 2k. ☑️ (query composição de plano da base 9m+)

**Sustenta no relatório:** §3 (Tamanho da base), §2-③ (saturação por faixa).

---

## 2. Saturação por exposição — quantas vezes a base já viu a oferta

**Fonte:** base elegível 12m+ classificada por nº de campanhas de Vitalício (BF 2023, BF 2024, BPDay 2025) em que já era cliente (dt_primeira_compra antes da campanha), sem ter comprado vitalício. ☑️

| Campanhas de Vitalício já vistas (sem comprar) | Membros | % |
|---|---|---|
| 0 — nunca viu a oferta | 4.615 | 1,4% |
| 1 | 103.910 | 30,8% |
| 2 | 68.386 | 20,3% |
| 3 (recusou BF23+BF24+BPD25) | 159.749 | 47,4% |

- **~99% da base madura já recebeu a oferta; 47% recusaram 3×.**
- **Fluxo de maturação:** 99.068 membros elegíveis cruzam 12m nos próximos 6 meses (~16,5k/mês). ☑️

**Sustenta:** §2-③ ("colheita de fluxo, não mineração de estoque"); §9 Risco 1 (saturação).

---

## 3. Conversão de Vitalício por faixa — referência Jun-Jul/2025

**Fonte:** relatório Notion "Análise de Perfil Membros Vitalícios" (tabela cohort) + validação fct_transactions. Referência correta = Jun-Jul/2025 (mesma estação/formato do aniversário).

| Faixa | Conversão Jun-Jul/2025 |
|---|---|
| 0-3m | 0,16% |
| 3-6m | 0,29% |
| 6-9m | 0,31% |
| 9-12m | 1,12% |
| 12-18m | 1,14% |
| 18-24m | 0,71% |
| 24m+ | 1,41% |
| Geral ponderado | 0,49% |

**Saturação histórica (mesmo bucket 24m+, campanhas sucessivas):** 12,93% (Nov/23) → 6,28% (Nov/24) → 1,41% (Jun-Jul/25). Geral: 3,06% → 2,38% → 0,49%.

**Sustenta:** forecast bottom-up do Vitalício (§7); tese de saturação.

---

## 4. Âncora do forecast — BPDay 2025 (22/06–31/07), composição real por frente

**Fonte:** `fct_transactions` (approved), janela BPDay 2025. ✅ (re-validado: R$29,19M total, R$20,33M Vitalício, 8.766 compradores, ticket R$2.319)

| Frente | Compradores | Receita | Ticket |
|---|---|---|---|
| Vitalício | 8.766 | R$20,3M | R$2.300 |
| Assinaturas novas (= bundle) | 27.505 | R$4,9M | R$155 |
| Renovações | 8.745 | R$2,8M | R$323 |
| Mecenas | 215 | R$1,1M | R$5.186 |
| **TOTAL** | — | **R$29,2M** | — |

**Ticket Vitalício por tier (BPDay 2025):** Black 1.620 / R$4.822 · Premium GBB 2.508 / R$2.463 · Básico 2.515 / R$1.549 · Apoiador 2.182 / R$1.105 · ponderado R$2.300. ☑️

**Baseline sazonal Jul-Ago 2025:** Jul R$20,2M (Vit R$13,6M, renov R$2,1M, 26.449 compradores) · Ago R$15,1M (Vit R$3,7M, renov R$4,0M, 30.733). Total R$35,3M. ☑️

**Sustenta:** §1 (âncora), §7 (forecast).

---

## 5. DESCOBERTA ① — a receita não vem dos leads

**Fonte:** compradores de Vitalício no BPDay 2025 cruzados com `dtm_analytics_lead_conversion` (flag lead VIT / qualquer lead / nunca lead). ✅ (re-validado: 962 / 3.229 / 4.575; 9,4% / 36,4% / 54,2%)

| Origem do comprador | Compradores | Receita | % receita |
|---|---|---|---|
| Lead da campanha Vitalício (VIT) | 962 | R$1,9M | 9,4% |
| Lead de outra campanha | 3.229 | R$7,4M | 36,4% |
| NUNCA se cadastrou como lead | 4.575 | R$11,0M | 54,2% |

⚠️ **Ressalva do analista:** a tag "VIT" só existe a partir de jun/2025, então "Lead VIT 9,4%" subestima (quem foi lead de Vitalício em BF23/BF24 cai em "outra"/"nunca"). **O número robusto é a partição binária lead/não-lead** (54,2% nunca foi lead nenhum, sobre 6M de registros e 144 tags). A conclusão se sustenta nesse corte.

**Sustenta:** §2-① (54% sem lead), tese "base é o motor".

---

## 6. DESCOBERTA ② — qualidade e oferta dirigem receita, não volume

**Fonte:** série mensal `dtm_analytics_lead_conversion` (leads) × `fct_transactions` (receita), 2023-2026. ✅ (re-validado pelo analista)

| Correlação | Reportado | Re-validado | Nota |
|---|---|---|---|
| Leads × receita (mesmo mês) | −0,04 | −0,04 (p=0,80) | ruído; +0,40 ao remover outliers de BF; confundido (aquecimento e venda em meses diferentes) |
| Leads(T) × receita(T+1), lag | +0,28 | **+0,37 (p=0,019)** | positivo e **significativo**; Spearman +0,59 |
| Receita/lead × conversão | +0,81 | +0,81 | qualidade manda |

**Por campanha (37 campanhas):** leads×receita +0,345 · leads×conversão −0,231 · receita/lead×conversão +0,807. ☑️

⚠️ **Correção aplicada ao relatório:** a versão antiga dizia "volume não traciona receita" (categórico). O correto: **aquecer rende, com defasagem (+0,37), desde que o lead tenha qualidade**. O teto de gasto frio é por eficiência/CM, não por "tráfego não adiantar".

**Prova de apoio:** Black Friday 2024 fez R$40,3M com 17,5k leads; documentários (DOM/ELS) captaram 233k/218k leads e fizeram R$9-11M.

**Sustenta:** §2-② (reescrito).

---

## 7. Conversão histórica por campanha (>20k leads, 2024-2026)

**Fonte:** `dtm_analytics_lead_conversion` agregado por nm_tag. ☑️

| Campanha | Leads | Conversão | Receita/lead | Tipo |
|---|---|---|---|---|
| TLR (Teller) 2025 | 66.207 | 18,2% | R$118 | produto/base |
| VIT (Vitalício) 2025 | 67.904 | 17,0% | R$100 | produto/base |
| BIT (Bitcoin) 2025 | 69.162 | 12,2% | R$74 | produto/base |
| UNI 2024 | 100.929 | 12,0% | R$44 | misto |
| ISR 2024 | 219.655 | 7,9% | R$26 | documentário |
| NTL24 2024 | 98.354 | 8,0% | R$26 | documentário |
| MST 2025 | 127.691 | 5,5% | R$18 | documentário |
| GOD 2025 | 72.579 | 6,5% | R$22 | documentário |
| RIO 2025 | 220.280 | 3,8% | R$10 | documentário |
| BMA 2026 | 190.491 | 4,3% | R$11 | documentário |
| DOM 2026 | 233.082 | 2,0% | R$5 | documentário |
| ELS 2025 | 218.327 | 1,4% | R$3,6 | documentário |

**Faixas:** documentário/frio 1,4-8% (R$3-26/lead); produto/base 12-18% (R$74-118/lead).

**Sustenta:** §1 (histórico), §2-② (qualidade manda).

---

## 8. DESCOBERTA central de canal — base vs frio (VIT e BIT)

**Fonte:** `dtm_analytics_lead_conversion`, status do membro no cadastro. ✅ (economia VIT re-validada: BASE 38,12% / R$240; FRIO 4,03% / R$15)

**Vitalício (tag VIT 2025, 67.904 leads, R$6,81M rastreável):**

| Grupo | Leads | Conversão | Receita | Receita/lead |
|---|---|---|---|---|
| BASE (membro/ex-membro) | 25.828 (38%) | 38,09% | R$6,19M (91%) | R$240 |
| FRIO (Não Membro) | 42.076 (62%) | 4,03% | R$618k (9%) | R$15 |

**Por canal de lead (VIT):** CRM/base própria 8.769 → 42,96% → R$330/lead · Pago 48.860 → 11,83% → R$50/lead · Orgânico 10.275 → 19,36% → R$144/lead. ☑️

**Bitcoin "A Nova Moeda" (BIT 2025, sucesso +61% ROI):**

| Grupo | Leads | Conversão | Receita | Receita/lead |
|---|---|---|---|---|
| BASE | 20.681 (30%) | 30,61% | R$4,39M (85%) | R$212 |
| FRIO | 48.481 (70%) | 4,36% | R$742k (15%) | R$15 |

- 99,4% dos leads BIT captados no aquecimento (68.772 de 69.162; só 95 na janela de venda). ☑️
- Status BIT: Não Membro 48.481/4,36% · Membro Ativo 13.172/38,13% · Ex-Membro 5.985/14,5% · MA Vitalício 1.524/28,81%. ☑️

**Bitcoin 2.0 "Congresso" (DBI 2026, fracasso −47% ROI):**
- PAGO 25.311 / 3,52% / R$10/lead · ORG 878 / 5,69% · **CRM = ZERO leads**. ☑️
- Só 16,5% de base; Membro Ativo converteu 13,53% (metade do BIT). ☑️

**Sustenta:** §4 (perfis das frentes), §8 (KPI mix base ≥35%), §9 Risco 2 (risco "DBI").

---

## 9. Mix de canal do aquecimento (BPDay 2025)

**Fonte:** `bp-lake.marketing.lead_registration`, janela 07-21/jun/2025 (campo ts_registered_at). ☑️

- facebook_ads: 53.463 (45.760 únicos) · youtube_ads: 2.647 · paid_publi: 329 → **~65% pago**
- email/insider: 6.990 · in_app: 2.081 · web_push: 157 → **~11% CRM**
- organic_social/instagram: 15.134 (8.183) · portal/outros orgânicos ~1k → **~19% orgânico**
- sem atribuição: 4.712
- **Total: ~69k leads (BPDay 2025 aquecimento).**

**Sustenta:** §5 (referência de mix), §6 (estratégia de canais).

---

## 10. CPL e economia do bundle (frente de aquisição)

**CPL — não há número de aquecimento isolado confiável:**
- Benchmark Meta ago-dez/2025 (único período com spend confiável): R$11,89M / 421.969 leads = **R$28/lead blended** (R$52/lead novo). ☑️ ⚠️ Mistura spend de venda + aquecimento de várias campanhas — **não é CPL de aquecimento**.
- **CPL de assinatura = R$3** ⚠️ input do time de mídia (revisão de mídia recomenda planejar R$4-7, R$3 é piso otimista).

**Economia do bundle (análogo CDL):** ⚠️ análogo
- Conversão: 1,44% frio / 8,8% base.
- Ticket do bundle = ticket de assinatura atual mantido (rebranding) ≈ R$155-195 ⚠️ confirmado pela gestão (sem uplift).
- **Receita/lead frio corrigida = 1,44% × R$195 = R$2,8** (NÃO R$13,9 — esse número carregava o ticket do CDL de R$1.218, erro corrigido). Base: 8,8% × R$195 = R$17.

**Sustenta:** §4 (ticket/receita-lead bundle — corrigido p/ R$2,8), §6 (orçamento por CPL), §11 Adendo (validar LTV/retenção e CPL real).

---

## 11. Premissas de gestão (não medidas nos dados)

| Premissa | Origem | Status |
|---|---|---|
| Meta R$15M = R$8M jul + R$7M ago, a 55% CM | Gestora (Bárbara) | ⚠️ definição |
| Evento 16/jul/2026 | Gestora | ⚠️ |
| Bundle = rebranding dos planos atuais, ticket mantido | Gestora | ⚠️ confirmado |
| Parcelamento 18x NÃO é risco de CM | Gestora | ⚠️ confirmado (diretor de receita pede evidência numérica como auditoria) |
| CPL de assinatura ~R$3 | Time de mídia | ⚠️ input (mídia recomenda planejar R$4-7) |

---

## 12. Lacunas conhecidas (apontadas na revisão)

- **Conversão por nº de exposições** (fresco vs 3×-exposto) — não medida; calibraria o teto do Vitalício. 🔲
- **Curva de retenção / LTV do bundle** — não existe; gateia o budget frio (CAC×LTV). 🔲
- **Capacidade/entregabilidade real de CRM** sobre a base 9m+ — premissa #1, não medida. 🔲
- **Custo efetivo de parcelamento por tier** — declarado não-risco, sem número de auditoria. 🔲

---

## Mapa rápido: afirmação do relatório → evidência

| Afirmação (index.html) | Seção desta evidência |
|---|---|
| Base 623,6k / elegível 558,3k / 9m+ 383,4k | §1 |
| 99% da base já viu a oferta; fluxo 99k/6m | §2 |
| Conversão Vitalício por faixa (saturada) | §3 |
| Âncora BPDay 2025 = R$29,2M | §4 |
| 54% da receita de Vitalício sem lead | §5 |
| Qualidade/oferta dirigem receita (lag +0,37) | §6 |
| Conversão 1,4-18% por tipo de campanha | §7 |
| Base converte 38% / frio 4%; mix ≥35% (BIT vs DBI) | §8 |
| Mix de canal ~65% pago / 11% CRM / 19% orgânico | §9 |
| Ticket bundle R$155-195; receita/lead frio R$2,8 | §10 |
| Meta, CM, 18x, CPL R$3 | §11 |
| Pendências de validação | §12 |

---

*Compilado em 16/jun/2026 a partir de todas as queries da análise. Itens ✅ foram re-rodados e confirmados na revisão independente do analista de dados; ☑️ rodados uma vez; ⚠️ são premissas/inputs/análogos, não medições diretas.*
