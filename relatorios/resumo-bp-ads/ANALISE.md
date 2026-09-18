# Resumo BP × BP Ads — Funil da Newsletter por Parceiro

## Pergunta original

Pedido do Elias (via Nicolas Zanirati, #performance-e-bi, 22/jul/2026): dash de acompanhamento
do Resumo BP para passar aos parceiros do BP Ads. Funil da newsletter (enviados, recebidos,
abertos, cliques) com visão consolidada (interna) e visão segmentada por anunciante — cada
parceiro enxerga só os cliques dos links dele.

## Decisões de abordagem

- **Fonte:** `staging.stg_insider__events`, campanhas `[RBP]` (nome `EM5XX - [RBP] [ENG] [CAD] Dia DD/MM`).
  Validado contra a UI do Insider (edição EM522, 14/07): entregues, cliques únicos e cliques
  do anunciante batem **exatos**; aberturas únicas ficam ~6% abaixo (janela de aberturas tardias).
- **Segmentação por parceiro:** `NET.REG_DOMAIN(nm_email_url)` do evento `email_click`.
  Domínios BP/sociais/editoriais são classificados em `refresh.py`; qualquer domínio externo fora
  dessas listas é tratado como anunciante (novos parceiros aparecem sozinhos no dropdown).
- **"Enviados"** ≈ delivered + blocked + dropped + bounce (Insider não expõe evento `sent`; ~1% acima do "Sent" da UI).
- **Duas taxas de abertura:** padrão mercado (~46%, inclui Apple MPP — comparável a benchmarks)
  e humana (`bl_human_open = 1`, ~10% — pessoas reais). O funil usa a humana; KPIs e tabela mostram ambas.
- **Janela:** móvel de **120 dias** (edições com >50k entregues, para excluir testes/reenvios parciais).
  Era 30 dias e estava errado para o caso de uso: anunciante repete a cada ~1 mês, então o parceiro
  via só a última inserção. Com 120 dias, cobre desde o relançamento visual do Resumo BP (23/04) — ~67 edições.
- **Execução das queries:** cliente Python + ADC (`google.cloud.bigquery`), igual ao `~/bin/bqq`.
  Não usar o `bq` CLI no `refresh.py`: o token dele expira e o refresh quebra sem forma de reautenticar.

## Achados principais

- ~390k enviados/edição diária, ~96% de entrega, ~37k aberturas humanas (~10%), 300–3.000 clicadores únicos.
- Cliques concentram em notícias BP (~74% no período inicial analisado); anunciantes ainda são <1% dos cliques.
- Anunciantes já veiculados: Sendflow, Vimansca, Lídio Carraro e **Allugator** (novo, estreou 16/09) — detalhe por inserção na tabela abaixo.
- ⚠️ **Links de anunciante saem sem UTM** (ex.: `vimansca.com.br/` puro). Domínio funciona como
  identificador, mas recomenda-se padronizar `utm_source=resumo_bp&utm_campaign=<parceiro>&utm_content=<edição>`
  para o parceiro medir no analytics dele e para distinguir 2 anúncios do mesmo parceiro na mesma edição.

### Inserções por anunciante (18/set/2026)

| Anunciante | Inserções | Detalhe (pessoas / cliques) |
|---|---|---|
| Vimansca | 8 | 14/07 (69 / 145), 17/08 (98 / 124), 04/09 (84 / 105), 08/09 (68 / 116), 09/09 (39 / 92), 10/09 (58 / 66), 11/09 (40 / 55), 14/09 (32 / 44) |
| **Allugator** | 2 | 16/09 (64 / 92), 17/09 (62 / 75) |
| Lídio Carraro | 1 | 21/08 (141 / 162) |
| Sendflow | 3 | 02/07 (74 / 147), 03/07 (28 / 41), 28/07 (37 / 58) |

Números maiores que os de 14/set nas edições de setembro: cliques tardios continuam entrando por
alguns dias depois do envio.

**Allugator — anunciante novo (18/set):** estreou nas edições de **16 e 17/09**, com o padrão de
inserção contratada — **3 links por edição** para `https://franquias.allugator.com/` (banner, texto
e botão, provavelmente), igual à edição contratada da Vimansca em 04/09. Somam 167 cliques / 126
clicadores nas duas edições. Verificado no mart `cbo_insider_email_analytics_daily` (histórico
completo desde fev/2024): **nunca apareceu antes** — é estreia de verdade, não retorno. Link também
sai **sem UTM**. Cadastrado em `PARCEIROS_NOME` no `refresh.py` (única manutenção manual por
anunciante novo); apareceu sozinho no dropdown e na tabela de destinos, como previsto.

⚠️ **`stf.jus.br` classificado como editorial (18/set):** a edição de 14/09 linkou uma matéria com
131 cliques para o STF. Pela regra *fail-open*, entraria no relatório como anunciante falso — foi
para `DOMINIOS_EDITORIAIS`. É exatamente o caso que o cadastro do marketing-bp resolve com fila de
pendências em vez de classificação automática.

✅ **Link esquecido da Vimansca saiu do template:** último clique em **14/09** (44 cliques);
nenhuma edição de 15/09 em diante tem link para `vimansca.com.br`. Confere com o relato de remoção
em 15/09.

⚠️ **Correção (16/set):** o Elias avisou que 08, 09, 10 e 11/09 **não foram dias de anúncio** da Vimansca — só 04/09 (3º mês do contrato). Validado no `stg_insider__events` e no mart `cbo_insider_email_analytics_daily`: a edição de 04/09 tinha **3 links** para `vimansca.com.br` (88+6+4 cliques); as edições de 08, 09, 10, 11 e 14/09 têm **1 link** cada (116, 93, 63, 54 e 41 cliques), com primeiro clique no dia do envio e maioria de clicadores novos (em 11/09, 32 de 38 não tinham clicado em 04/09). Conclusão: um elemento com link da Vimansca ficou no template do Resumo BP depois de 04/09 e só saiu em 15/09. Os cliques são reais, mas não são inserção contratada. O relatório detecta por domínio e não consegue distinguir os dois casos — precisa da lista de dias contratados por anunciante (cadastro por inserção, não só por empresa). O parágrafo abaixo ficou registrado como estava em 14/set e está **errado** na leitura de "recorrente".

~~**A Vimansca virou anunciante recorrente:**~~ saiu de 2 inserções esporádicas (14/07, 17/08) para veicular 04, 08, 09, 10 e 11/09 — quatro dias seguidos na segunda semana de setembro. O alcance por inserção cai conforme a frequência sobe (98 pessoas em 17/08 contra 38–67 nos dias seguidos), o que é esperado: a mesma base recebe o anúncio repetido. Somadas, as 7 inserções deram 691 cliques.

Sendflow e Lídio Carraro seguem sem inserção nova desde 28/07 e 21/08.

⚠️ A janela do relatório é de 120 dias, então a inserção do **Insider Store** (mar–abr/2024, achada ao varrer o histórico completo) não aparece aqui — só na página do marketing-bp, que lê o histórico inteiro.

### Detecção automática: o que o código faz sozinho

A classificação é **fail-open**: todo domínio clicado que não estiver nas listas de BP / social /
editorial é tratado como anunciante. Consequências:

| Situação | Automático? |
|---|---|
| Nova inserção de anunciante já conhecido | ✅ Sim — aparece no próximo refresh |
| Anunciante **novo** (domínio nunca visto) | ✅ Sim — entra no dropdown e na tabela de destinos sozinho |
| Nome de marca do anunciante novo | ❌ Não — sai como domínio cru (`lidiocarraro.com`) até ser adicionado em `PARCEIROS_NOME` |
| Novo domínio **editorial** (link de notícia externa) | ❌ Não — entra como se fosse anunciante; precisa ir para `DOMINIOS_EDITORIAIS` |
| Inserção com ≤ 3 cliques numa edição | ❌ Não — cortada pelo `HAVING qt_cliques > 3` em `cliques_dominio.sql` |
| Link de parceiro encurtado por domínio BP (`sitebp.la`, `go.bp.app`) | ❌ Não — contaria como tráfego BP |
| Inserção com mais de 120 dias | ❌ Não — fora da janela |

Verificado em 25/ago: nenhum anunciante está sendo escondido pelo corte de 3 cliques, e todos os
links dos encurtadores BP são de campanha própria (freemium, compartilhe, EVG) — nenhum de parceiro.
**Manutenção mínima por anunciante novo: uma linha em `PARCEIROS_NOME`.**

### ⚠️ Gotchas de leitura

- **A taxa de abertura humana oscila muito por período** — 7,6% (mai) → 23% (jun–jul) → 9,4% (semana de 27/07)
  → 23,5% (ago), medido sobre eventos `email_open`. `bl_human_open` está sempre populado (nunca NULL),
  então não é falha de dados: é mudança de composição/classificação MPP. **Não comparar taxa de abertura
  humana entre inserções distantes** sem olhar o período — cliques não sofrem esse efeito e são a métrica
  confiável para comparar veiculações.
- **CTR de anunciante fica na casa de 0,0x%** — o formato da página usa 2–3 decimais abaixo de 1%,
  senão o número vira "0%" para o parceiro.
- **O rótulo de edição é `DD/MM`** e serve de chave no match parceiro→edição no `index.html`.
  Seguro na janela de 120 dias; se algum dia a janela passar de 365 dias, colide e precisa virar data ISO.

## Migração para o marketing-bp — PR #152 aberto (11/set)

> **Status:** https://github.com/barbaraolivieribp/marketing-bp/pull/152 — CI verde, mergeable. Entrega a página `/bp-ads` com duas abas (**Funil de negociações** do pipeline BP ADS do Pipedrive + **Resultados dos disparos**, que é este relatório embutido com export PDF) e `/admin/resumo-bp-anunciantes`. Depois do merge ainda faltam: aplicar a migration `resumo_bp_dominios` no Supabase e deployar as 2 edge functions pela Lovable (o push não deploya). **Este relatório do portal segue sendo a versão viva até lá.**

⚠️ A página nova `/resultados-crm` (main, set/2026) lê e-mail de `dtm_analytics_revenue_insider_funnel`, enquanto esta usa `cbo_insider_email_analytics_daily`. Os dois marts **discordam em ~4% das edições** (429 de 445 batem até 0,1%; 11 divergem acima de 1%, máx 50%) — ambos batem na edição validada contra a UI. Decidir qual é a fonte oficial antes que alguém compare as duas telas.


**Fonte muda para o mart `datamart.cbo_insider_email_analytics_daily`** (descoberto 25/ago), que já tem
tudo pronto e resolve o refresh manual:

- `qt_sent` (o "Sent" real do Insider — 385.512 na edição de 14/07, contra 390.048 da minha aproximação
  `delivered+blocked+dropped+bounce`), `qt_delivered`, `qt_unique_open`, `qt_unique_machine_open`, `qt_unique_click`
- **`arr_link_activity`** — array com URL + cliques + cliques únicos por link: é a segmentação por parceiro
  pronta, idêntica ao "Link Click Activity" da UI do Insider (Vimansca 14/07: 141 cliques / 67 pessoas ✓)
- **443 edições desde fev/2024** → mata a limitação da janela de 120 dias
- Atualizado pelo dbt → sem `refresh.py`, sem `data.json`, sem launchd

Padrão do marketing-bp: edge function (`requireAuth` + `_shared/bigquery.ts`) → hook → componente → rota.
⚠️ Edge function **não sobe no push** — deploy manual pela Lovable.

### Cadastro de anunciantes (desenho definido 25/ago — a validar com Elias)

A classificação *fail-open* de hoje não sobrevive ao histórico completo: no mart inteiro aparecem
`revistaoeste.com`, `gazetadopovo.com.br`, `cnnbrasil`, `senado.leg.br`, `vatican.va` — todos **fontes
das matérias** do Resumo BP, que virariam anunciantes falsos. Precisa de lista explícita.

Testado e **refutado**: usar a forma do link (raiz vs caminho) para separar anúncio de fonte. Vimansca usa
`vimansca.com.br/` (raiz), mas Sendflow usa `sndflw.com/i/T7HR...` e Lídio Carraro
`loja.lidiocarraro.com/raridades/...` — iguais a link de matéria. **Não há sinal estrutural; tem que ser humano.**

Desenho: **cadastro por empresa, não por inserção** — registrar um domínio pega todas as inserções dele,
passadas e futuras. Mais uma **fila de pendências**: domínio não classificado não entra como anunciante,
fica esperando triagem (o oposto de hoje, onde entra sozinho e errado — foi assim que `terra.com.br` virou
falso anunciante). Volume medido: **1 a 4 domínios novos por mês**, em geral 2.

Três tipos, não dois — `substack.com/@telleroficial` e `docs.google.com/forms` são **conteúdo da própria BP**,
nem anúncio nem fonte externa.

Tabela: `dominio` (PK), `tipo` (`anunciante`/`fonte_externa`/`conteudo_bp`), `nm_empresa`, `caminho_prefixo`
(opcional, para domínio compartilhado tipo Sympla), `bl_ativo`, auditoria. Nome da empresa é campo próprio
porque uma marca pode ter mais de um domínio.

Mockup navegável com dados reais: artifact `99bbc54b`.

⚠️ Regra de processo, não de software: **link de anunciante não pode ser embrulhado no encurtador BP**
(`sitebp.la`, `go.bp.app`) — o clique viraria tráfego BP e o anunciante sumiria. Conferido em 25/ago: ok hoje.

## Pendências / próximos passos

- **Cadastrar no marketing-bp:** com o PR #152 mergeado (16/09), `allugator.com` (anunciante, marca "Allugator") e `stf.jus.br` (fonte externa) precisam entrar no seed/tabela `resumo_bp_dominios` do Supabase — senão a Allugator sai como domínio cru e o STF vira anunciante falso na página nova. Hoje só estão cadastrados no `refresh.py` deste relatório.
- **Link esquecido no template (16/set):** ✅ resolvido no template (sem cliques de Vimansca desde 15/09); avisar Nicolas para conferir o template do Resumo BP; decidir com Elias se as edições 08–14/09 devem sair do relatório da Vimansca (hoje o filtro é só por domínio). No cadastro de anunciantes do marketing-bp, considerar registrar **dias contratados** por anunciante, não só o domínio.
- Validar dash com Nicolas/Elias (mensagem na thread do #performance-e-bi).
- Avaliar se a janela de 120 dias basta a longo prazo: quando o BP Ads tiver mais de 4 meses de
  histórico, o parceiro volta a perder inserções antigas. Alternativa é materializar uma tabela
  de histórico de edições em vez de reler a `stg_insider__events` a cada refresh.
- Decidir entrega da visão restrita por parceiro (página por parceiro com link não-listado vs Looker com ACL).
- Propor padrão de UTM para links de anunciante com quem monta as edições.
- Se aprovado, agendar refresh recorrente (launchd, padrão zenvia-custos).

## Queries

| Arquivo | O quê |
|---|---|
| [queries/funil_edicao.sql](queries/funil_edicao.sql) | Funil por edição: enviados, entregues, abertos (total e humano), clicadores, cliques, unsub |
| [queries/cliques_dominio.sql](queries/cliques_dominio.sql) | Cliques por domínio de destino e edição (segmentação de parceiro) |

## Wiki atualizada

- `wiki-bp/pages/meta-insider-ads.md`: tag `RBP` documentada (nomenclatura, fonte, gotcha de UTM, aproximação de "enviados").
