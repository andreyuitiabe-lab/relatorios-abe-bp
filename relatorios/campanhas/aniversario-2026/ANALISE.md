# Análise: Meta de Leads — Campanha Aniversário 2026

**Data:** 15 jun/2026 | **Analista:** André Abe

---

## Pergunta original
Qual é a meta de leads de aquecimento para atingir R$15M na campanha de aniversário (Vitalício + rebranding de assinaturas)?

## Decisões de abordagem

- **Receita histórica:** usei `fct_transactions` com janelas de datas por campanha (UTM não disponível para BPDay, usei janela temporal)
- **Aquecimento:** `bp-lake.marketing.lead_registration`, campo de data `ts_registered_at` (TIMESTAMP). Há também `dt_regristered_at` (STRING, com typo) — usar `ts_registered_at`.
- **Base ativa elegível:** `dim_subscriptions` (active/wo renewal/paid) + fct_transactions (bl_lifetime_offer) para total, depois excluindo quem já tem Vitalício
- **Maturidade:** calculada como `DATE_DIFF(CURRENT_DATE, DATE(dt_primeira_compra), MONTH)` onde `dt_primeira_compra` é o MIN de `fct_transactions` (approved)
- **Ticket médio Vitalício:** ponderado pelo mix de tiers do BPDay 2025 = R$2.300

## Achados principais

- **Base ativa Jun/2026:** 623.604 membros totais, 558.337 elegíveis para Vitalício
- **24m+:** 232.498 membros (dos quais 181.308 ainda sem Vitalício — 22% já converteram)
- **BPDay 2025 (referência primária):** R$29,2M total, R$20,3M Vitalício, 69.531 leads de aquecimento, R$420/lead (taxa blended)
- **Meta de R$15M é conservadora:** cenário pessimista da base sozinha (sem aquecimento) já projeta R$15M
- **Meta de leads recomendada:** 60.000 leads únicos no aquecimento, projeta R$34-35M total
- **Risco principal:** saturação da faixa 24m+ (22% já converteram, conversão caiu de 12,93% BF23 para 6,28% BF24)
- **Incógnita crítica:** rebranding de assinaturas — sem histórico, premissa de R$5,5M (realista) é especulativa

## Pendências / próximos passos

- Validar mix de tier esperado para BPDay 2026 (se Black Vitalício será promovido com mais agressividade)
- Definir datas exatas de aquecimento e venda para confirmar janela
- Modelar estratégia do Comercial separadamente (contribuição relevante pós-Vitalício)
- Após primeiros dias de venda: recalibrar conversão por faixa com dados reais

## Queries

| Arquivo | O que faz | Status |
|---|---|---|
| [01_base_ativa_maturidade.sql](queries/01_base_ativa_maturidade.sql) | Base ativa total por faixa | ✅ rodou |
| [02_base_elegivel_vitalicio.sql](queries/02_base_elegivel_vitalicio.sql) | Base elegível (sem Vitalício) | ✅ rodou |
| [03_receita_historica_campanhas.sql](queries/03_receita_historica_campanhas.sql) | Receita por campanha histórica | ✅ rodou |
| [04_aquecimento_leads.sql](queries/04_aquecimento_leads.sql) | Leads de aquecimento BPDay 24/25 | ✅ rodou |
| [05_vitalicio_tier_campanha.sql](queries/05_vitalicio_tier_campanha.sql) | Ticket médio Vitalício por tier e campanha | ✅ rodou |

## Wiki atualizada

- `metricas-referencia.md` — adicionado BPDay 2025 e BF 2023/2024 receita/leads
- `dbt-fct-leads-events.md` — adicionado nota sobre campos de data da `lead_registration`
- `vitalicio.md` — achados de saturação e composição do 24m+

---

# Análise 2: Perfil dos compradores BP10 (31 jul/2026 — campanha em aberto)

## Pergunta original
Quem está comprando na BP10, por produto: membros novos, ex-membros ou ativos? Se cadastraram em outras campanhas (quais)? O que já tinham comprado?

## Decisões de abordagem

