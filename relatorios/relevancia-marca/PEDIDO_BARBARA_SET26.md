# Rodada 9 — pedido da Bárbara (14/09/2026)

Prompt de handoff para abrir em sessão nova. Continuação direta do relatório
`relevancia-marca`. Prazo combinado: **sexta, 18/09/2026**.

---

## Prompt

Você vai continuar o relatório **relevancia-marca** (rodada 9). É um pedido da Bárbara
Olivieri feito em 14/09/2026 no #squad-cac e reforçado por DM, com prazo na sexta (18/09).

### O pedido, como ela escreveu

> "Esta semana precisamos ter um entendimento mais concreto do impacto dos nossos vídeos que
> têm mais sucesso no YouTube e impacto em vendas/CAC. Cases para serem analisados: **sabatinas
> e 11 de setembro**. O Abe tem um estudo inicial mas precisa ser refinado. Incluído **dados do
> YouTube Studio**, principalmente, que esteve pendente no último e ajuda na análise."

> "Analisar tbm com dados do **Instagram**: como estamos na janela de 90 dias desses dois,
> acredito que teremos todos os dados fornecidos durante a API — número de seguidores a mais,
> alcance etc."

Ela pediu explicitamente que as métricas sejam divididas em dois blocos:

**1. Impacto relacionável** (as que têm relação direta com o vídeo)
- Métricas do YouTube do período
- Métricas do CTA do YouTube no período — "desde view na LP por UTM até o objetivo da LP"
- Métricas de pesquisa de marca do período, **incluindo portal**
- Métricas de redes sociais do período (de alcance a faturamento)

**2. Impacto indireto nos outros canais** — vendas, ticket médio etc.

No DM ela deu o contexto que motivou o pedido:
- "Sobre este final de semana: Google teve o pior desempenho (YouTube) e **todo o efeito vem do
  fechamento de BP10**."
- "Tenho muita clareza que os eventos não são relacionados, até pq o efeito no que o vídeo se
  trata não foi tão sentido no Technocracia."
- "Porém, posso estar errada. **Precisamos encontrar uma forma de analisar isso.**"

Ou seja: ela já tem uma hipótese (o pico do fim de semana é fechamento de lote de BP10, não o
vídeo) e quer um método que separe as duas coisas — não uma confirmação.

### Meta verificável

Para cada um dos dois cases (sabatinas e 11 de Setembro), responder com número:

1. **Atenção**: quanta audiência o vídeo gerou (YouTube + plataforma + redes).
2. **Venda rastreável**: quanto disso virou lead/venda com UTM/CTA atribuível.
3. **Venda não rastreável**: qual o efeito no volume de vendas e no CAC do período contra
   contrafactual pareado.
4. **Veredito**: o movimento comercial do período é atribuível ao vídeo ou ao fechamento de
   BP10? Com o teste que sustenta a resposta, não com narrativa.

### Antes de produzir: revisão crítica do que já foi feito

Esta rodada **não é só mais uma análise**. São 8 rodadas acumuladas, várias com conclusão já
publicada e já repetida em reunião. Antes de rodar qualquer query nova, faça uma passada
adversarial no `ANALISE.md`, nos `TESTE_*.md` e nos scripts, procurando erro, fragilidade e
ponto cego. Trate os achados anteriores como hipóteses de um colega, não como verdade herdada.

Abaixo estão **candidatos a ponto cego que eu já suspeito**. Não são conclusões: confirme ou
derrube cada um lendo o código e os dados, e diga qual é o caso. Se um deles se confirmar, diga
**o que muda na conclusão publicada** — inclusive se a resposta for "nada, o efeito sobrevive".

1. **O desenho individual pode não responder à pergunta que a Bárbara está fazendo.** Todo o
   maquinário de pessoa-dia mede *consumo na plataforma* → venda. A audiência do YouTube, em
   larga maioria, **não está na plataforma**. "O vídeo no YouTube gerou venda?" e "quem assistiu
   na plataforma comprou mais?" são perguntas diferentes, e só a segunda foi respondida até
   agora. A ponte entre as duas é exatamente o que falta (YT Studio + UTM/CTA). Isto é o ponto
   cego central desta rodada — encare de frente antes de escrever qualquer coisa.
