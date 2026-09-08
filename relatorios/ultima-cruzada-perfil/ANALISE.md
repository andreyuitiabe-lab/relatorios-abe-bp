# Coleção Brasil: A Última Cruzada — perfil do comprador e abordagem do Comercial

**Data da análise:** 04/09/2026 · **Atualizado:** 08/09/2026 · **Janela:** 01–08/09/2026 (lançamento 01/09)

> Números do fechamento de **08/09/2026 10h30**. **A versão viva é o relatório HTML** — `python refresh.py`
> regera `data.json` e a página inteira a partir das queries de `queries/`.
>
> ⚠️ **A leitura mudou entre 04 e 08/09** e a mudança é de mix de canal, não de comportamento.
> Na primeira semana o Comercial fazia 66% do volume; com a mídia escalando, caiu para
> 40,4%. Como os dois canais vendem para públicos diferentes, todo agregado se moveu
> (vitalícios 52,2% hoje contra 70% em 04/09). **O comprador de cada canal não mudou** —
> mudou quanto cada canal pesa. Ver §"Comercial e digital vendem para pessoas diferentes".

## Pergunta original

Quem está comprando a Coleção Brasil: A Última Cruzada — membros ou não? Qual o perfil
(renda, cartão, consumo, engajamento, tempo de casa)? E como o Comercial está abordando?

## Decisões de abordagem

- **Universo**: `nm_gateway_plan LIKE 'colecao-brasil%'` **OU** produto contendo "Coleção Brasil".
  A wiki documentava só 2 planos; existem **4** (`-fisico`, `-completo`, `-completo-cursos`,
  `-digital`) + bundles em `nm_gateway_plan = 'black'` (`Última Cruzada + Black Vitalício/Anual`).
  Filtrar só pelos 2 documentados perderia ~30% das vendas.
- **Chave de pessoa**: e-mail normalizado (cobre multi-conta). 1.012 compradores aprovados no fechamento de 08/09.
- **Membership**: whitelist de tiers de `bq-regras.md`, **excluindo os planos do próprio livro**
  (produto físico gera assinatura-fantasma — sem isso, 100% viraria "membro ativo").
- **Vitalício**: `bl_lifetime_offer` restrito a planos GBB/produto com "Vitalício", excluindo
  `colecao-brasil|odisseia|clube-do-livro` (esses vêm com a flag ligada sem ser vitalício).
- **Abordagem**: as conversas Zenvia do produto foram identificadas por **regex no texto da
  conversa** (`última cruzada|coleção brasil`) — o Zenvia **não tem etiqueta/etapa própria do CBR**
  (`nm_latest_lead_product_detail` segue com VITALÍCIO GBB / BLACK / MECENAS).
- **Buckets de abordagem mutuamente exclusivos** (corrigido pós-auditoria): a 1ª versão classificava
  o prospect por `MIN(template)` e jogava no bucket "broadcast" todo prospect tocado pelo disparo,
  inclusive os que também tiveram atendimento de vendedor. Os 384 prospects mistos (6,6% do bucket)
  concentravam 96,8% das respostas e 82,6% das vendas atribuídas ao disparo — a taxa de resposta
  aparecia como 5,3% em vez de **0,18%**. Agora há três grupos disjuntos.
- **Guarda de causalidade na atribuição**: "abordado" exige abordagem anterior à compra. Sem ela,
  metade das vendas "abordado → digital" era de gente abordada depois de já ter comprado.
- **Detector de script**: a assinatura da abertura pula os 40 primeiros caracteres — quase todo
  script começa com o primeiro nome do cliente, e comparar o início faz disparo de massa parecer
  mensagem única (media 13% de script onde o real é 98%).
- Benchmark de renda/cartão calculado sobre os 603k membros ativos, para não ler nível de cartão
  em absoluto (gotcha de `bq-acesso.md`: Black+ sozinho não é sinal de elite).
