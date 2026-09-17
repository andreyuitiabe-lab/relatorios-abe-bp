# Teste A — Formato vs pauta: de onde vem o lift de ativação da sabatina?

**Data:** 02/09/2026 · **Continuação de:** [ANALISE.md](ANALISE.md) §3–4 e pendência 1
**Queries:** `queries/21_*.sql` a `23_*.sql` · **Script:** `scripts/teste_a_analise.py` · **Dados:** `data/teste_a_*.csv`

## Pergunta

O lift de ativação da playlist `BP nas Eleições` (IAC 1,98×, lift 1,44–1,65× em membro
leve/médio) vem da **relevância eleitoral do entrevistado** ou do **formato entrevista**?
Evidência prévia: `BP Entrevista` (formato irmão, sem pauta eleitoral) tinha IAC 2,70×,
*acima* da sabatina.

**Interpretação pré-registrada:** lift(ALTA) ≈ lift(BAIXA) e ambos ≈ BP Entrevista → é formato.
lift(ALTA) >> lift(BAIXA) → a notoriedade/pauta importa.

## Resposta curta

**É formato, não pauta.** Na mesma máquina e no mesmo período, o lift pooled das sabatinas
(1,61×, IC95 [1,37–1,86]) é **estatisticamente idêntico** ao dos top-5 episódios de
`BP Entrevista` (1,61×, IC95 [1,36–1,86]; p da diferença = 0,95). E a notoriedade **não**
escala o lift: os dois entrevistados de maior projeção nacional (Marçal e Renan) são os
**únicos sem lift nenhum** na plataforma (0,70× pooled, IC95 [0,30–1,15]) — com um caveat
operacional importante (§Descoberta), enquanto Zema (2,06×), Aldo Rebelo (1,78×) e Caiado
(1,69×) lideram. O gradiente vai na direção **oposta** à hipótese da pauta.

## Descoberta que muda a leitura anterior

**Renan e Marçal só entraram na plataforma em 19/08/2026** — as lives de 14/08 e 17/08 foram
no YouTube; `MIN(dt_created_at)` das duas mídias na playlist é 19/08 (query 21). Duas
consequências:

1. **O IAC 1,98× da playlist (query 14, sessões até 07/08) foi medido SEM nenhum pessoa-dia
   de Renan/Marçal.** O lift documentado na ANALISE.md §3 é inteiramente das 7 sabatinas de
   jun–jul (Caiado, Zema, Rebelo, Derrite, Salles, Cury, de Toni).
2. A audiência de Renan/Marçal na plataforma é *catch-up* (D+2 a D+5 da live) — o público
   quente assistiu no YouTube. Isso confunde a comparação ALTA vs BAIXA (ver limitações).

**Última transação aprovada confirmada: 02/09 (dia parcial); compras completas até 01/09.**
Logo D+14 só é completo para pessoa-dias ≤ 18/08 — Renan/Marçal (estreia 19/08) **não têm
janela D+14 completa**, ao contrário do que o desenho assumia. Solução: D+14 como métrica
primária para as 7 sabatinas de jun–jul; **D+7 uniforme** (pessoa-dias ≤ 25/08, cobre o grosso
da audiência de Renan/Marçal) como janela de comparabilidade das 9.

## Desenho

Máquina da query 14, rodada **por sabatina individual** (query 22) e por episódio de
BP Entrevista (query 23):

- **População:** pessoa-dia de membro (nenhuma sessão free/fake-free no dia), engajamento
  leve/médio (1–8 dias ativos nos 30d anteriores), **sem compra aprovada não-renovação nos
  60d anteriores**. Sessão = ≥300s em `obt_kafka__view_sessions`.
- **Desfecho:** compra aprovada não-renovação (`fct_transactions`, join por e-mail via
  `dim_contact`) em D+1..D+14 (primário) e D+1..D+7 (uniforme). Nunca D+0 (causalidade reversa).
- **Comparador:** pessoa-dias das top-8 playlists da janela (excluídas `BP nas Eleições` **e**
  `BP Entrevista`, para não contaminar o contraste de formato), **pareado por calendário**:
  para cada sabatina, o controle usa somente os dias em que ela teve audiência. A taxa de
  controle padronizada pelo mix de dias do tratado (coluna `taxa_c_std` nos CSVs) confirma que
  o pareamento não muda a conclusão.
