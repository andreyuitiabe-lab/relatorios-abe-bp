# Runbook — Fechamento mensal de Influenciadores

**Gatilho:** André pede "o fechamento de influenciadores do mês" (ou variação) no começo do mês.
Este arquivo é o passo a passo completo. Não improvisar: o relatório de agosto levou 12 versões e
teve a conclusão central invertida duas vezes — os erros que custaram caro estão marcados com ⚠️.

**Público:** Thais Schönerwald (Head de Influência), Isabella Antunes, Bárbara Olivieri.
Duas delas não têm facilidade com números — a linguagem do relatório é calibrada para isso.

---

## Passo 0 — Contexto a carregar

- `~/.claude/wiki-brasil-paralelo/pages/influenciadores.md` (rotina, regras e achados acumulados)
- Este runbook e o `ANALISE.md` da pasta
- `~/.claude/wiki-bp/pages/portal-relatorios.md` só se for mexer na estrutura do portal

## Passo 1 — Conseguir o cachê (bloqueia tudo)

O cachê **não existe no BigQuery**. Sem ele o `refresh.py` para de propósito.

Pedir a **aba INFLUENCIADORES do controle de custo variável** do mês fechado. Quem manda:
Bárbara/Isabella (em agosto veio da Bárbara, com Arthur Victor de Albuquerque Lima e João de Souza
Luiz em cópia). Pedir por Slack no grupo com as três, ou por e-mail.

O que a planilha traz: `Influenciador · Período · Projeto · Descrição · Valor total acordado`.

Preencher em `custo_manual.json`, chave `AAAA-MM`:

| Campo | O que entra |
|---|---|
| `cache_peca_venda` | Cachê de quem gravou **peça de venda** (linhas "Influenciadores Fixos BP" e afins). Entra no cálculo de retorno. |
| `acao_de_marca` | Evento, presença, press kit, passagem — **fora** do retorno. Antes de classificar aqui, conferir no BQ se a pessoa tinha anúncio de venda rodando. |
| `excluido_a_pedido` | O que o André mandar tirar. Registrar o valor e o motivo. |
| `contexto_bp` | Venda nova, custo marginal, spend Meta total e as duas médias da casa — sai do post de fechamento do Washington no `#geral-bp`. |
| `pendencias` | Frases que vão para a seção de pendências da página. |

⚠️ **Conferir se a soma das linhas bate com o total declarado na planilha.** Em agosto divergiu
R$ 5.500 (linhas R$ 52.431,10 × total R$ 46.931,10). Usar a soma das linhas e registrar em `pendencias`.

⚠️ **Cruzar quem teve mídia com quem tem cachê.** Em agosto, cinco influenciadores com R$ 84 mil de
anúncio não tinham cachê listado — o retorno deles ficou otimista. Listar em `pendencias`.

## Passo 2 — Rodar

```bash
cd ~/meu_projeto/relatorios-abe-bp/relatorios/influenciadores-mensal
python3 refresh.py --mes AAAA-MM
```

Usa `bqq` (ADC, não expira). ⚠️ Nunca `bq query`.

Ler os dois avisos que o script imprime:
- **"N anúncios sem influ identificado"** → ver quais e completar o `MAPA` no `refresh.py`. Em agosto
  sobrou 1 ("justiça influ", que não é pessoa). Se subir muito, tem nome novo.
- **"cachê de X sem anúncio correspondente"** → ou o nome está escrito diferente na planilha, ou a
  pessoa não teve peça no ar.

## Passo 3 — Revisar o texto (a parte que exige cabeça)

O `data.json` alimenta gráficos e tabelas. **O texto é escrito à mão.** Abrir as duas páginas no
navegador e olhar o console: há uma guarda que avisa se a soma do `data.json` divergir dos totais
escritos. Ela pega número desatualizado, não frase errada.

Checklist do que muda todo mês:

