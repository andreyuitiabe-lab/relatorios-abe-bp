# Freemium: quem ativa e o que consome

## Pergunta original

O time que está montando outra visão do freemium precisa verificar se quem entra no
freemium está ativando (consumindo alguma coisa) e o que está consumindo.

## Entrega

[`queries/ativacao_e_consumo.sql`](queries/ativacao_e_consumo.sql) — uma query, duas seções
(`resumo` e `conteudo`). Roda em ~8s sobre 5 semanas de coorte.

## Decisões de abordagem

**Freemium não é o papel `free`.** `'free' IN UNNEST(dim_user.arr_roles)` é estado atual e
some quando a pessoa converte — filtrar por ele subconta justamente os convertidos. A coorte
é "criou conta e não tinha compra aprovada até 1h depois do cadastro".

**A conta tem de nascer junto ou depois do download.** Sem essa regra entra quem já era
cadastrado e só baixou o app depois, que converte muito mais. A tolerância de 1h é
obrigatória: o `first_open` costuma ser gravado DEPOIS do `dt_created_at` na mesma sessão, e
um corte estrito descarta ~1/3 dos cadastros legítimos.

**Ativação = qualquer play** (`obt_user_media_interactions`). Para profundidade, trocar por
`vl_total_watch_time_seconds >= 300`, que é o critério de 5 min do relatório
"Essa galera assiste e compra?".

## Achados principais

Coorte de 01/07 a 05/08/2026 — 9.721 contas freemium, janela de 30 dias:

- **66,1% ativam** (6.428). **Um terço nunca consome nada** (3.293).
- **A ativação se decide em 24h**: 5.841 das 6.428 ativações acontecem no primeiro dia —
  **91% do total**. De 7d para 30d a curva anda só 203 contas.
- **El Salvador carrega tudo**: 4.656 contas, **47,9% da coorte inteira**, 4.075 horas. O
  segundo colocado (O Brasil Evangélico) faz 11,1%.
- Cauda longa e rasa: fora os três primeiros, nenhum conteúdo passa de 8,5% de alcance.

Curvas completas (D0..D30) medidas em coorte equivalente:

| Dia | Ativou | Comprou | Ativados | Não ativados |
|---|---:|---:|---:|---:|
| D0 | 50,5% | 0% | — | — |
| D1 | 60,2% | 2,2% | 3,2% | 0,4% |
| D7 | 64,1% | 4,9% | 6,9% | 1,2% |
| D30 | 66,2% | 6,0% | 8,0% | 2,3% |

**Ativação qualifica**: quem ativa converte 3,5× mais em D30 (8,0% contra 2,3%) e rende
R$ 48,39 por conta contra R$ 15,92. Dos compradores, 85% tinham ativado, e 78% desses
assistiram ANTES de comprar.

⚠️ **Isso é qualificação, não causalidade.** Quem assiste é quem já estava mais interessado;
parte do gap é seleção. Separar exigiria holdout — segurar a ativação para uma fração
aleatória dos novos cadastros.

## Implicação prática

A janela de ação é o primeiro dia. Fluxo de nurture de 7, 14 ou 30 dias chega depois de a
ativação já estar decidida. E o terço que nunca ativa (3.293 contas na coorte medida) é o
maior bloco parado: converte a 2,3% e hoje não recebe tratamento diferente.

## Pendências

- Validar se "ativação" deve ser play ou 5 min — muda o número e a comparabilidade com o
  relatório "Essa galera assiste e compra?".
- O holdout, se a decisão for escalar ativação.

## Queries

| Arquivo | O que faz | Status |
|---|---|---|
| [`ativacao_e_consumo.sql`](queries/ativacao_e_consumo.sql) | resumo de ativação + ranking de conteúdo | ✅ rodou (8s) |

## Wiki

Regras da coorte já estão em `~/.claude/wiki-bp/pages/freemium-app.md` (seção do funil
download → conta → venda).