- **Corte por canal em vez de por "fase" da campanha** (decisão de 08/09): a tentação era comparar
  semana 1 × semana 2, mas 05–06/09 é fim de semana e 07/09 é feriado — o Comercial não vende nesses
  dias, então a queda dele é calendário, não estratégia. O corte por canal isola o efeito real:
  o comprador de cada canal não mudou, mudou o peso de cada canal no mix.

## Achados principais

### Resultado em 8 dias
- **1.012 compradores / R$ 1.015.275** (ticket médio R$ 1.003).
- **Comercial 409 (40,4%) / R$ 404.123**;
  Digital 603 / R$ 611.151.
- Curva diária (compradores, Comercial|Digital): 01/09 0|3 · 02/09 76|9 · 03/09 108|68 · 04/09 119|78 · 05/09 22|130* · 06/09 8|157* · 07/09 53|137* · 08/09 23|21
  — `*` = fim de semana ou feriado (o Comercial não vende nesses dias; o digital não para).
  ⚠️ O último dia é parcial.
- **Inversão de mix na virada da semana**: o digital passou de 9 compradores (02/09) para 157 (06/09).
  O Comercial oscila com o calendário, então **não se pode concluir que ele desacelerou** — a queda de
  119 (sex 04) para 22 (sáb 05) e 8 (dom 06) é operacional.
- Mix de produto: Físico 721 (ticket R$ 942),
  Completo 264 (R$ 1.198),
  Digital 25 (R$ 414), Bundle Black 2.
- **Recusa/abandono**: 376 pessoas (488 tentativas) —
  ~37% do número de compradores, sem fluxo de recuperação aparente.

### Comercial e digital vendem para pessoas diferentes
O mesmo produto, dois públicos. É isso que explica a diluição do agregado.

| Indicador | Comercial | Digital | Razão |
|---|---:|---:|---:|
| Compradores | 409 | 603 | ÷1,5 |
| Ticket médio | R$ 988 | R$ 1.013 | ~1× |
| Membro ativo | 82,15% | 57,38% | 1,4× |
| Vitalício | 73,59% | 37,65% | **2,0×** |
| Comprou o CDL | 54,77% | 42,45% | 1,3× |
| 1ª compra na BP | 4,65% | 12,44% | ÷2,7 |
| LTV anterior (mediana) | R$ 6.190 | R$ 2.490 | **2,5×** |
| Cartão premium | 85,82% | 84,64% | ~1× |
| Sem sessão em 90d | 36,92% | 61,69% | ÷1,7 |

- O Comercial vende para a base fiel; o digital para um público **muito mais frio em vínculo**
  (37,65% de vitalícios contra 73,59%, LTV 2,5× menor).
- ✅ **Mas o poder de compra é o mesmo**: cartão premium 85,82% × 84,64%
  e ticket praticamente igual. A mídia não desceu de faixa econômica — está alcançando o mesmo tipo de
  gente com dinheiro que ainda não tem vínculo forte com a BP. Canais complementares, não substitutos.

### Vínculo com a base (agregado — ler junto com o corte por canal acima)
- **90,7% já eram clientes**; 94 pessoas fizeram a 1ª compra na BP
  (eram 13 em 04/09 — o crescimento é quase todo do digital).
- **67,4% membros ativos · 52,2% vitalícios ·
  15,1% Mecenas · 47,4% compraram o CDL ·
  20,9% a Odisseia.**
- **LTV anterior mediano R$ 4.061**; 50,9% já gastou R$ 4 mil+.
- **Tempo de casa mediano 3,98 anos.**
- **Penetração de 1,93% entre os 24,9k compradores do CDL** —
  o público natural da carteira segue longe de saturado.

### Perfil socioeconômico (acima da base, com folga)
| Indicador | Compradores UC | Base membros ativos | Lift |
|---|---:|---:|---:|
| Cartão premium (Black/Amex/Platinum) | 85,1% | 57,2% | **1,5×** |
| Cartão nível Black | 64,9% | 30,5% | **2,1×** |
| Renda (decil 8–10 do CEP) | 58,4% | 31,7% | **1,8×** |

