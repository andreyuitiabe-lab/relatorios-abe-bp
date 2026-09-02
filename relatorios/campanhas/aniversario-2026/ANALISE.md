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

---

# Análise 3: Validação de bônus — reembolsos por upgrade (18 ago/2026)

## Pergunta original
A lista de compradores das ofertas com bônus (enviada aos parceiros) exclui vendas reembolsadas — mas reembolso causado por **upgrade** não pode tirar o bônus: a pessoa fechou dentro do prazo (algumas ondas de bônus terminaram em 17/08). Quais vendas reembolsadas devem voltar para a lista?

## Decisões de abordagem
- **Ofertas/janelas/bônus**: planilha "Ofertas + Bônus Aniv26" (`1hbYANEwbHFvhmyFGjkQBe075BinM5C6njvzkakDYp8M`, gid=0), 90 ofertas, extraída em 18/08. O `Oferta na Guru` (UUID) casa direto com `fct_transactions.id_offer`; a mesma oferta aparece em várias ondas com janelas e bônus diferentes → o join usa `id_offer` + `dt_ordered_at BETWEEN início AND fim`.
- **Critério de upgrade**: não confiar só no `tx_refund_reason` do `financial.fct_charges` (texto livre, inconsistente). O critério é **existir compra aprovada posterior da mesma pessoa** — mesma conta OU mesmo email/CPF/telefone via `dim_contact` (multi-conta). O motivo do reembolso vem junto como evidência de apoio.
- Inclui `partially_refunded` (reembolso solicitado) além de `refunded`.

## Achados principais (run 18/08/2026)
- **132 vendas reembolsadas** de ofertas com bônus dentro das janelas.
- **94 têm compra aprovada posterior (92 pessoas) → mantêm o bônus.** Motivos: upgrade (32), duplicated subscription (30), intencional (15), nova venda/Nova venda/nova compra (15).
- **38 sem compra posterior** → reembolso real, sem direito (31 "intencional").
- ⚠️ `bl_tem_upgrade` = "tem compra aprovada posterior" — inclui casos em que a nova compra é mais barata. A coluna `nm_tipo_troca` classifica: **upgrade (54) / mesmo plano (22) / troca equivalente (4) / downgrade (14)**. Os 14 downgrades (ex: Vitalício → assinatura Básico) merecem decisão humana se o bônus for atrelado ao tier. `lk_guru` traz o link do contato na Guru para conferência.

## Queries

| Query | O quê |
|---|---|
| [12_bonus_reembolso_upgrade.sql](queries/12_bonus_reembolso_upgrade.sql) | Vendas reembolsadas das ofertas com bônus + flag de upgrade (compra aprovada posterior da mesma pessoa) + contato/motivo/detalhe do upgrade |

## Pendências
- **Re-rodar antes de fechar a lista dos parceiros**: upgrades da semana de 18–22/08 ainda vão gerar reembolsos novos de compras feitas até 17/08.
- Output tem PII (nome/email/CPF/telefone) → entregar fora do repo, nunca commitar.

## Wiki atualizada
- `wiki-bp/pages/bq-regras.md` — valores observados de `tx_refund_reason` e padrão de validação reembolso-por-upgrade

---

# Análise 4: Lista COMPRA NEGADA + ABANDONO de Vitalícios BP10 (02 set/2026)

## Pergunta original
Pedido do Comercial (Slack, prazo 13h): lista de compra negada e abandono de carrinho de **Vitalícios da campanha BP 10 Anos**, com coluna de plano e valor tentado. Exclusões pedidas: (1) quem pediu para sair das comunicações, (2) contatos abertos com o Comercial, (3) tentativas via link de vendedor, (4) membros CEC/Mecenas/Retiro/Fundador Big Picture/Clube do Livro, (5) carteira Comercial.

## Decisões de abordagem
- **Atribuição BP10**: checkout `%bp-10-anos%` OU UTM `[BP10]`/`lan_bp10%`, desde 11/06/2026 (início do aquecimento — cobre a pré-venda `lan_bp10_pre_venda`).
- **Vitalício**: `LOWER(nm_gateway_product) LIKE '%vital%'` — todos os produtos vitalícios do checkout BP10 contêm "Vitalício" no nome; evita a contaminação do combo Odisseia+Travessia (`bl_lifetime_offer=TRUE` sem ser vitalício) e separa dos planos anuais vendidos no mesmo checkout.
- **Tipos**: `canceled` = COMPRA NEGADA (168) · `abandoned` = ABANDONO DE CARRINHO (346) · `expired`/`billet_printed` = PIX/BOLETO GERADO E NÃO PAGO (128, rótulo próprio para o Comercial filtrar). `waiting_payment` fora (ainda pode pagar sozinho).
- **Link de vendedor** (exclusão 3): pessoa excluída inteira se qualquer tentativa BP10 tem `bl_is_commercial_channel`, `nm_salesman` ou produto `Comercial -%`.
- **Contato aberto** (exclusão 2): `dim_zenvia_contacts` não-archived + `TRIM(nm_group)='Comercial'` (definição validada em ago/26, não a CTE followUp) + Pipedrive `OPEN`.
- **Carteira** (exclusão 5): `nm_stage='carteiraMecenas'` não-archived (definição padrão da wiki).
- **Blacklist** (exclusão 1): snapshot `tb_blacklist_crm_snapshot` de 26/08 — validado contra o Drive (planilha modificada 25/08, snapshot posterior → em dia).
- **Por zelo (implícito)**: excluído quem **já tem vitalício aprovado** — 1.334 contas do universo concluíram a compra depois da recusa/abandono.
- 1 linha por pessoa (dedup triple-key), priorizando negada > pix/boleto > abandono, depois a mais recente; `qt_tentativas` mostra reincidência.

## Achados principais (run 02/09/2026)
- **642 pessoas** na lista final: 346 abandono (R$ 496k tentados), 168 negada (R$ 240k), 128 pix/boleto não pago (R$ 193k) — **R$ 930k em tentativas recuperáveis**.
- Funil: 3.776 contas com tentativa → −602 via link de vendedor → 3.171 elegíveis → exclusões (com sobreposição): **Zenvia aberto com Comercial 2.169 (68%!)**, já tem vitalício 1.334 (42%), carteira 789, CDL 98, Pipedrive 46, Mecenas 32, CEC/Retiro/Fundador 2, blacklist 0.
- Leitura: a maior parte dos carrinhos BP10 **já está sendo trabalhada pelo Comercial** — a lista entrega justamente o resíduo que ninguém está cobrindo.
- Planos tentados: Premium GBB Vitalício 316 · Básico Vitalício 170 · Originais Vitalício (label Apoiador) 156.

## Queries

| Query | O quê |
|---|---|
| [13_lista_negada_abandono_vitalicio.sql](queries/13_lista_negada_abandono_vitalicio.sql) | Lista completa com todas as exclusões — 1 linha/pessoa, plano+valor+parcelas+motivo da recusa |

## Pendências
- Output tem PII → CSV/XLSX entregues fora do repo (scratchpad da sessão). Se pedirem refresh, re-rodar a query 13 (tentativas de hoje entram; quem comprar depois sai sozinho pela exclusão de vitalício aprovado).
