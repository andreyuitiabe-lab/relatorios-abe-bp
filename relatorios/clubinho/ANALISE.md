# Clubinho do Livro BP — planos e preços (30/09/2026)

## Pergunta original
Thomas Bergman (P&L do Clubinho) perguntou, em DM de 30/09:
1. Quantos compradores do Clube do Livro ficaram no plano do meio e no mais caro.
2. Como estimar quanto o Clubinho vai vender nos planos 2 e 3.

O lançamento é em 05/10, com 3 planos (Desbravador, Navegante, Coleção Completa) e 3 grades de preço em discussão. A resposta orienta o P&L (impressão, brindes, frete) e a escolha do preço.

## Decisões de abordagem
- **Divisão por plano no CdL, por pessoa e não por transação.** Cada nível é uma perna separada: `clube-do-livro` (físico, sempre ~R$ 1.188), `ebooks-*clube*` (bump digital) e `black` com produto ou oferta "Clube do Livro" (Ouro). A pessoa entra no nível mais alto que tem aprovado. Quem comprou só o digital fica de fora. Upgrade = perna comprada mais de 1 dia depois da primeira.
- **SSR com 3 braços pareados.** As mesmas 60 personas (seed 2026, 20 por faixa de renda, 25–75 anos) nos 3 braços. Cada braço foi processado por agentes separados, sem ver os outros, para uma grade não ancorar a outra.
- **O prompt pede para pensar numa criança de 4–8 anos da família.** O DW não tem dado de filhos. Mesmo assim, 24% das personas responderam que não têm criança nessa faixa, o que confirma que o denominador real é mais estreito.
- **Volume por analogia, não pelo `03_forecast.py`.** O fator de preço `sqrt` do script foi invalidado em jul/2026. A calibração usa produtos com nota parecida na renda alta: Odisseia (3,30 → ~3.800 reais) e Box BUC (3,55 → forecast de ~2.700).
- **A divisão estimada para o P&L (45/30/25) é julgamento.** Fica entre "considera" (51/26/22) e "decidido" (13/35/52), mais perto do "considera", porque o SSR exagera o entusiasmo da renda alta. Está declarada como premissa no `refresh.py`.

## Achados principais
- **CdL (24.927 compradores):** 71,1% só físico · 26,0% físico + digital · 2,9% Ouro. No Digital: 70/28/1,3. No Comercial: 72/24/4,5. Só 297 pessoas (1,2%) subiram de nível depois da compra.
- **Nota do Clubinho por renda (grade B):** alta 3,05 · média 2,40 · baixa 1,85. É nicho premium, abaixo do CdL (4,50 na alta).
- **Preço:** a nota média quase não se move (C−A = −0,12, t = −1,73). Mas a renda alta que assinaria (nota 4–5) cai de 40% (A) para 30% (B) e 20% (C). A receita por respondente fica em A 151 · B 150 · C 125, ou seja, **B empata com A usando ~13% menos unidades**.
- **Planos:** o decidido vai no Completa (52%), puxado pelo audiobook (64% de intenção entre quem o cita). O indeciso vai no Desbravador (51%). "Jogos online" é lido como mais tela (18% de intenção entre quem cita), o que deixa o **Navegante como o plano fraco**.
- **Volume:** referência ~3.000 assinaturas / R$ 3,2M (banda de 1.500 a 5.000).
- **Objeções:** peso do total anual (43%), sem criança na faixa (24%), trava de 12 meses sem ver o livro (16%, intenção de só 4%). O melhor público é 45–65 anos, com a ideia de presente para neto.

## Pendências / próximos passos
- A oferta publicada tem dois totais em 12x errados (Desbravador 89,90 → "718,80"; Navegante 99,90 → "838,80"). Avisar a Bárbara e o Luan.
- O frete não está definido na oferta.
- Backtest depois da campanha: comparar a divisão real por plano e o volume com este forecast. Não fechar com apuração parcial (lição da Odisseia).
- Enviar ao Thomas o resumo da parte 2 (a parte 1 foi enviada em 30/09).

## Queries
| Arquivo | O que faz | Status |
|---|---|---|
| [queries/cdl_mix_planos.sql](queries/cdl_mix_planos.sql) | Divisão de compradores do CdL por nível, canal e direto/upgrade | ✅ rodou 30/09 |

Sessões SSR: `personas_ssr/output/sessao_20260930_141639` (A), `_141640` (B), `_141641` (C). O consolidado (`clubinho_ssr_set2026_consolidado.csv`) fica fora do repo porque tem `id_user`.

## Wiki atualizada
Nenhuma ainda. Pendente: adicionar a divisão por nível do CdL em `bq-planos.md` §Clube do Livro e o caso Clubinho na memória do projeto SSR.