- **Atribuição**: replicada a regra do dashboard de campanhas (UTM `bp10`/`vit`, tracking `BP10`, caminhos `anos`/`aniversario`/`10`), **com correção**: `10` só como segmento de caminho. A regra original (contains) casa com o tier `[10r]` (Apoiador R$10) e infla ~8k+ vendas de outros funis (combos ELS, EVG, CDL, `[10r] seja-membro`). ⚠️ Provável bug no dashboard — reportar.
- **Janela**: `dt_ordered_at >= 2026-06-11` (início do aquecimento), approved, sem renovações.
- **Classificação por email** — padrão canônico de `queries-referencia.md` §"status do membro no momento da compra" (join `dim_user` → `dim_subscriptions`, operador `>` estrito porque o checkout BP10 vende assinatura junto):
  - *Membro ativo* = assinatura paga iniciada ANTES da compra e cobrindo a data, ou vitalício prévio (`nm_subscription_recurrence = 'vitalício'`)
  - *Ex-membro* = teve assinatura iniciada antes, nenhuma cobrindo a data
  - *Não era membro* = nunca teve assinatura paga
  - ⚠️ **Correção (31/07 tarde):** a 1ª versão usava status atual + `dt_started_at <= compra` — a assinatura criada pelo próprio checkout contava como "ativo" e "novo" era qualquer pessoa sem tx prévia. Isso subestimava ex-membros para ~1%; o correto é **24%**.
- **Leads**: `dtm_analytics_lead_conversion` por email; tag BP10 vs outras tags com cadastro anterior à compra.

## Achados principais

- **Cohort: 3.481 compradores, ~R$3,02M** (11/06→30/07). Vitalício = 36% dos compradores e **69% da receita** (R$2,06M).
- **Status na compra (não era / ativo / ex)**: cohort inteiro **41 / 35 / 24**. Por produto: Vitalício 30/48/22 · Mecenas 5/95/0 · Clube do Livro 10/75/15 · Assinaturas 55/21/25.
- **Ex-membros = 24% do cohort (838 pessoas)** — a campanha reativa churned de verdade. Destaques: Assinatura Premium **36% ex**, Vitalício Básico 26%, Vitalício Premium 23%. Mecenas e Black Vit não reativam (0–6%).
- **Vitalício Black é o mais "base"**: 86% ativos, ticket R$3,7k, só 8% nunca-membros. Premium (R$958k) e Básico (R$573k) Vit têm ~32–34% de nunca-membros + ~1/4 de ex — porta de aquisição E de reativação.
- **Leads**: 40% dos compradores nunca foram lead de nenhuma campanha (Vitalício: **53%** — venda direta via CRM/base, coerente com `[VIT]`). Só 24% se cadastraram na LP da BP10.
- **Cadastros prévios pulverizados**: lp-principal (6,9%), VIT (5,9%), EVG (5,8%), TLR (5,5%), RBP (4,9%), BMA (4,7%) — nenhuma campanha domina a origem.
- **Socioeconômico (vs base ativa)**: demografia idêntica (masc 61,2/60,7 · região igual · idade madura, +2pp em 65+); o que distingue é poder de compra — decil 7+ 45,9% vs 42,5%, cartão premium 63,1% vs 57,2%, black 36,7% vs 30,3%.
- **Compras prévias** (não-novos): Básico 1.045, Premium GBB 584, Apoiador 479, Patriota 479, Núcleo 275; **243 já tinham outro vitalício** e recompraram; 90 eram Mecenas.

## Queries

| Query | O quê |
|---|---|
| [06_perfil_compradores_bp10.sql](queries/06_perfil_compradores_bp10.sql) | Novo/ativo/ex-membro × produto |
| [07_leads_origem_compradores.sql](queries/07_leads_origem_compradores.sql) | Visão geral de cadastro de leads |
| [08_tags_previas_compradores.sql](queries/08_tags_previas_compradores.sql) | Top campanhas prévias |
| [09_compras_previas.sql](queries/09_compras_previas.sql) | Produtos já comprados antes |
| [10_leads_por_produto.sql](queries/10_leads_por_produto.sql) | Origem de cadastro × produto |
| [11_perfil_socioeconomico.sql](queries/11_perfil_socioeconomico.sql) | Gênero, idade, região, renda, cartão — BP10 vs base ativa |

## Relatório
- [perfil-compradores/index.html](perfil-compradores/index.html) — página HTML no padrão do relatório El Salvador (KPIs, composição novo/ativo/ex por produto, origem de cadastro, compras prévias, conclusões). Snapshot 31/07, dados hardcoded — re-gerar no fechamento da campanha.

## Wiki atualizada
- `wiki-bp/pages/metricas-referencia.md` — seção "BP10 — perfil dos compradores" (números + gotcha da atribuição `[10r]`)

## Pendências
- Reportar ao dono do dashboard de campanhas o falso positivo da regra "Caminhos: 10" (casa com tier `[10r]`).
- Campanha em aberto — números crescem; re-rodar no fechamento.
