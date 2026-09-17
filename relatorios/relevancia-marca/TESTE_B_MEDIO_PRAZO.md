# Teste B — Efeito de médio prazo da sabatina (D+30/D+60; D+90 censurado)

**Executado em 02/09/2026.** Extensão do achado §3 da [ANALISE.md](ANALISE.md) (query 14:
membro leve 1,65× / médio 1,44× em D+1..D+14; freemium nulo).

## Pergunta

O lift de ativação de membro em D+14 é **antecipação de compra que já viria** (pull-forward)
ou **incremento real**? E o freemium, nulo em D+14, sai do zero quando a janela alonga
(lift de aquisição lento — não-membro converte em ~421 dias)?

**Interpretação pré-registrada:** lift estável/crescente ao alongar → incremento;
lift decaindo para ~1× → pull-forward; freemium saindo do nulo → aquisição lenta (cautela, n pequeno).

## Censura à direita — o que sobrevive a cada janela

Última data **completa** em `fct_transactions`: **2026-09-01** (02/09 é o dia corrente,
parcial; 03/09+ são registros com data futura espúria — `MAX(dt_ordered_at)` cru dá 10/09 e
engana). Um pessoa-dia em dia *d* só entra na janela D+k se *d + k ≤ 2026-09-01*:

| Janela | Cutoff do pessoa-dia |
|---|---|
| D+14 | dia ≤ 18/08/2026 |
| D+30 | dia ≤ 02/08/2026 |
| D+60 | dia ≤ 03/07/2026 |
| D+90 | dia ≤ 03/06/2026 |

Pessoa-dias de exposição (≥300s) por sabatina da playlist `BP nas Eleições`
(query [24](queries/24_censura_sabatinas.sql) · [data/teste_b_censura.csv](data/teste_b_censura.csv)):

| Sabatina | 1º dia | pd total | D+14 | D+30 | D+60 | D+90 |
|---|---|---:|---:|---:|---:|---:|
| Ronaldo Caiado | 08/06 | 6.090 | 5.802 | 5.481 | 4.811 | **0** |
| Romeu Zema | 13/06 | 3.442 | 3.161 | 2.907 | 2.438 | **0** |
| Aldo Rebelo | 17/06 | 3.431 | 3.325 | 3.238 | 2.832 | **0** |
| Guilherme Derrite | 25/06 | 1.186 | 1.093 | 994 | 672 | **0** |
| Ricardo Salles | 26/06 | 1.807 | 1.646 | 1.530 | 906 | **0** |
| Augusto Cury | 28/06 | 4.805 | 3.555 | 3.295 | 1.511 | **0** |
| Caroline de Toni | 27/07 | 1.275 | 1.135 | 600 | 0 | 0 |
| Pablo Marçal | 19/08 | 4.579 | **0** | 0 | 0 | 0 |
| Renan Santos | 19/08 | 2.116 | **0** | 0 | 0 | 0 |

- **D+90 é infactível hoje**: a playlist estreou em 08/06/2026 e o cutoff D+90 é 03/06 —
  **zero** pessoa-dias elegíveis. O plano pré-registrado D+90 fica censurado; a janela mais
  longa factível é **D+60**, e a razão reportada é **lift(D+60)/lift(D+14)**.
- **Marçal e Renan não têm nem D+14 completo** (estreia da exposição 19/08; o evento foi
  14/08 e 17/08, mas o 1º pessoa-dia na plataforma é 19/08) — fora de todas as janelas.
- Caroline de Toni só sobrevive a D+14/D+30 e por isso fica fora do universo comum.
- **Sobrevivem ao teste: 6 sabatinas** (Caiado, Zema, Aldo Rebelo, Derrite, Salles, Cury),
  13.170 pessoa-dias brutos com D+60 completo.

## Desenho

- **Universo comum às 3 janelas** (exigência de comparabilidade — nenhuma mistura de universo):
  pessoa-dias com **dia ∈ [08/06/2026, 03/07/2026]** — todos com D+14, D+30 e D+60 completos, e
  tratado e comparador no **mesmo calendário** (isso corrige um viés do desenho da query 14, em
  que comparadores de mar–mai não tinham contrapartida tratada).
- Máquina idêntica à query 14: sessão ≥300s em `obt_kafka__view_sessions`; outcome **D+1..k**
  (nunca D+0); compra = `approved` e `bl_is_renovation = FALSE`, join por e-mail via
  `dim_contact`; **sem compra nos 60d anteriores**; engajamento prévio ≥1 dia/30d (exclui
  "sem atividade prévia"); comparador principal = **top-8 playlists** por audiência do próprio
  universo; estratos: membro leve (1–2 dias/30d), médio (3–8), heavy (9+), freemium (agregado —
  558 pessoa-dias tratados não suportam faixas).
- **Overlap tratado/comparador**: regra da query 14 mantida — classificação por pessoa-DIA com
  precedência sabatina > top_playlist > outro; a mesma pessoa pode ser tratado num dia e
  comparador em outro. Ao alongar a janela isso não muda a atribuição (a janela só muda o
  outcome, não o grupo).
