#!/usr/bin/env python3
"""Monta data.json do relatório de relevância de marca (versão 17/09/2026).

Fontes de cada bloco estão no campo "fonte" do próprio JSON. O núcleo é recalculado
por scripts/nucleo_corrigido.py (série completa + block bootstrap); os demais blocos vêm
das saídas em data/ e das queries listadas no ANALISE.md.
Uso: python3 refresh.py            (monta data.json)
     python3 refresh.py --nucleo   (roda antes o nucleo_corrigido.py)
"""
import json, subprocess, sys
from pathlib import Path
from datetime import date
B = Path(__file__).parent
if "--nucleo" in sys.argv:
    subprocess.run([sys.executable, str(B/"scripts"/"nucleo_corrigido.py")], check=True)

D = {
"meta": {
  "titulo": "O que o YouTube faz pelas vendas",
  "gerado": date.today().isoformat(),
  "pedido": "Bárbara Olivieri e Luan Licidonio, 14 e 17/09/2026 (#squad-cac e DM)",
  "janela": "01/08/2025 a 12/09/2026 (408 dias); transações íntegras até 15/09",
  "aviso": "Versão de trabalho. Os achados das rodadas 9c a 9e foram retirados após revisão estatística independente — ver Método."
},
"resposta_curta": [
  {"t": "Existe associação, e é forte.", "d": "Dias em que o canal tem mais audiência orgânica têm <b>19,5% mais transações</b> com o mesmo dinheiro de mídia. Resiste a calendário, placebo e mudança de método."},
  {"t": "Mas não conseguimos provar que o vídeo causa a venda.", "d": "O teste decisivo falhou: <b>renovações no cartão</b>, que são cobrança automática e não podem ser causadas por um vídeo de hoje, sobem quase na mesma proporção. A parte específica de venda nova não se distingue de zero."},
  {"t": "E os três dias citados têm explicação interna.", "d": "13 e 15/09 são fechamento do BP10, com Vitalício em 65% e 77% da receita. No fim de semana de 12–13/09, o BP10 explica mais que o crescimento inteiro."}
],
"perguntas": [
  {"quem": "Luan", "p": "Tivemos dois hits no YT (11 de setembro e STF) e o melhor dia de vendas do mês com ótimo CM. Acho pouco provável não terem correlação.",
   "veredito": "Certo sobre o padrão, errado sobre os eventos",
   "r": "Testei os <b>10 maiores vídeos do canal</b> desde agosto de 2025, todos acima de 1 milhão de views. No dia da publicação o efeito é +4,1%; em D+1 e D+2, cerca de +12%, no percentil 91 do placebo — direcional, mas o teste só detectaria efeito acima de <b>22%</b>. Não dá para concluir nem a favor nem contra pelos eventos. O padrão que existe é de <b>regime</b>: dias de canal forte vendem mais. E os dois hits que ele cita são <b>lives de notícia</b>, o formato que menos aparece nas vendas.",
   "n": "10 vídeos acima de 1M de views · MDE 22%"},
  {"quem": "Bárbara", "p": "Google teve o pior desempenho e todo o efeito vem do fechamento de BP10. Tenho clareza que os eventos não são relacionados, mas posso estar errada.",
   "veredito": "Certa no fim de semana, e o dado geral não a contraria",
   "r": "No fim de semana de <b>12 e 13/09 ela está certa</b>: as transações com UTM de BP10 foram de 1.679 para 2.758, um aumento de 1.079, enquanto o total subiu 933 — tudo que não é BP10 caiu 2,5%. Em <b>10 e 11/09</b> o padrão é outro: a receita ficou 24% e 12% acima do esperado com spend 3% e 12% <i>abaixo</i>, o único dos casos em que isso acontece. Sobre o Technocracia ela está certa e pelo motivo certo: a coorte de cadastro assiste e não compra melhor, com 1,26% de conversão.",
   "n": "UTM BP10 · pareamento por mesmo dia da semana"}
],
"bloco1": {
  "titulo": "Bloco 1 — impacto relacionável",
  "itens": [
    {"o": "Métricas do YouTube do período", "s": "entregue",
     "r": "Acesso destravado em 16/09 (era o gap declarado do relatório anterior). <b>11 de Setembro</b>: 2.857.472 views e 4.549 inscritos, com pico de 1,33 milhão em 11/09, terceiro maior do canal desde junho. <b>Marçal</b>: 823.590 views e 5.301 inscritos. <b>Renan</b>: 379.439 views e 3.421 inscritos."},
    {"o": "CTA do YouTube por UTM, do clique ao objetivo da LP", "s": "entregue",
     "r": "Funil completo, de 01/08 a 13/09: <b>26,4 milhões de views</b> no canal geraram <b>14.326 sessões</b> nas landing pages com UTM de YouTube orgânico — 0,054% —, e essas sessões viraram <b>894 leads</b> e <b>834 vendas</b>, R$ 333 mil. A conversão da sessão é alta, 5,8%, porque é tráfego morno que clicou no link da descrição. O gargalo é o passo anterior: de cada 2.000 pessoas que assistem, uma clica. No acumulado de 13 meses o canal rastreia <b>R$ 6,0 milhões</b>, cerca de 1% da receita. Por mil views: live R$ 27, corte R$ 10, Short R$ 3. <b>Os três cases somam 20 vendas e R$ 8 mil</b> — os CTAs apontavam para outro produto, não para o próprio conteúdo.",
     "funil": [["Views do canal", "26.424.747", ""], ["Sessões na LP por UTM", "14.326", "0,054% das views"], ["Leads", "894", "6,2% das sessões"], ["Vendas", "834", "5,8% das sessões"], ["Receita", "R$ 332.685", "R$ 7.561 por dia"]]},
    {"o": "Pesquisa de marca, incluindo portal", "s": "parcial",
     "r": "Share of Search é coincidente e não move eficiência; o portal no Mixpanel tem série curta, desde maio, e serve como descritivo. A peça que falta é o <b>Search Console</b>, única fonte de volume real de busca por query de marca — depende de acesso à propriedade, e o histórico é de apenas 16 meses."},
    {"o": "Redes sociais, do alcance ao faturamento", "s": "entregue, e o caminho não existe",
     "r": "Puxei a Graph API do Instagram, 5,1 milhões de seguidores, série diária desde agosto de 2025. <b>Nenhuma métrica passa no crivo</b>: alcance e engajamento têm correlação 0,6 com o spend, e os cliques no site correlacionam com venda mas os dias de muitos cliques são dias de 10% mais mídia. O que existe e vale usar é o funil rastreado: 8 a 33 mil leads por mês com UTM de Instagram orgânico, convertendo 2% a 4%."}
  ]
},
"bloco2": {
  "titulo": "Bloco 2 — impacto indireto nos outros canais",
  "linhas": [
    {"c": "Transações totais", "e": "+19,5%", "ic": "[+8,6, +42,4]", "p": "0,004", "ok": True},
    {"c": "Receita", "e": "+18,0%", "ic": "[−2,9, +48,6]", "p": "0,114", "ok": False},
    {"c": "CAC de ads", "e": "−13,7%", "ic": "[−25,0, −6,6]", "p": "0,007", "ok": True, "nota": "é o mesmo fato das transações, com o spend pareado"},
    {"c": "Spend (checagem do pareamento)", "e": "+1,2%", "ic": "[−3,7, +10,7]", "p": "0,29", "ok": None},
    {"c": "Ticket médio", "e": "−5,4%", "ic": "[−12,8, +4,3]", "p": "0,29", "ok": False}
  ],
  "nota": "Pareamento por quintil de spend, fim de semana e fase de venda, excluindo abertura e fechamento de campanha. Intervalos por bootstrap de bloco. 262 dias.",
  "canais_titulo": "Por canal de venda",
  "canais_texto": "A quebra por canal responde à pergunta sobre impacto nos outros canais, mas com uma ressalva: com o método corrigido, nenhuma destas linhas sobrevive a uma correção para múltiplas comparações. São direcionais.",
  "canais": [
    {"c": "Orgânico e YouTube", "part": "8% das transações", "e": "+63%", "ic": "[+20, +119]"},
    {"c": "Comercial", "part": "22%", "e": "+31%", "ic": "[+2, +85]"},
    {"c": "Ads (Meta e Google)", "part": "41%", "e": "+21%", "ic": "[+5, +40]"},
    {"c": "CRM", "part": "14%", "e": "+8%", "ic": "cruza zero"}
  ],
  "canais_nota": "O padrão — efeito maior fora da mídia paga — é o que se esperaria de audiência que ativa a base. Mas é também compatível com um fator comum de demanda, e o teste do controle negativo não deixa escolher entre os dois."
},
"cases": [
  {"nome": "Sabatinas — Renan (14/08) e Marçal (17/08)",
   "atencao": "1,20 milhão de views somadas, 8,7 mil inscritos ganhos, 5,8 mil usuários na plataforma",
   "rastreavel": "14 transações, R$ 6,0 mil",
   "nao_rastreavel": "Lift de 1,14× em D+14 na plataforma para os dois, com intervalo cruzando 1. Nos dias, a receita acompanhou o spend, que estava 39% e 147% acima do esperado.",
   "veredito": "Não atribuível. A receita do período é mídia.",
   "extra": "Os dois têm de 10 a 90 vezes mais views que as outras sabatinas e são os únicos sem lift medido. Zema 2,03×, Rebelo 1,82×, Caiado 1,71×. É formato, não fama."},
  {"nome": "STF e Banco Master — os maiores vídeos do canal",
   "atencao": "Master x STF, 03/09: 4.358.295 views, o maior do canal no período. STF julga Moraes, 15/09: 3.522.311 views.",
   "rastreavel": "Master x STF: 408 transações e R$ 58 mil pelo link da descrição, que apontava para assinatura.",
   "nao_rastreavel": "Em 03/09, dia do maior vídeo do ano, as vendas foram as <b>mais baixas da semana</b>: 825 transações, contra 939 na véspera e 934 no dia seguinte. Em 15/09, com o segundo maior vídeo, foi o <b>melhor dia do mês</b>, R$ 1,68 milhão — mas era o fechamento do BP10 com corujão, e o Vitalício respondeu por 77% da receita.",
   "veredito": "Dois vídeos do mesmo tipo e tamanho, resultados opostos. O que difere é o calendário comercial, não o vídeo.",
   "extra": "Este é o contraste mais direto que o dado oferece: se audiência gigante causasse venda, 03/09 teria sido um dia excepcional. Foi o mais fraco da semana."},
  {"nome": "11 de Setembro — live no YouTube em 10/09",
   "atencao": "2,86 milhões de views, 4.549 inscritos, 2.480 usuários na plataforma",
   "rastreavel": "6 transações, R$ 2,1 mil, e 428 leads para o Technocracia",
   "nao_rastreavel": "Em 10 e 11/09 a receita ficou acima do esperado com spend menor. No teste por pessoa, 2,44× em D+3, mas o teste só detecta acima de 3,7×.",
   "veredito": "Parcialmente atribuível em 10 e 11; não no fim de semana, que é BP10.",
   "extra": "Achado de método: a estreia do doc na plataforma em 07/09 era um único usuário de QA. A audiência real começa em 11/09, dia seguinte à live. D+7 fecha em 19/09 e D+14 em 26/09."}
],
"sabatinas": [
  {"n": "Romeu Zema", "v": 40135, "l": "2,03×", "ic": "[1,52–2,56]", "sig": True},
  {"n": "Aldo Rebelo", "v": 12922, "l": "1,82×", "ic": "[1,30–2,40]", "sig": True},
  {"n": "Ronaldo Caiado", "v": 47674, "l": "1,71×", "ic": "[1,15–2,27]", "sig": True},
  {"n": "Ricardo Salles", "v": 16349, "l": "1,39×", "ic": "[0,48–2,03]", "sig": False},
  {"n": "Pablo Marçal", "v": 823590, "l": "1,14×", "ic": "[0,63–1,65]", "sig": False},
  {"n": "Renan Santos", "v": 379439, "l": "1,14×", "ic": "[0,43–1,97]", "sig": False},
  {"n": "Augusto Cury", "v": 53730, "l": "1,10×", "ic": "[0,72–1,49]", "sig": False},
  {"n": "Caroline de Toni", "v": 0, "l": "1,10×", "ic": "[0,44–2,00]", "sig": False},
  {"n": "Guilherme Derrite", "v": 9028, "l": "1,04×", "ic": "[0,29–1,96]", "sig": False}
],
"controle_negativo": {
  "titulo": "O teste que mudou a conclusão",
  "texto": "Renovação no cartão é 98,8% das renovações e é cobrança automática na data de aniversário da assinatura. Um vídeo publicado hoje não pode causar uma cobrança automática de hoje. Se ela sobe junto com as vendas novas nos dias de audiência alta, existe um fator comum movendo o dia inteiro.",
  "linhas": [
    {"c": "Vendas novas (o desfecho do estudo)", "e": "+0,174", "ic": "[+0,085, +0,263]", "p": "&lt;0,001"},
    {"c": "Renovação automática no cartão", "e": "+0,116", "ic": "[−0,021, +0,253]", "p": "0,096"},
    {"c": "Razão entre as duas", "e": "+0,058", "ic": "[−0,109, +0,224]", "p": "0,50"}
  ],
  "conclusao": "A razão não responde. A parte do efeito específica de venda nova — a única que o YouTube poderia gerar — não se distingue de zero. Não é dia do mês (p=0,87) nem método de pagamento.",
  "leituras": [
    "Um fator comum de nível de dia — a hipótese que nunca conseguimos descartar.",
    "Mecânica de coorte: quem foi adquirido em dia de audiência alta há 12 meses renova hoje em dia parecido. Nesse caso a renovação é desfecho defasado, não controle.",
    "Controle grosseiro: a renovação varia quase 15 vezes por dia da semana."
  ]
},
"o_que_fazer": [
  {"t": "Encorajamento aleatorizado na base", "prazo": "2 a 3 semanas", "d": "Sortear metade da base para receber o aviso apontando ao vídeo e medir compra em D+1 a D+14 por intenção de tratar. Randomiza no nível da pessoa, usa a régua de CRM que já existe e detecta lift de 1,2×, contra 1,6 a 2,0× do desenho observacional. <b>É o único caminho que separa causa de correlação no prazo do trimestre.</b>"},
  {"t": "Search Console", "prazo": "1 hora depois do acesso", "d": "Acesso de leitura à propriedade para fechar o bloco de pesquisa de marca. O histórico é de 16 meses, então cada semana sem coletar é semana perdida."},
  {"t": "Tagging por vídeo nas telas finais", "prazo": "depende do time de conteúdo", "d": "Hoje os CTAs dos programas grandes apontam para a campanha da vez, não para o próprio conteúdo. Por isso os três cases rastreiam R$ 8 mil. Com UTM por vídeo, o bloco rastreável deixa de ser cego."},
  {"t": "Aleatorizar o dia de estreia de conteúdo evergreen", "prazo": "programa de 12 meses", "d": "Sortear a data dentro de pares bloqueados por dia da semana e fase de campanha torna a audiência exógena no nível do dia. Custo zero em dinheiro, algum em agenda editorial."}
],
"metodo": {
  "desenho": "Comparação de dias com audiência orgânica acima e abaixo da mediana, dentro de estratos de quintil de spend, fim de semana e fase de venda. Audiência é views de vídeo longo pela API do YouTube Analytics, excluindo anúncio e Shorts. Intervalos por bootstrap de bloco, que respeita a autocorrelação da série.",
  "validacoes": [
    "Spend pareado: os dois grupos gastam o mesmo (+1,2%, não significativo).",
    "Calendário completo: excluindo estreias, aberturas, fechamentos, lotes e ofertas novas, o efeito permanece.",
    "Placebo por deslocamento circular: o efeito fica fora da banda do acaso.",
    "Controle negativo com views pagas: dias de mais anúncio em vídeo têm CAC pior, o oposto do orgânico.",
    "Controle negativo com renovações: FALHA — é o que impede a leitura causal."
  ],
  "limites": [
    "Nenhum teste observacional descarta um fator comum: uma pauta quente move audiência e vendas ao mesmo tempo.",
    "A revisão independente derrubou os achados das rodadas 9c a 9e — mecanismo do Comercial, histerese, corte de views, LTV sobre CAC e o teste dos vídeos grandes. Não foram usados aqui.",
    "Os intervalos das versões anteriores deste relatório estavam de 1,6 a 1,9 vezes estreitos demais.",
    "A audiência do YouTube não é endereçável por região, então não existe geo holdout para o canal."
  ]
}
}
(B/"data.json").write_text(json.dumps(D, ensure_ascii=False, indent=1))
print(f"data.json: {len(json.dumps(D))//1024} kB · {len(D)} blocos")