2. **Volume e eficiência podem não ser duas evidências independentes.** A rodada 2 vende
   "+24,7% de transações E CAC −11,9%" como sinal limpo em *duas* dimensões, com o spend
   pareado. Mas com spend fixo, CAC é quase o inverso de transações atribuídas a ads. Verifique
   se os dois números são o mesmo fato contado duas vezes ou se a diferença entre transações
   totais e transações de ads sustenta a leitura. Decomponha.
3. **Multiplicidade sem correção.** 8 rodadas, 4 estratos, janelas D+7/14/30/60, 11 fontes de
   relevância, ranking de 172 playlists no IAC. Quantos testes foram feitos no total e quantos
   "significativos" sobreviveriam a um ajuste de múltiplas comparações? O topo de um ranking de
   172 itens é selecionado por ruído por construção — o IAC tem n mínimo por playlist?
4. **Erro-padrão com pessoa-dia repetida.** O próprio texto admite que os ICs de janela longa
   são anti-conservadores por autocorrelação. Isso vale também para o teste principal (D+14)?
   Os erros estão clusterizados por pessoa? Se não estiverem, os p<0,005 estão inflados e o
   1,65× pode ser bem menos sólido do que parece.
5. **Nulo com pouca potência virou conclusão de negócio.** "Freemium é nulo, não distribuir
   sabatina como topo de funil" vem de 102–486 pessoa-dias. Calcule o **efeito mínimo
   detectável** desse teste. Se ele só detecta lift acima de, digamos, 2×, então "nulo" não
   autoriza a recomendação — é ausência de evidência, não evidência de ausência.
6. **Contaminação de mídia paga no Organic Video.** Campanha de vídeo do Google Ads sem
   tagging correta cai como tráfego orgânico no GA4. A ρ com spend *total* é baixa (0,162), mas
   o teste certo é contra o **spend de vídeo do Google/YouTube**, não o spend agregado. Se
   houver contaminação, o termômetro inteiro mede orçamento, como o social.
7. **O pareamento controla fase, mas não mix de campanha.** Um dia com fechamento de BP10 e um
   dia com uma campanha pequena têm baselines de conversão diferentes mesmo dentro do mesmo
   quintil de spend e da mesma "fase". A rodada 8 tratou lançamento e fechamento como dummies —
   isso basta, ou o mix de campanha ainda está solto?
8. **Uso operacional causal de um indicador declaradamente coincidente.** A própria análise diz
   que o efeito é contemporâneo e que lag ≥1 é nulo nas duas direções, e mesmo assim a métrica
   proposta recomenda "se o YT orgânico está alto, há espaço para escalar". Se o indicador não
   antecede nada, essa recomendação se sustenta? Ou é conselho de agir com base em algo que só
   se sabe depois?
9. **A seleção dos próprios cases usa uma variável nunca medida.** "Os vídeos que têm mais
   sucesso no YouTube" — sucesso no YouTube (views, retenção) nunca foi medido. Todos os
   rankings existentes são de consumo na plataforma. Os dois cases foram escolhidos por
   percepção, não por dado.
10. **Três eventos simultâneos no case de setembro.** A estreia do 11 de Setembro (07/09), o
    pico de cadastro de Technocracia (05–07/09) e o fechamento de BP10 caem na mesma janela.
    A dúvida da Bárbara é exatamente essa. Ou o desenho separa os três, ou a entrega tem que
    dizer que não separa — e o que seria preciso para separar.
11. **Potência para n=1 evento.** A rodada 1 já mostrou que n=2 eventos não detecta nada
    (Lewis & Rao). O case do 11 de Setembro é **um** evento. Declare o efeito mínimo detectável
    **antes** de rodar. Um "não significativo" produzido por falta de potência não pode ser
    reportado como "o vídeo não teve efeito" — esse é o erro mais fácil de cometer aqui e o
    mais caro em reunião.

Procure também o que não está nesta lista. E se alguma conclusão publicada estiver
simplesmente errada, diga — corrigir em público é mais barato que manter.