- Gênero inferido: 69% masculino.
- Idade (dado em 533 de 1012): **68% tem 45 anos ou mais**.
- Geografia: SP 30%, RJ 12%, RS 10%, PR 7%, MG 7%, DF 6%.
- Pagamento: 86% cartão (12x é o padrão de todas as ofertas), 12% Pix.

### Engajamento: compra sem consumo
- **51,7% dos compradores não teve nenhuma sessão na plataforma nos últimos 90 dias** (era 43% em 04/09 — subiu com o peso do digital, que tem 61,69%).
  Só 15% são usuários de alto engajamento (11+ dias ativos em 90d).
- O produto físico vende para quem **tem vínculo mas não consome** — colecionador, não espectador.
- O Comercial converte melhor exatamente na faixa engajada leve/média (73–74% das vendas dessas
  faixas são comerciais) e pior nos totalmente inativos (57%).

### Abordagem do Comercial: o disparo frio não abre conversa
**13.414 prospects abordados** desde o lançamento. Grupos mutuamente exclusivos.

| Tipo de abordagem | Prospects | Respondeu | Comprou | Conversão | Receita | Abertura scriptada |
|---|---:|---:|---:|---:|---:|---:|
| Disparo em massa (só a peça) | 6.027 | **0,23%** | 16 | **0,265%** | R$ 15.985 | 99% |
| Disparo + atendimento de vendedor | 457 | 80,74% | 31 | 6,783% | R$ 27.782 | 99% |
| Abordagem do vendedor (sem disparo) | 6.930 | **25,76%** | 326 | **4,704%** | R$ 330.897 | 77% |

- **A peça de disparo, sozinha, segue quase inerte**: 6.027 prospects, 0,23% de
  resposta, 16 vendas, R$ 15.985. Quem foi atendido por vendedor converte
  18× mais e trouxe R$ 330.897.
- ⚠️ **O disparo não aquece — ele seleciona** (conclusão mantida com 4 dias a mais de dados).
  Controlando pela etapa `carteiraMecenas`: disparo puro 0,3% · disparo + atendimento
  7,52% · **vendedor sem disparo 8,02%**. Quem recebeu a peça antes de falar com o
  vendedor continua convertendo **menos** que quem nunca recebeu.
- ⚠️ **O mecanismo segue não testado.** 77% das "abordagens de vendedor" abrem com
  texto repetido em 20+ conversas — os dois lados são disparo scriptado. A diferença de
  0,23% para 25,76% na resposta é real, mas não é personalização.
- `carteiraMecenas` concentra a operação: 8.932 prospects,
  330 vendas (3,69%).
- Vendas entre **29 vendedores** (líder com 68).

### Dentro das conversas: o que o cliente escreve
Base: **2.160 prospects que responderam** (7.296 mensagens), 15,0% compraram.

- **44,8% nunca escreveram nada** — só clicaram no botão do WhatsApp ou
  mandaram "sim/ok" (10,0% de conversão).
- Conversão por profundidade: só clique 10,0% → 1 fala 10,9% →
  2–3 17,4% → **4+ falas 37,2%**. ⚠️ Parte é causalidade reversa:
  frete/endereço e "paguei" são temas **pós-decisão**.
- ⚠️ **"Quanto custa" é o tema mais comum (496 pessoas) e converte
  16,7% — abaixo da média de 19,0% de quem escreve.**
  Pergunta sobre o produto em si (226) converte 29,6%.

**Pedir desconto não é objeção — é sinal de compra** (conclusão mantida):