- **Sensibilidade** (query 26): mesmo cálculo com comparadores do período amplo 01/03–03/07
  (desenho original da query 14), para medir o quanto o calendário do comparador move o resultado.
- IC95: Newcombe/Wilson na diferença de proporções; IC do lift por log-risk-ratio (Katz).
  Queries: [25](queries/25_janelas_medio_prazo.sql) · [26](queries/26_sensibilidade_periodo_amplo.sql).
  Dados: [teste_b_janelas.csv](data/teste_b_janelas.csv) ·
  [teste_b_sens_amplo.csv](data/teste_b_sens_amplo.csv) ·
  [teste_b_resultado.csv](data/teste_b_resultado.csv).

## Resultado — desenho principal (calendário pareado, sabatina vs top-8)

| Estrato | Janela | n trat / comp | Taxa trat | Taxa comp | Lift [IC95] | Diff pp [IC95] | RPP trat (razão) |
|---|---|---|---:|---:|---|---|---|
| **Membro leve** | D+14 | 1.895 / 24.999 | 2,37% | 1,44% | **1,64× [1,21–2,23]** | +0,93 [+0,32, +1,73] | R$ 37,59 (2,16×) |
| | D+30 | idem | 3,38% | 2,16% | **1,56× [1,21–2,01]** | +1,21 [+0,47, +2,14] | R$ 54,24 (2,12×) |
| | D+60 | idem | 5,70% | 3,47% | **1,64× [1,35–1,99]** | **+2,23 [+1,24, +3,38]** | R$ 96,49 (2,25×) |
| **Membro médio** | D+14 | 2.802 / 22.237 | 2,28% | 1,75% | 1,30× [1,00–1,69] | +0,53 [+0,01, +1,17] | R$ 37,31 (1,62×) |
| | D+30 | idem | 3,93% | 2,99% | **1,31× [1,08–1,60]** | +0,94 [+0,24, +1,75] | R$ 59,28 (1,53×) |
| | D+60 | idem | 6,46% | 5,11% | **1,26× [1,09–1,47]** | +1,35 [+0,45, +2,36] | R$ 81,77 (1,17×) |
| Membro heavy | D+14 | 1.548 / 9.605 | 2,45% | 2,92% | 0,84× [0,60–1,18] ns | −0,46 [−1,21, +0,49] | R$ 43,84 (0,89×) |
| | D+30 | idem | 4,78% | 4,85% | 0,99× [0,78–1,25] ns | −0,07 | R$ 74,27 (0,93×) |
| | D+60 | idem | 8,14% | 8,36% | 0,97× [0,81–1,17] ns | −0,22 | R$ 108,57 (0,80×) |
| **Freemium** (todas) | D+14 | 558 / 4.807 | 1,79% | 1,56% | 1,15× [0,60–2,21] ns | +0,23 [−0,67, +1,74] | R$ 10,16 (1,29×) |
| | D+30 | idem | 3,58% | 2,54% | 1,41× [0,89–2,25] ns | +1,05 [−0,30, +2,98] | R$ 17,02 (1,05×) |
| | D+60 | idem | 5,02% | 4,43% | 1,13× [0,77–1,66] ns | +0,59 [−1,06, +2,79] | R$ 24,24 (0,84×) |

### Curva do lift (sabatina vs top-8, calendário pareado)

```
lift
2,0 |
1,8 |
1,6 |  ●1,64———————●1,56———————●1,64   membro leve      razão D+60/D+14 = 1,00
1,4 |
1,3 |  ●1,30———————●1,31———————●1,26   membro médio     razão D+60/D+14 = 0,97
1,15|  ○1,15       ○1,41       ○1,13   freemium (ns)    razão D+60/D+14 = 0,99
1,0 |––––––––––––––––––––––––––––––––  (pull-forward previa convergência para cá)
0,85|  ○0,84       ○0,99       ○0,97   heavy (ns)
    +----D+14--------D+30--------D+60
```

### Sensibilidade (comparador período amplo 01/03–03/07, desenho da query 14)

| Estrato | D+14 | D+30 | D+60 | razão D+60/D+14 |
|---|---|---|---|---|
| Membro leve | 2,08× [1,55–2,78] | 1,55× [1,22–1,98] | **1,45× [1,21–1,75]** | 0,70 |
| Membro médio | 1,57× [1,23–2,01] | 1,35× [1,12–1,62] | 1,13× [0,98–1,31] | 0,72 |
| Membro heavy | 1,03× ns | 0,97× ns | 0,85× [0,72–1,01] | 0,82 |
| Freemium | 0,69× ns | 0,90× ns | 0,84× ns | 1,22 |

O decaimento aqui (0,70–0,72) é **artefato de calendário do comparador**: o D+60 de um
comparador de março cai em abr–mai e o de um tratado de junho cai em jul–set — fases de
campanha diferentes inflam a taxa base do tratado-período. No desenho com calendário pareado
(o correto para comparar janelas) o decaimento desaparece. Mesmo no pior caso (desenho amplo),
o lift do leve em D+60 é 1,45× com IC inteiro acima de 1 — longe de convergir para 1×.