- [ ] **Tiles do topo** (4 no resumo): gasto, retorno, venda do canal, comparação com a casa
- [ ] **Resumo em 3 pontos** — reescrever inteiro, é a leitura do mês
- [ ] **Seção 01** (`Como ler`, só no resumo tem versão curta): os valores citados nas 3 regras
- [ ] **Seção 02 Gastamos**: parágrafo de abertura, tabela de cachê, ponte com a planilha, ação de marca
- [ ] **Seção 03 Voltou**: os três caminhos + **bloco de ROI** (recalcular os três degraus)
- [ ] **Seção 04 Cascata**: os três valores, o % de cauda do canal × da casa, a comparação na mesma régua
- [ ] **Seção 05 Quem vendeu**: os 3 parágrafos de leitura + a nota do hit rate + quem vendeu sem gasto
- [ ] **Seção 06 Peças**: funil (N no ar / escaladas / quase sem verba), notas dos anúncios e campanhas
- [ ] **Seção 07 Ao longo do ano** (só detalhado): quantos meses acima da média, o padrão da verba
- [ ] **Seção 08 Destaques**: refazer os 5 cards, cada um com "o que fazer"
- [ ] **Seção 09 Pendências**: puxar de `custo_manual.json` e revisar
- [ ] **Rodapé/data** de apuração

### ⚠️ Os cinco erros que já custaram retrabalho

1. **Não dizer que o canal rende acima da média sem checar na mesma régua.** No caixa influs dão mais
   que a casa; contando só peça que rodou, dão menos. A diferença é a venda atrasada, que no canal é
   ~20% contra ~4% na casa. **Sempre comparar só-ativas contra só-ativas.**
2. **Não recomendar realocar verba entre influenciadores.** Quem distribui é o algoritmo da Meta —
   o time sobe tudo. A alavanca deles é cachê, contrato e volume/qualidade de peça.
3. **Não recomendar "pedir mais peças" a quem já entrega muito.** Checar o hit rate primeiro: em
   agosto Fran Otto entregou 28 e teve 1 escalada. O gargalo era distribuição, não volume.
4. **Não chamar o bloco comercial de "vendedor ligou".** 78% dele não tem oportunidade registrada no
   CRM, e parte é recuperação de pagamento. Dizer "fechada pelo time comercial".
5. **Não somar cachê + mídia numa rubrica só** de "investimento em influs" — no controle de custo
   marginal são linhas diferentes e juntar dupla-conta o mês.

### Convenções de escrita

- Nunca "ROAS". Sempre **"cada R$ 1 virou R$ X"**.
- Traduzir: mídia = dinheiro do anúncio · criativo = peça/vídeo · lead = quem deixou o contato.
- Todo número com referência ("R$ 1,54, contra R$ 1,46 da média da casa"). Número solto não comunica.
- Onde a leitura for dura, dizer sem suavizar. Este relatório já teve conclusão errada corrigida.
- Sem emoji como marcador de seção.

## Passo 4 — Validar os dados

Rodar as checagens de `queries/check_*.sql` (uma vez por mês basta, são baratas):

| Query | Confirma |
|---|---|
| `check_dupe.sql` | nenhuma venda contada em mais de um anúncio |
| `check_deals.sql` | o bloco comercial não infla por UNNEST duplo |
| `check_recon.sql` | zero renovação, todas aprovadas, receita reconstituída venda a venda, zero sobreposição entre os caminhos |

Conferir também: cabeçalho, linha e rodapé de cada tabela com o **mesmo número de células** (já
quebrou uma vez depois de edições sucessivas), e o portal respondendo 200.

## Passo 5 — Publicar

```bash
cd ~/meu_projeto/relatorios-abe-bp
git add relatorios/influenciadores-mensal/
git commit -m "Influenciadores mensal: fechamento de <mês>"
python3 scripts/atualiza-datas.py
git add relatorios/index.html && git commit -m "Atualiza datas do portal"
git push origin main
```

