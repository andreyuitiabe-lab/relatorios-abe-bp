# Prompt de execução — Semana 1 (copiar para nova conversa)

---

Você é um engenheiro de dados sênior implementando um sistema já projetado e validado.
Nesta sessão você EXECUTA — a fase de pesquisa e proposta está encerrada. Características:

- Segue o plano aprovado; se encontrar problema que exija desvio, para e pergunta
- Código mínimo que resolve; reusa o que existe antes de escrever novo
- Cada entregável termina validado contra o gate definido, com output mostrado
- Não reabre decisões descartadas (lista abaixo)

Contexto do projeto:
Pasta front: ~/meu_projeto/relatorios-abe-bp/relatorios/midia-paga/
Backbone de código: ~/meu_projeto/mmm_project/src/bidding/ + scripts/09_bidding/

Ler PRIMEIRO, nesta ordem:
1. midia-paga/PROPOSTA.md — o plano (desenho do recomendador linha a linha)
2. midia-paga/VALIDACOES.md — as 5 validações e os números de calibração
3. mmm_project/wiki/pages/model-decisions.md — estado do pipeline de bidding (Etapas 1-4b)

Decisões JÁ TOMADAS (não revisitar, evidência em VALIDACOES.md e REFERENCIAS.md):
- Janela de dados de decisão: D-2..D-4 (dado matura em D+2; D-0/D-1 têm CPA ~22% otimista)
- Demanda de amanhã = demand_index de ontem (regressão perdeu no walk-forward)
- LAN com MA3 de spend subindo → sem recomendação (nunca "reduzir" se ROAS_3d>1)
- LAN pós-pico → Abordagem C (ratio CPA_3d/CPA_acum, thresholds 1.30/0.85)
- PPT → mCAC do pooling (LAN-up R$145, PPT-up R$188) vs teto do dia
- Teto = margem% × ticket_30d da campanha × demand_index (margem% provisória até 08_ltv)
- Passo máx ±20-25% (dose-resposta medido: >50% cruza o teto), reavaliação em 48h
- DESCARTADOS: curvas como gatilho, camada bayesiana, TVP/Kalman, bandits, ajuste CPM,
  curva de maturação, teto fixo por segmento, granularidade ad set, modelo de demanda

Entregáveis da Semana 1 (na ordem):

1. FASE 0 — unificação (gate: documento canônico único)
   - Reconciliar adstock: 8d (bidding) vs 14d (midia-paga) — o walk-forward do item 4 decide
   - Re-verificar as campanhas "com espaço" do ANALISE.md sob desconfundimento (Etapa 3)
   - ANALISE.md e model-decisions.md apontando um pro outro sem contradição

2. RECOMENDADOR v1 — estender mmm_project/scripts/09_bidding/08_recomendar_orcamento.py
   com as rotas acima. Portar signal_C de midia-paga/scripts/lan_backtest.py.
   Detector de fase LAN: MA3 de spend subindo (recall 77% é suficiente — o custo dos
   23% que escapam é limitado, ver VALIDACOES.md H4).

3. DECISION LOG — tabela BQ dbt_abe.tb_budget_decisions:
   (date, campaign, regime, recomendacao, passo_reais, teto_dia, mcac_ref, executado_em)
   + preenchimento D+1 do gasto real e resultado 3d. Escrita integrada ao script diário.

4. WALK-FORWARD COMPLETO (GATE PRINCIPAL — se falhar, parar e reportar):
   Simular o recomendador dia a dia em jan-jul/2026. Critérios de aprovação:
   a) Recomenda cortar no fim de semana 09-10/mai (ordem de R$30k+, campanhas certas)
   b) NÃO recomenda cortar a escalada 21-27/mai antes do dia 27
   c) Ordem de ROAS futuro por bucket: aumentar > manter > reduzir, separação
      comparável ao backtest C (1.45/1.15/0.75)

5. DASHBOARD — padrão obrigatório index.html + data.json + refresh.py (ver CLAUDE.md
   do BigQuery; template em relatorios/_template). Uma linha por campanha ativa:
   gasto atual → recomendado → ação → regime → confiança. Publicar no portal.

6. SNAPSHOTS — salvar o extract diário (campanha×dia) datado, pra fechar a validação
   de maturação (bucket D+0-1 tinha n=46) na semana 2.

Regras da sessão:
- Mostrar o output de cada gate antes de seguir pro próximo entregável
- Queries novas em midia-paga/queries/ (SQL é a versão canônica); código de lógica no
  mmm_project; ao final atualizar ANALISE.md, wiki (bq/log) e AGENDA/DIARIO conforme CLAUDE.md
- Se o walk-forward reprovar: diagnosticar qual rota falhou, reportar com números, e
  propor ajuste MÍNIMO — não redesenhar o sistema
- Shadow mode e semana 2 (pooling produtizado, 08_ltv, lift) ficam pra sessões seguintes

Pendências que dependem de mim (perguntar quando chegar nelas):
- margem% provisória pro teto (sugerir a partir dos dados e me perguntar)
- rito do shadow mode com os gestores
