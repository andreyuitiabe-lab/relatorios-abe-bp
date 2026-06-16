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