⚠️ **`git add` só da pasta.** O repo tem muita coisa não commitada de outros relatórios — nunca `-A`.

Atualizar o card no portal (`relatorios/index.html`): `data-date` e o texto de `.card-date` para o
mês novo. O `data-updated` é do script, não escrever à mão.

⚠️ **O repo é PÚBLICO e indexável.** O relatório traz cachê nominal, avaliação de parceiros e
faturamento da BP. O André autorizou explicitamente em 03/set/2026 — se entrar dado de natureza
nova (contrato, PII, número de outra área), perguntar de novo antes de subir.

Esperar o Pages (~1 min) e conferir:
```
https://andreyuitiabe-lab.github.io/relatorios-abe-bp/relatorios/influenciadores-mensal/
```

## Passo 6 — E-mail

**Para:** thais.schonerwald@brasilparalelo.com.br, isabella.antunes@brasilparalelo.com.br,
barbara.olivieri@brasilparalelo.com.br

⚠️ **Criar como rascunho e avisar o André, não enviar direto** — a menos que ele mande enviar.
A análise do mês é escrita à mão e vai para a head de marketing.

**Assunto:** Influenciadores — resultado de <mês>

Modelo (trocar os números e os dois primeiros bullets pela leitura do mês):

> Oi Thais, Isabella e Bárbara,
>
> Fechamos o resultado de <mês> do canal de influenciadores:
> **<link>**
>
> Os números principais:
> • Gastamos R$ X (R$ Y de anúncio + R$ Z de cachê)
> • Voltou R$ W em N vendas
> • Cada R$ 1 investido virou R$ V, contando só as peças que rodaram no mês
>
> O que mais chama atenção:
> • <achado 1, com o número>
> • <achado 2, com o número>
>
> A página abre no resumo, e tem link no rodapé para a versão detalhada com método e validações.
>
> Ficou faltando: <pendências do mês, se houver>
>
> Qualquer dúvida me chama.
> André

## Passo 7 — Registrar

- `ANALISE.md` desta pasta: achados do mês e pendências
- `~/.claude/wiki-brasil-paralelo/pages/influenciadores.md`: só o que for padrão novo ou achado que
  muda leitura futura — não repetir o número do mês
- `~/.claude/wiki-bp/pages/metricas-referencia.md`: números do mês
- `~/.claude/wiki-bp/log.md`: uma linha
- `DIARIO.md` + tirar da `AGENDA.md`

## Pendências herdadas de agosto/2026

Verificar se foram resolvidas antes de repetir na página:

1. Divergência de R$ 5.500 na soma da aba INFLUENCIADORES
2. Os cinco com mídia e sem cachê (Murillo Capellozzi, Diego Del Rio, BR Explora, Pedro Alaer,
   Julliene Salviano — R$ 84.031)
3. **Comissão** das vendas fechadas pelo comercial — pedir ao Comercial; era 39% da receita do canal
4. **Gross-up de 12,15%**: decidir se entra. Em agosto levaria o retorno de R$ 1,23 para R$ 1,10
5. Teste com a mídia: isolar as peças de melhor retorno em conjunto próprio, para forçar entrega
6. UTM/link próprio por influenciador — recomendação repetida desde julho

## Por que não é automático

Foi avaliado em 08/set/2026 e descartado:
- **Cloud agent (`/schedule`) não serve** — roda na infra da Anthropic, sem acesso à máquina local,
  logo sem `bqq` e sem credencial do BigQuery.
- **LaunchAgent local rodando `claude -p`** funcionaria (é o padrão do `com.abe.zenvia-custos`), mas
  esbarra em duas coisas: o cachê depende de alguém mandar a planilha, e a análise do mês é
  julgamento — automatizar texto e envio para a head de marketing é risco alto para o ganho.

Se um dia virar automático, o desenho discutido era: dia 1 pede o custo, dia 5 publica e deixa o
e-mail como rascunho para o André revisar.
