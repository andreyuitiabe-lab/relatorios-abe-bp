# Otimização por evento de resposta — CPL, custo/resposta e conversão

## Pergunta original
Como estão o CPL e o custo por resposta de cada campanha do Facebook Ads, comparando
as campanhas **otimizadas por evento de resposta** com as demais — e ao longo do tempo,
relacionando com a **conversão (lead→venda) como um todo** de cada campanha.

Hipótese do solicitante: a campanha otimizada por evento de resposta deveria **aprender
e ganhar eficiência ao longo do tempo**.

## Decisões de abordagem
- **"Otimizada por evento de resposta" = campanhas de LEAD com `Lead Survey` no nome**
  (ex: `[LAN] [EVG] [LEAD] [ADVANTAGE] Brasil | Evento Lead Survey`). O evento otimizado
  é a resposta da pesquisa de qualificação. **Dois lançamentos rodam o experimento: EVG e BP10.**
- **Comparação justa = dentro de cada lançamento.** A taxa de resposta acompanha o lançamento
  ter pesquisa ativa, não a otimização: EVG e BP10 têm 65–84%, enquanto ELS/ABC/DOM/CDL têm 0%
  (não têm pesquisa na landing). Comparar survey vs *todas* as campanhas de LEAD é enganoso.
- **CPL e leads via atribuição last-click:** `lead_conversion.utm_content` → `id_advertising`
  → `nm_campaign_name` no funil Meta. Investimento vem do funil Meta; leads/respostas/vendas
  da `lead_conversion`.
- **⚠️ Gotcha de atribuição (corrigido):** o `utm_content` tem dois formatos — `AD## … __<id>`
  (maioria) e **`<id>` puro (BP10)**. O regex `__([0-9]+)$` perdia 100% dos leads do BP10.
  Trocado por **`([0-9]+)$`**, que cobre os dois e não altera os demais lançamentos
  (match do EVG idêntico: 47.783). Sem isso, o BP10 nem aparecia na análise.
- **Reconciliação com o dash oficial:** o dashboard conta por `nm_tag` (lançamento inteiro,
  todas as campanhas e fontes) — ex: BP10 no dia 26/jun = 1.325 cad / 923 resp / 69,7%.
  Este relatório mede o recorte da campanha `Lead Survey` no facebook, atribuída ao anúncio
  (única forma de separar survey vs base). Cobertura de atribuição verificada: **99,9%** dos
  leads facebook do BP10 casam com um anúncio — não há vazamento. Os números diferem do dash
  por **escopo**, não por erro. O relatório mostra as duas métricas lado a lado.
- **Dias anômalos (data-driven):** dias em que o CTR da campanha survey desaba (&lt;0,5%) são
  detectados automaticamente e marcados em vermelho — não são performance real de mídia e sim
  falha técnica de clique/destino (ver achados). Hoje: BP10 em 26–27/jun.
- **Conversão = compra aprovada em até 30 dias do registro** (`arr_st_approved_transactions`,
  `days_to_purchase BETWEEN 0 AND 30`). CAC = investimento Meta ÷ vendas atribuídas.
- **Curva de aprendizado:** série diária na vida da campanha survey (19–30/jun/2026, 12 dias).
- Métrica norte para qualidade do lead é o **custo por resposta** (não o CPL puro) — ver
  framework de qualificação de leads.

## Achados principais
- **Custo por resposta converge rápido (EVG):** survey cai de **R$ 15,89** no 1º dia para
  **R$ 4–5** já no 3º–4º dia, alcançando o patamar da base (~R$ 4,5). Aprendizado do algoritmo
  confirmado — mas a eficiência **estabiliza no nível do grupo base, não abaixo dele**.
- **Padrão consistente nos dois lançamentos** (agregado 19–30/jun) — survey vs base:
  - **EVG:** CPL R$ 3,96 vs R$ 3,37 (+18%); taxa resp. **83,7% vs 74,8%** (+9 pp);
    custo/resp. R$ 4,73 vs R$ 4,51 (empate); conversão **0,78% vs 0,95%** (pior).
  - **BP10:** CPL R$ 5,88 vs R$ 4,45 (+32%); taxa resp. **77,5% vs 70,9%** (+7 pp);
    custo/resp. **R$ 7,59 vs R$ 6,27 (pior)**; conversão **0,43% vs 0,93%** (pior).
- **Regra geral:** otimizar por evento de resposta sobe a taxa de resposta (+7 a +9 pp), mas
  ao custo de um CPL 18–32% maior. No melhor caso empata o custo/resposta (EVG); no BP10
  fica **pior**. Em nenhum dos dois a conversão em venda melhorou.
- **Por lançamento (120 dias):** os dois lançamentos com pesquisa têm os **piores CAC entre
  os grandes — BP10 R$ 546 e EVG R$ 310**, contra ELS R$ 118 (mais barato) e DOM R$ 225.
  Qualificar via pesquisa não está, hoje, produzindo conversão melhor que os lançamentos sem ela.
- **Pico de custo do BP10 (26–27/jun) = falha técnica, não mídia:** gasto normal (R$ 500) e
  impressões até maiores (24k), mas cliques outbound despencaram de ~240 para 15 (CTR 2,8% → 0,06%).
  Sem clique → sem lead → CPL saltou para R$ 126 e custo/resposta para R$ 253. Assinatura de link
  quebrado / pixel de clique não disparando. Normalizou em 28–29/jun. Marcado como anomalia no relatório.

## Pendências / próximos passos
- **Revisitar conversão do EVG em ~30 dias** (após maturar a janela de compra) para ver se
  a maior qualificação se converte em venda — hoje é cedo demais para concluir.
- Avaliar se vale **escalar o investimento** na campanha survey (hoje só R$ 4k) para teste
  com massa estatística — diferença de 9 pp na taxa de resposta é direcional, não conclusiva.
- Verificar **qualidade das respostas** (renda/intenção) dos leads survey vs padrão, não só volume.

## Queries
| Arquivo | O que faz | Status |
|---|---|---|
| [queries/serie_diaria.sql](queries/serie_diaria.sql) | CPL e custo/resposta diários, survey vs outras EVG | ✅ rodou |
| [queries/conversao_por_lancamento.sql](queries/conversao_por_lancamento.sql) | Invest, CPL, tx. resposta, conv., CAC por lançamento | ✅ rodou |
| [queries/resumo_grupos.sql](queries/resumo_grupos.sql) | Resumo agregado dos dois grupos | ✅ rodou |

## Relatório
- `index.html` + `data.json` + `refresh.py` (padrão de dados externos).
- Atualizar dados: `cd relatorios/evento-resposta && python refresh.py --push`

## Wiki atualizada
- (pendente) `wiki-bp/pages/meta-insider-ads.md` — registrar que `| Lead Survey` no nome marca
  otimização por evento de resposta, e que a taxa de resposta acompanha o lançamento ter pesquisa,
  não a otimização da campanha.