- **Inferência:** Fisher exato (pooled tratado vs controle pareado) + bootstrap por dia
  (2.000 reps) para IC95 do lift e da diferença entre grupos. Lift de grupo = observados ÷
  esperados (esperado = Σ nₜ × taxa de controle pareada de cada sabatina — tipo SMR).
- **Janelas:** sabatinas: pessoa-dias 08/06–25/08 (D+14 completo só ≤18/08); BP Entrevista:
  01/03–18/08 (alinha com a query 14/15).

## Classificação de notoriedade

| Grupo | Entrevistados | Justificativa |
|---|---|---|
| **ALTA** | Pablo Marçal, Renan Santos | Candidatos presidenciais de projeção nacional; picos de mídia nacional na semana da sabatina |
| **Fronteira** | Romeu Zema, Ricardo Salles | Projeção nacional real (governador/pré-candidato; ex-ministro), mas sem o pico de atenção de Marçal/Renan. Testados nos dois lados |
| **BAIXA** | Caiado, Cury, Aldo Rebelo, Derrite, Caroline de Toni | Projeção regional/setorial (Cury é notório como autor, não como figura eleitoral — notoriedade *eleitoral* baixa) |

## Resultado por sabatina

**D+14** (janela completa; Renan/Marçal não têm) — tratado vs controle top-8 pareado por dia:

| Sabatina | Estreia | n (pessoa-dias) | taxa D+14 | controle | **Lift** | IC95 (boot) | p (Fisher) | RPP-14 | razão RPP |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| Romeu Zema | 13/06 | 1.385 | 2,82% | 1,37% | **2,06×** | [1,56–2,59] | <0,001 | R$ 51,43 | 3,1× |
| Aldo Rebelo | 17/06 | 1.357 | 2,36% | 1,33% | **1,78×** | [1,25–2,35] | 0,003 | R$ 34,12 | 2,1× |
| Ronaldo Caiado | 08/06 | 2.390 | 2,34% | 1,39% | **1,69×** | [1,14–2,25] | <0,001 | R$ 39,10 | 2,4× |
| Ricardo Salles | 26/06 | 672 | 1,94% | 1,26% | 1,53× | [0,53–2,15] | 0,119 | R$ 24,99 | 1,7× |
| Augusto Cury | 28/06 | 1.305 | 1,53% | 1,25% | 1,22× | [0,74–1,67] | 0,379 | R$ 20,94 | 1,4× |
| Caroline de Toni | 27/07 | 368 | 1,36% | 1,37% | 0,99× | [0,29–1,74] | 1,000 | R$ 17,03 | 1,1× |
| Guilherme Derrite | 25/06 | 432 | 1,16% | 1,25% | 0,93× | [0,19–1,82] | 1,000 | R$ 15,93 | 1,1× |

**D+7 uniforme** (inclui Renan/Marçal; pessoa-dias ≤ 25/08):

| Sabatina | n | taxa D+7 | controle | **Lift** | IC95 | p |
|---|---:|---:|---:|---:|---|---:|
| Aldo Rebelo | 1.382 | 1,81% | 0,76% | **2,40×** | [1,70–3,22] | <0,001 |
| Romeu Zema | 1.473 | 1,56% | 0,77% | **2,02×** | [1,19–2,97] | 0,002 |
| Ricardo Salles | 704 | 1,28% | 0,72% | 1,78× | [0,76–2,66] | 0,109 |
| Ronaldo Caiado | 2.468 | 1,26% | 0,78% | **1,61×** | [1,06–2,30] | 0,011 |
| Augusto Cury | 1.450 | 0,76% | 0,71% | 1,07× | [0,22–1,83] | 0,753 |
| Guilherme Derrite | 443 | 0,68% | 0,73% | 0,93× | [0,00–1,86] | 1,000 |
| **Pablo Marçal** | 1.527 | 0,46% | 0,57% | **0,81×** | [0,25–1,45] | 0,725 |
| **Renan Santos** | 734 | 0,27% | 0,57% | **0,48×** | [0,00–1,16] | 0,447 |
| Caroline de Toni | 402 | 0,25% | 0,73% | 0,34× | [0,00–1,15] | 0,380 |

