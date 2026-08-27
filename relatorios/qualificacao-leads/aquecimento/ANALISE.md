# Aquecimento · Qualidade — acompanhamento da captação por campanha (IQL + RPL)

**Data:** 26–27/08/2026 · **Status:** passo 1 de 3 entregue (5 campanhas) (camada "Decidir" viva) · **Pai:** [../ANALISE.md](../ANALISE.md) (IQL) · mockup aprovado: artifact `a3fd60ec`

## Pergunta original

André (26/08): "implementar um novo jeito do time de marketing acompanhar as métricas de aquecimento
para melhorar processos e performance" — % de leads bons, CPL, ROAS potencial. As métricas já
estavam desenhadas (mockup v3 + D52); o que faltava era o **sistema de acompanhamento**: quem olha o
quê, quando, e como separar sinal de ruído.

## Plano acordado (3 passos)

| Passo | O quê | Status |
|---|---|---|
| 1 | **Camada Decidir** (mídia, diário): mockup v3 com dados vivos — hero de retorno esperado, régua CPL → CPL máx → RPL, leads/dia por faixa, retorno/dia, pacing realizado × esperado, top anúncios, personas, benchmark | ✅ 26/08 — esta pasta |
| 2 | **Camada Vigiar** (gestão, semanal): inputs controláveis com alvo (cobertura da pesquisa, % do gasto acima da meta, taxa de resposta, share do budget em "escalar") + outputs com **banda de controle** (XmR) + leitura piso–teto quando cobertura de pesquisa difere + seção de cadência | 🔲 |
| 3 | Validar 2 semanas com o time (ENE/JOM); critério: ≥1 realocação registrada usando retorno esperado (D22) + time explica o bloco Vigiar sozinho → portar para marketing-bp (sub-aba Qualidade do grupo Aquecimento, molde PR #110/#106) | 🔲 |

Literatura que embasa o desenho (resumo na conversa de 26/08): input vs output metrics (Amazon WBR);
SPC/XmR — reagir a variação comum é *tampering*; monitoramento de scorecard (Siddiqi: PSI,
characteristic stability); Goodhart — parear eficiência com qualidade (NM-A/R$ como guardrail);
CPQL > CPL e fechar o loop com a plataforma (value-based bidding = CAPI com valor, D54).

## Decisões de abordagem

- **Portal HTML primeiro, marketing-bp depois** (André, 26/08) — validar o modelo de acompanhamento com dados reais antes de codar React/edge fn.
- **Pasta própria** `qualificacao-leads/aquecimento/` (não evoluir `iql/`): o `iql/` é o dashboard analítico (camada Aprender); esta é a página operacional. Padrão template: `index.html` + `data.json` + `refresh.py` + `queries/`.
- **Métrica-mestra = retorno esperado = RPL projetado ÷ CPL, meta 1,5×** (D52). RPL projetado vem de `cbo_campaign_rpl_estimate` (projetor por janela — D53). CPL máximo = RPL ÷ 1,5.
- **Retorno por dia e por anúncio** usa `vl_capi_event_value` (EV da faixa × fator da campanha, D54) — o mesmo valor que vai para a Meta, então a página e o Gerenciador falam o mesmo número.
- **Spend blendado** = todo `[LEAD]` Meta + Google + PMax cuja sigla (2º colchete) = tag (mesma regra da `vw_cpl_lead_campanha`), a partir do `dt_inicio` da campanha. Leads = todos da tag desde `dt_inicio` (tags reusadas: JOM desde 25/07).
- **Pacing por coortes**: esperado(t) = Σ coortes diárias × curva de receita acumulada por idade do lead. Curva = **mediana entre EVG, BP10, DOM, ELB26**, só compras **antes da abertura de venda** (ELB26 nunca abriu → todas), horizonte 60 dias; faixa = min–máx entre as 4. ⚠️ Difere do mockup de 04/08 (que dava ENE em 36% do esperado): com esta curva documentada e reproduzível a ENE está em **114%** em 26/08. A curva do mockup não estava documentada — esta é a canônica a partir de agora.
- **Campanhas na página (27/08):** ENE, EVG, BP10, ELB26, JOM — todas as que tiveram pesquisa in-funnel. Config `CAMPANHAS` ganhou `tipo` (aberto/fechado): em lançamento **fechado** a curva esperada do pacing só vale até a abertura da venda — o veredito (`pacing_ref`) é lido no último dia do aquecimento e o gráfico marca a abertura; em **aberto** (ENE, venda direta) a curva vale inteira. Pré-abertura: EVG 216% e BP10 271% do esperado (pré-venda forte), ELB26 104%, JOM 66%, ENE 121%.
- **Leitura comparável** (iql.md): o hero mostra o "teto comparável" (EV dos respondentes aplicado a todos) ao lado do retorno observado quando a cobertura de pesquisa < 90%. Falta aplicar por anúncio (passo 2).
- **Personas** dos A+/A por cascata: base reimpactada (status ≠ NM) → veterano (mais_3a) → descobridor (6m_a_3a) → recém-chegado (≤6m) → sem pesquisa. Conversão com <5 vendas não mostra % (D18).
- **Benchmark** exclui tags com spend por >75 dias (sempre-ativas/LP: TLR12 com CPL R$ 0,19 etc. não são comparáveis).
- Pesquisa respondida = `ARRAY_LENGTH(arr_survey_responses) > 0` no cbo (o `nm_survey_response_level` só existe no `fct_lead_iql`).
- Governança D20: `refresh.py` faz assert de que nenhuma chave de pesos/WOE entra no `data.json`.

## Achados (26/08)

- **ENE**: 15.432 leads · CPL R$ 1,19 (spend só até 06/08 — mídia parou; leads seguiram por CRM/orgânico) · A+/A 31,8% (47,9% entre respondentes; cobertura 57%) · RPL projetado R$ 11,98 (D+7 ancorado, ±23%) · **retorno esperado 10,1×** (teto comparável 12,3×) · CPL máximo R$ 7,99 · realizado R$ 48k / 227 vendas · pacing 114% do esperado. Todos os 8 anúncios com n≥50 estão ≥ 3,5× — nenhum para cortar; o problema da ENE nunca foi a mídia.
- **JOM**: 10.826 leads desde 25/07 · CPL R$ 3,56 · A+/A 29,1% (41,4% entre respondentes) · RPL R$ 8,45 **sem âncora** (`ev_iql`, ±35% — a tag reusada não fecha janela) · retorno 2,4× · pacing 70% (abaixo do esperado, dentro da faixa min) · ROAS realizado 0,38× — venda não abriu.
- Curva de referência: R$ 0,90/lead no dia 0 → R$ 1,89 (D+9) → R$ 2,95 (D+29) → platô R$ 3,05 (D+40+), pré-abertura.

## Pendências / próximos passos

1. **Passo 2 — camada Vigiar** (ver plano). Banda de controle XmR sobre `serie[].vl_retorno_esp` e `pacing[]`; bloco de inputs com alvo; leitura piso–teto por anúncio; seção "cadência" (mídia diário / gestão segunda-feira / analytics no fechamento).
2. ~~Publicar no portal~~ ✅ 26/08 (card na seção IQL); atualizado 27/08 com 5 campanhas.
3. Spend da ENE parou em 06/08 nas planilhas Adveronix — confirmar com a mídia se a campanha foi pausada ou se é lacuna de dado.
4. JOM: PMax `[LAN] [JOM] [LEAD] [PMAX] Junho` clonada com URL da ENE (meta-insider-ads.md) — parte do spend JOM gerou leads ENE; CPL JOM levemente superestimado e ENE subestimado. Não corrigido aqui.
5. Quando validado → marketing-bp (fix da regex `__(\d+)$` na `fetch-leads-attribution` junto).

## Queries

| Arquivo | O quê |
|---|---|
| [queries/resumo_campanha.sql](queries/resumo_campanha.sql) | Uma linha por campanha: leads, spend blendado, CPL, qualidade (geral e entre respondentes), receita observada, projeção do RPL |
| [queries/serie_diaria.sql](queries/serie_diaria.sql) | Leads por faixa, spend, CPL e retorno esperado por dia |
| [queries/ads.sql](queries/ads.sql) | Anúncios Meta com spend: mix de faixas, CPL, RPL esperado, retorno, vendas |
| [queries/curva_referencia.sql](queries/curva_referencia.sql) | Curva de receita acumulada por idade do lead (mediana de 4 campanhas, pré-abertura) |
| [queries/pacing_realizado.sql](queries/pacing_realizado.sql) | Receita realizada acumulada por data da compra |
| [queries/personas.sql](queries/personas.sql) | Cascata de personas entre A+/A |
| [queries/benchmark.sql](queries/benchmark.sql) | Retorno projetado por campanha (≥5k leads, spend desde ago/2025) |
| [queries/faixas.sql](queries/faixas.sql) | EV por faixa (`dim_iql_cutoffs`) |

Parâmetros `tag`/`dt_inicio` são `DECLARE`s substituídos pelo `refresh.py` (config `CAMPANHAS`). Campanha nova = 1 linha na config.

## Para retomar

- **Próximo passo:** passo 2 — em `refresh.py`, calcular banda XmR (média móvel + 2,66×MR̄) da série de retorno e do pacing; adicionar bloco `vigiar` no data.json com os 4 inputs e alvos; em `index.html`, card "Vigiar" abaixo do hero + seção "Cadência".
- **Wiki a carregar:** `wiki-bp/pages/iql.md` (leitura comparável, governança) → este ANALISE → `../ANALISE.md` §Operacionalização (plano marketing-bp).
- **Queries:** todas ✅ rodaram em 26/08 (`refresh.py` ~1m20s).
- **Contexto fora da wiki:** servidor local para ver a página: `python3 -m http.server 8765` na pasta; screenshot com Chrome headless (ver histórico da sessão de 26/08). Modo escuro é o default do headless.