## Veredito: incremento real, não pull-forward

1. **Membro leve: incremento real.** Lift 1,64× em D+14 e **1,64× em D+60**
   (razão = 1,00); a diferença absoluta **cresce** de +0,93pp para **+2,23pp** e a receita
   extra por pessoa-dia vai de +R$ 20 para **+R$ 54** (2,25×). Pull-forward previa lift → 1×
   e diff → 0; aconteceu o oposto: as compras incrementais continuam se acumulando após D+14.
2. **Membro médio: incremento com no máximo antecipação marginal.** 1,30× → 1,26×
   (razão 0,97), significativo em D+60 [1,09–1,47]. Na sensibilidade decai a 1,13× ns —
   ler como efeito real porém menor e menos robusto que o do leve. A razão de RPP cai
   (1,62×→1,17×): o incremento do médio é mais em conversão do que em ticket.
3. **Freemium: continua nulo — sem indício de lift de aquisição lenta até D+60.**
   Point estimates 1,13–1,41× mas todos os ICs cruzam 1 folgadamente (n tratado = 558) e a
   RPP em D+60 fica *abaixo* do comparador (0,84×). Alongar a janela não tirou o freemium do
   zero. Com ~421 dias de conversão média, D+60 ainda é cedo para descartar de vez — mas nada
   aqui sustenta usar sabatina como topo de funil.
4. **Heavy: nulo em todas as janelas**, consistente com o achado original (já está no teto).

**Leitura de negócio:** a conclusão da ANALISE.md §3 se **fortalece** — a sabatina (e por
extensão o formato entrevista) gera **receita nova** na base morna, não antecipa receita que
já viria. O efeito de 60 dias no membro leve (+2,2pp de conversão, +R$ 54/pessoa-dia) é ~2,4×
o efeito aparente de 14 dias em valor absoluto.

## Limitações

- **D+90 censurado**: zero pessoa-dias elegíveis (playlist estreou 08/06; cutoff D+90 era
  03/06). O grosso do universo (08/06–03/07) completa D+90 em **01/10/2026** — reexecutar a
  query 25 com a janela D+90 **após ~05/10/2026** para fechar a razão pré-registrada
  lift(D+90)/lift(D+14).
- O universo comum cobre só **6 das 9 sabatinas** e 26 dias de calendário (08/06–03/07);
  Marçal e Renan — as de maior repercussão pública — estão fora até de D+14. O resultado é
  sobre as sabatinas de jun/2026.
- Freemium com n tratado pequeno (558 pessoa-dias): poder só para efeitos grandes (~>1,7×).
- Observacional com pareamento por engajamento prévio + exclusão de compra recente — não é
  experimento; seleção residual por interesse (quem escolhe assistir político X) não é
  controlada. A checagem de pré-tendência da rodada original (tratados com taxa prévia MENOR)
  vale para o mesmo universo de junho.
- Ao alongar a janela a taxa base sobe (leve: 1,44%→3,47% no comparador) — lifts entre janelas
  são comparáveis por razão e por diferença, mas não são a mesma escala de raridade.
- Overlap de pessoas entre grupos em dias diferentes (regra da query 14 mantida); com janelas
  longas os outcomes de pessoa-dias vizinhos da mesma pessoa se sobrepõem mais, o que
  autocorrelaciona observações e estreita artificialmente os ICs — os ICs reportados são
  anti-conservadores em magnitude desconhecida (mitigação futura: 1 pessoa-episódio em vez de
  pessoa-dia, ou cluster bootstrap por e-mail).

## Queries e dados

| Arquivo | O quê |
|---|---|
| [queries/24_censura_sabatinas.sql](queries/24_censura_sabatinas.sql) | Censura por sabatina (1º dia, pd sobreviventes por janela) |
| [queries/25_janelas_medio_prazo.sql](queries/25_janelas_medio_prazo.sql) | Máquina principal: 3 janelas, universo comum D+60, calendário pareado |
| [queries/26_sensibilidade_periodo_amplo.sql](queries/26_sensibilidade_periodo_amplo.sql) | Sensibilidade: comparador período amplo (desenho query 14) |
| [data/teste_b_censura.csv](data/teste_b_censura.csv) | Saída Q24 |
| [data/teste_b_janelas.csv](data/teste_b_janelas.csv) | Saída Q25 (contagens brutas) |
| [data/teste_b_sens_amplo.csv](data/teste_b_sens_amplo.csv) | Saída Q26 (contagens brutas) |
| [data/teste_b_resultado.csv](data/teste_b_resultado.csv) | Tabela final janela × estrato com lifts, ICs, RPP e razão D+60/D+14 |

ICs calculados por script auxiliar (Newcombe na diferença; Katz no risk ratio) — reproduzível
a partir dos CSVs brutos; o resultado consolidado está em `teste_b_resultado.csv`.