## Comparação ALTA vs BAIXA

Lift pooled (observados ÷ esperados, controle pareado por dia de cada sabatina; IC e p por
bootstrap de dias):

| Cenário | Janela | Lift ALTA | Lift BAIXA | Diferença | p |
|---|---|---:|---:|---|---:|
| **Principal** (ALTA = Marçal+Renan; fronteira na BAIXA) | D+7 | **0,70** [0,30–1,15] | **1,65** [1,34–1,95] | [−1,46; −0,42] | **0,001** |
| Só nacionais puros vs locais puros (Derrite, de Toni, Rebelo) | D+7 | 0,70 [0,28–1,16] | 1,75 [1,24–2,22] | [−1,68; −0,37] | 0,003 |
| Sensibilidade: Zema+Salles movidos para ALTA | D+7 | 1,40 [0,97–1,87] | 1,54 [1,21–1,91] | [−0,72; +0,44] | 0,607 |
| Sensibilidade: ALTA = Zema+Salles (D+14, sem Renan/Marçal) | D+14 | 1,90 [1,49–2,28] | 1,51 [1,21–1,79] | [−0,09; +0,88] | 0,115 |

- No cenário principal a direção é **oposta** à hipótese da pauta: lift(ALTA) < lift(BAIXA),
  p=0,001. Não há nenhum cenário em que lift(ALTA) >> lift(BAIXA).
- A sensibilidade mostra que o resultado do cenário principal é carregado inteiramente por
  Renan/Marçal (o caso confundido pela estreia tardia); movendo os casos de fronteira, os
  grupos ficam indistinguíveis — que é exatamente a predição do "é formato".

**Proxy contínua de notoriedade** (pessoa-dias de audiência da própria sabatina × lift):
Spearman ρ = 0,30 (p=0,43, n=9) no D+7; ρ = 0,61 (p=0,15, n=7) no D+14. Sem relação
significativa — e o que existe de positivo no D+14 é "audiência grande ativa mais", que é
compatível com formato+interesse, não especificamente com pauta eleitoral (Aldo Rebelo, grupo
BAIXA, tem o 2º maior lift D+7).

## Contraste com BP Entrevista (a régua de formato)

Top-5 episódios por audiência, mesma máquina, D+14 (01/03–18/08):

| Episódio | n | taxa D+14 | Lift | IC95 | p | RPP-14 |
|---|---:|---:|---:|---|---:|---:|
| A Odisseia com Lucas Ferrugem | 1.367 | 3,15% | **2,15×** | [1,59–2,81] | <0,001 | R$ 34,53 |
| Dom Bertrand e Luiz Philippe | 1.508 | 1,99% | **1,47×** | [1,05–1,97] | 0,043 | R$ 30,11 |
| Capitão Antunes | 1.528 | 2,16% | 1,41× | [0,86–1,84] | 0,059 | R$ 27,12 |
| Francisco Litvay | 436 | 2,06% | 1,44× | [0,62–2,14] | 0,307 | R$ 18,49 |
| Daniel Teixeira (CHEGA) | 355 | 1,41% | 1,08× | [0,29–1,81] | 0,812 | R$ 190,85 ⚠️ |

⚠️ RPP do Daniel Teixeira é outlier de cauda (≤5 compradores, uma compra gigante) — ignorar o RPP, o lift é ~1.

**Pooled D+14: sabatinas 1,61× [1,37–1,86] vs BP Entrevista 1,61× [1,36–1,86] — diferença
[−0,35; +0,38], p=0,95.** Indistinguíveis. (O 2,70× vs 1,98× do IAC da ANALISE.md era razão de
RPP contra a mediana do catálogo — métrica de receita, sensível a cauda; na régua de *taxa de
conversão* com controle pareado, os dois formatos empatam exatamente.)

Dentro de BP Entrevista o lift também **não** acompanha notoriedade pública do entrevistado
(o maior é um episódio com o apresentador do Odisseia, produto interno; o "mais famoso"
politicamente não lidera) — mesma dispersão por episódio que as sabatinas (0,99–2,06 vs
1,08–2,15).