| Sinal na fala | Prospects | Conversão |
|---|---:|---:|
| ✅ Pediu desconto ou condição melhor | 88 | **34,1%** |
| ✅ Citou ser cliente fiel (vitalício / CDL / Odisseia) | 63 | **41,3%** |
| ❌ Declarou restrição financeira | 64 | 7,8% |
| ❌ Achou caro (juízo de valor) | 39 | 7,7% |
| ❌ Clicou por engano / curiosidade | 26 | 7,7% |
| ❌ Ainda pagando o vitalício | 10 | 0,0% |

Base 15,0%. Dois clientes diferentes na mesma frase sobre dinheiro — quem negocia e quem
não tem — e o roteiro não os separa.

**Fricções operacionais:**

| Fricção | Prospects | Conversão |
|---|---:|---:|
| Pediu condição citando fidelidade | 104 | 23,1% |
| Travou no campo de cupom do checkout | 17 | 58,8% |
| Esperando entrega de CDL / Odisseia | 19 | 26,3% |
| Confundiu com a série de 2018 ou com o CDL | 3 | 0,0% |
| Não sabe onde acessar o que comprou | 4 | 75,0% |

- **Não há política de fidelidade**: 104 pessoas pediram condição citando ser
  vitalício/CDL/Odisseia. Resposta do vendedor (83 conversas):
  vai verificar / consegue 18 · passa um cupom 6 · nega — preço fechado 6 · cita a fidelidade do cliente 7 — cada um decide na hora.
- **Campo de cupom sem código divulgado** trava a compra no último passo.
- **19 pessoas em abordagem esperam um produto físico anterior** — risco evitável
  com cruzamento de lista.
- O nome reaproveita a **série "A Última Cruzada" de 2018–2019** (~13k transações antigas na fct).

⚠️ **Privacidade**: transcrições têm nome/telefone. **Nenhuma citação literal publicada** — o repo é
público. A query fica versionada, o texto não; o `data.json` recebe apenas contagens.

### Atribuição: o Comercial trabalha a nata, o digital alcança o resto
⚠️ "Abordado" exige abordagem **antes** da compra. **27 compradores foram
abordados só depois de já ter comprado** (higiene de lista).

| Origem | n | Ticket | Membro | Vitalício | LTV mediana |
|---|---:|---:|---:|---:|---:|
| Abordado → venda Comercial | 307 | R$ 997 | 82% | 76% | R$ 6.390 |
| Abordado → venda Digital | 66 | R$ 1.034 | 77% | 67% | R$ 5.422 |
| Comercial sem abordagem prévia | 102 | R$ 958 | 81% | 67% | R$ 5.842 |
| **Digital sem abordagem prévia** | **537** | R$ 1.010 | **55%** | **34%** | **R$ 2.298** |

- **37% dos compradores foram abordados antes de comprar** (era 60% em 04/09 — caiu porque o
  digital cresceu, não porque o Comercial abordou menos).
- Crédito ambíguo: 66 vendas (R$ 68.288) no digital com abordagem prévia.
- **O grupo majoritário virou o digital sem abordagem nenhuma**: 537 pessoas
  (53,1% dos compradores), com 34% de vitalícios contra
  76% e LTV mediano 64% menor.

### Preço: o Comercial vende mais barato que o site
- **Físico**: Comercial ticket médio **R$ 904** vs Digital
  **R$ 977**.
- **Completo**: Comercial R$ 1.181 vs Digital R$ 1.211.
- **6 faixas de preço simultâneas** na versão física (compradores Comercial/Digital):
  R$ 719 (106C/7D) · R$ 948 (111C/0D) · R$ 959 (55C/361D) · R$ 1.068 (7C/54D) · R$ 1.199 (9C/3D) · R$ 1.918 (1C/3D). A faixa mais barata segue quase exclusiva do Comercial.
- Pendente confirmar com o time se a dispersão é teste controlado ou desconto discricionário.

## Pendências / próximos passos

- [ ] **Confirmar a política de preço**: 6 faixas simultâneas no físico, a mais barata quase
      exclusiva do Comercial. Teste controlado ou desconto livre do vendedor?