### Fatos já levantados — não redescobrir

- **O case "11 de setembro" é a mídia `As Consequências do 11 de Setembro após 25 Anos`**,
  playlist **`Temas em alta`**, estreia na plataforma em **07/09/2026**, **1.757 usuários
  distintos**. (Confirmado em `obt_user_media_interactions`.)
  ⚠️ **D+14 dessa estreia só fecha em 21/09** — até sexta só existe D+11. Entregar o D+7 fechado
  e deixar D+14/D+30 agendados, dizendo isso explicitamente no relatório.
- **Sabatinas**: Renan Santos e Pablo Marçal estrearam na plataforma em **19/08** (as lives de
  14 e 17/08 foram só no YouTube) e hoje são os dois maiores da playlist `BP nas Eleições` —
  **5.826 e 3.200 usuários**. O Teste A (02/09) só conseguiu medi-los em **D+7** e deu não
  significativo (Marçal 0,81× · Renan 0,48×).
  **Agora dá para rodar D+14 e D+30 dos dois** — `fct_transactions` aprovadas estão íntegras até
  **14/09/2026**. Esse é o refinamento mais barato e o que responde direto à pergunta dela
  ("os vídeos de mais sucesso vendem?"). Reutilizar `queries/22_lift_por_sabatina.sql` e
  `queries/25_janelas_medio_prazo.sql`.

### Bloqueios reais — declarar para ela logo, não na sexta

- **YouTube Studio não está em lugar nenhum.** Não existe tabela de views/inscritos/retenção no
  BigQuery (verificado em `datamart` e `dbt_abe`) e o GA4 não tem isso. O que o GA4 tem é
  **Organic Video** = sessões que o YouTube manda para o site (mediana 767/dia), que é
  termômetro, não audiência de canal. O acesso ao YouTube Analytics está pedido desde 25/08
  (Fase 2 do `PLANO.md`) e segue **bloqueado por permissão** — é exatamente o mesmo gap do
  relatório anterior. **Conseguir o acesso de Visualizador no YouTube Studio é o item 0 da
  semana**; sem ele o bloco "métricas do YouTube do período" continua parcial e isso tem que
  estar escrito no topo da entrega.
- **Instagram/Meta Insights idem** — não há fonte no warehouse. E existe um achado que
  contradiz o uso ingênuo do dado de rede: **social orgânico do GA4 mede orçamento**
  (ρ com spend 0,861; pareado por spend, o CAC *piora* 12,9% e a conversão por sessão cai
  20,6%). Se for usar alcance/seguidores do Instagram, usar como métrica de atenção, nunca como
  indicador comercial, e dizer por quê.
- **Portal (Mixpanel)**: `fct_mixpanel__portal_page_view_events` só existe desde 01/05/2026 e a
  instrumentação está crescendo — série curta. Ela pediu "pesquisa de marca incluindo portal";
  dá para usar como descritivo do período, não como série para teste pareado.

### O que já está resolvido — não repetir trabalho

Ler `ANALISE.md` inteiro antes de começar. Os vereditos fechados:

- Hipótese "relevância baixa a resistência" **refutada no agregado**; o efeito real é
  **ativação da base morna** (membro leve 1,65×, freemium nulo até D+60).
- **É formato, não pauta**: o lift não escala com notoriedade; sabatinas pooled = BP Entrevista
  (1,61× = 1,61×). **Estreia tardia na plataforma zera a ativação** — gotcha central para o case
  do 11 de Setembro, cuja estreia foi 07/09.