## Veredito

**Formato, com alta confiança na parte testável — e um resultado operacional novo sobre
Renan/Marçal.**

1. **Sabatina ≈ BP Entrevista** na mesma régua (1,61× vs 1,61×, p=0,95). A condição
   pré-registrada "lift(ALTA) ≈ lift(BAIXA) e ambos ≈ BP Entrevista" é satisfeita no único
   recorte limpo (D+14, jun–jul, com Zema/Salles testados nos dois lados: diferenças ns).
2. **Notoriedade não escala o lift** em nenhum recorte: a proxy contínua é ns, o ranking
   individual é liderado por Zema/Rebelo/Caiado (fronteira e BAIXA), e os dois nomes de maior
   projeção nacional têm lift pontual **abaixo de 1** na plataforma.
3. **O caso Renan/Marçal é um achado à parte**: publicadas na plataforma só em D+2/D+5 da
   live, as duas sabatinas de maior audiência no YouTube **não ativaram a base na
   plataforma** (0,70×, IC95 [0,30–1,15] — o IC exclui o 1,34 do piso do grupo BAIXA).
   Leituras possíveis, não separáveis com estes dados: (a) o público quente já tinha assistido
   no YouTube e o pessoa-dia da plataforma é *replay* frio; (b) o efeito de ativação depende
   do momento de estreia; (c) público de Marçal/Renan é menos aderente ao produto BP. Em
   qualquer leitura, **não é a notoriedade que gera a ativação**.

**Implicação prática:** para ativar a base morna, o que importa é pautar o *formato*
entrevista/sabatina (e estreá-lo na plataforma junto com o momento público), não caçar o
entrevistado de maior projeção eleitoral.

## Limitações (honestas)

- **Renan/Marçal**: janela D+7 (não D+14), truncagem zero mas janela curta; estreia tardia na
  plataforma confunde notoriedade com timing/canal. O teste ALTA vs BAIXA "puro" está, a rigor,
  **confundido** — por isso o veredito se apoia mais no empate sabatina×entrevista e na
  ausência de gradiente dentro de jun–jul do que no p=0,001 do cenário principal.
- **Poder por sabatina**: com n de 368–2.468 pessoa-dias e taxas ~1–3%, os ICs individuais são
  largos (Salles, Cury, de Toni, Derrite são todos compatíveis com 1× e com 1,8×). As
  conclusões válidas são as pooled; não usar os lifts individuais isoladamente para rankear
  entrevistados.
- **Observacional**: mesmo com placebo de top-playlists, pareamento por calendário, exclusão
  D+0 e condicionamento em "sem compra 60d" (gotchas da wiki aplicados), seleção residual de
  quem escolhe assistir cada conteúdo não é eliminável sem experimento.
- Pessoa-dia que assistiu 2 sabatinas no mesmo dia conta nas duas (raro; viés ~0).
- RPP-14 é sensível a cauda (caso Daniel Teixeira); os vereditos usam taxa de conversão.

## Arquivos

| Arquivo | O quê |
|---|---|
| [queries/21_sabatinas_inventario.sql](queries/21_sabatinas_inventario.sql) | Inventário das 9 sabatinas (estreia na plataforma, pessoa-dias) |
| [queries/22_lift_por_sabatina.sql](queries/22_lift_por_sabatina.sql) | Máquina da query 14 por sabatina, saída (grupo, dia) p/ pareamento |
| [queries/23_lift_bp_entrevista.sql](queries/23_lift_bp_entrevista.sql) | Idem para top-5 episódios de BP Entrevista |
| [scripts/teste_a_analise.py](scripts/teste_a_analise.py) | Lift, Fisher, bootstrap, grupos, proxy contínua |
| `data/teste_a_inventario_sabatinas.csv` | Saída query 21 |
| `data/teste_a_lift_por_sabatina.csv` · `data/teste_a_lift_bp_entrevista.csv` | Saídas granulares 22/23 |
| `data/teste_a_resultado_por_sabatina.csv` · `data/teste_a_resultado_bp_entrevista.csv` | Tabelas finais com lift/IC/p |