- [ ] **Definir condição de fidelidade publicada** por tier (vitalício / CDL / Odisseia). É o pedido
      mais frequente na conversa e hoje cada vendedor decide na hora.
- [ ] **Corrigir o campo de cupom do checkout** — exibe campo sem código divulgado e trava a compra
      no último passo.
- [ ] **Cruzar a lista de abordagem com entregas pendentes** de CDL/Odisseia antes de disparar.
- [ ] **Testar o mecanismo do disparo** (o dado não separa): A/B de remetente (blast × número do
      vendedor) e de formato (peça longa com imagem × texto curto) na mesma lista.
- [ ] **Higiene da lista**: compradores estão sendo abordados depois de já ter comprado.
- [ ] Pedir **etiqueta/etapa própria do CBR no Zenvia** — a medição depende de regex no texto.
- [ ] Lista de reabordagem das recusas (limite/cartão), com perfil idêntico a quem comprou.
- [ ] **Revisitar com a campanha madura**: 8 dias ainda não medem maturação, churn de parcelamento
      nem CAC do digital (falta cruzar com custo de mídia para saber se o comprador frio do digital
      se paga).

## Queries

| Arquivo | O que faz | Status |
|---|---|---|
| [queries/universo_vendas.sql](queries/universo_vendas.sql) | Universo por plano/canal/status | ✅ |
| [queries/base_compradores.sql](queries/base_compradores.sql) | Cria `bp-staging.dbt_abe.tb_uc_compradores` (1 linha/comprador, todos os atributos) | ✅ |
| [queries/perfil_agregado.sql](queries/perfil_agregado.sql) | Renda, cartão, gênero, pagamento, UF | ✅ |
| [queries/benchmark_base.sql](queries/benchmark_base.sql) | Benchmark cartão/renda na base de membros ativos | ✅ |
| [queries/funil_abordagem.sql](queries/funil_abordagem.sql) | Cria `tb_uc_abordagens`; funil disparo→resposta→venda por template | ✅ |
| [queries/etapa_zenvia_compradores.sql](queries/etapa_zenvia_compradores.sql) | Etapa Zenvia dos compradores | ✅ |
| [queries/atribuicao_perfil_por_origem.sql](queries/atribuicao_perfil_por_origem.sql) | Perfil por origem (abordado × canal) | ✅ |
| [queries/amostra_transcricoes.sql](queries/amostra_transcricoes.sql) | Amostra de conversas para ler o pitch | ✅ |
| [queries/conversas_falas_cliente.sql](queries/conversas_falas_cliente.sql) | Separa turnos `seller:`/`prospect:` e devolve as falas com desfecho (⚠️ PII — uso local) | ✅ |

## Entrega

Relatório HTML no portal: `relatorios/ultima-cruzada-perfil/` (card em **Base & Produtos**).
Estrutura padrão — `index.html` (layout + gráficos, nada hardcoded) + `data.json` (gerado) +
`refresh.py` (materializa as tabelas de trabalho e regera o JSON) + `queries/` + este arquivo.
Atualizar com `python refresh.py --push`.

Paleta dos gráficos validada com o validador da skill `dataviz`
(3 slots: azul `#3b6ef5` → âmbar `#b45309` → verde `#0f8a4d`; a paleta anterior da casa falhava na
banda de luminosidade e no piso de croma). Rótulos diretos em todas as barras são o encoding
secundário exigido pelo ΔE 6,6 do par âmbar↔verde.

## Wiki atualizada

- `wiki-bp/pages/bq-planos.md` — seção da Coleção reescrita: 4 planos + bundles Black, sigla `CBR`,
  checkouts, faixas de preço por canal, assinatura-fantasma.
- `wiki-brasil-paralelo/pages/ultima-cruzada.md` — nova página com os achados de negócio.
- `wiki-bp/pages/metricas-referencia.md` — números de referência do lançamento.