- **Rodada 8 (11/09)**: fechamento de lote não é confundidor; o sinal de conversão ("porta mais
  aberta") é **fenômeno de lançamento** — fora das janelas de estreia sobra volume (+18,9%***),
  a conversão por sessão zera e o CAC enfraquece (−6,8%, p=0,05).
- Share of Search é coincidente, não antecedente, e não move eficiência. Social orgânico e
  GA4 newUsers descartados como fonte.
- Métricas vivas: **termômetro diário** (YT orgânico > 1,3× a MM28) e **IAC-14 por playlist**
  (`queries/15_iac_ranking_playlists.sql`).

### Pendência operacional que entra junto

A rodada 8 **está no working tree e não foi commitada**: `M relevancia-marca/ANALISE.md`,
`M index.html`, mais untracked `TESTE_A/B/C_*.md`, `data/`, `queries/21–26`, `scripts/`.
Falta **commit + push** (perguntar ao André antes de commitar) e **responder a Bárbara e o Luan
na thread do #performance-e-bi**, que ficou sem retorno desde 11/09:
https://slack-brasil-paralelo.slack.com/archives/C05D4PQEYTT/p1789143570602289

### Onde está tudo

| Item | Caminho |
|---|---|
| Análise viva (843 linhas, 8 rodadas) | `relatorios-abe-bp/relatorios/relevancia-marca/ANALISE.md` |
| Programa em 5 fases | mesma pasta, `PLANO.md` |
| Bibliografia comentada | mesma pasta, `REFERENCIAS.md` |
| Testes de setembro | `TESTE_A_FORMATO_VS_PAUTA.md`, `TESTE_B_MEDIO_PRAZO.md`, `TESTE_C_GA4_NEWUSERS.md` |
| 26 queries validadas | `queries/` |
| Scripts de análise | `scripts/` (o pareado é `teste_pareado_spend.py` / `teste_pareado_sem_lancamento.py`) |
| Relatório publicado | https://andreyuitiabe-lab.github.io/relatorios-abe-bp/relatorios/relevancia-marca/ |

**Wiki a carregar antes de escrever qualquer query:**
`wiki-bp/pages/bq-acesso.md`, `bq-schema-core.md`, `bq-regras.md`, `metricas-referencia.md`
(§Ativação por conteúdo e §Share of Search), `mcp-ga4.md`;
`wiki-brasil-paralelo/pages/relevancia-marca.md` (obrigatória), `regras-negocio.md`,
`campanhas-calendario.md` (o verbete Tecnocracia/TEC tem o contexto do fim de semana que ela
citou), `canais.md`.

**Regras que valem aqui:**
- Toda query roda com `bqq`. Nunca `bq query`.
- `tb_campaign_period` está incompleta (faltam DOM, ELS, CDL, EVG, ODI, ENE) — usar o calendário
  da wiki, como faz `teste_pareado_sem_lancamento.py`.
- Grafia: o conteúdo na plataforma é `Technocracia`, **com H**. Regex em `tecnocra` volta vazio
  em silêncio.
- Significância por placebo/pareamento, não por t-test em n pequeno. Nada de causalidade sem
  contrafactual — o teto do método é direcional (Gordon 2023); o padrão-ouro seria geo holdout.

### Entrega esperada

Duas coisas, nesta ordem.

**1. Auditoria crítica (antes de qualquer query nova).** Uma seção nova no `ANALISE.md`
— "Rodada 9a — auditoria das rodadas 1–8" — com os achados da revisão ordenados por quanto
mudam a conclusão. Para cada um: o que foi checado, o veredito (confirmado / derrubado /
inconclusivo), e o efeito prático. Itens que exigirem recomputar algo, recompute. Traga isso
para o André **antes** de seguir — pode mudar o que vale a pena rodar na rodada 9b, e pode
exigir correção do que já está publicado e da página da wiki.

**2. A análise dos dois cases.** Atualizar o relatório existente **in-place** (é o mesmo tema,
não criar pasta nova), com uma seção nova para sabatinas e 11 de Setembro, e atualizar
`ANALISE.md` + `wiki-brasil-paralelo/pages/relevancia-marca.md`. Se o acesso ao YouTube Studio
não sair a tempo, entregar o que dá com plataforma + GA4 + UTM e deixar o gap declarado no
topo — não silenciar a limitação.

Em ambas: número com intervalo, não adjetivo. Onde o dado não sustenta a resposta, dizer que
não sustenta e o que seria preciso para sustentar. A Bárbara pediu explicitamente "uma forma de
analisar isso" e disse que pode estar errada — ela quer método que possa contrariá-la, não
confirmação.
