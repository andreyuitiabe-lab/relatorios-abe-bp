/* Influenciadores — fechamento. Código comum às duas páginas (resumo e detalhado).

   O data.json traz dois recortes em `views`:
     todos        — todo anúncio com peça de influenciador
     recorrentes  — só os influs com contrato recorrente (D.meta.recorrentes)
   O toggle troca o recorte de TODOS os gráficos e tabelas e dos números marcados no
   texto com data-v. Bloco com data-only="todos|recorrentes" só aparece naquele recorte.
   O botão de mês ([data-vp]) troca o período: os dois meses juntos ou um mês só
   (D.periodos). Recorte e mês vão na URL (#recorrentes, #set, #recorrentes-set) para
   dar para mandar o link já filtrado. */
(function () {
const REL = {};
window.REL = REL;

/* ── formatação ─────────────────────────────────────────── */
const BRL  = v => 'R$ ' + Math.round(v).toLocaleString('pt-BR');
const BRLk = v => v >= 1000 ? 'R$ ' + (v / 1000).toFixed(v >= 10000 ? 0 : 1).replace('.', ',') + ' mil' : 'R$ ' + Math.round(v);
const NUM  = v => v.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
const RET  = v => 'R$ ' + NUM(v);
/* ROI = retorno sobre o gasto, em %. É o "cada R$ 1" menos 1: R$ 1,55 -> +55%. */
const ROI  = x => (x < 0 ? '−' : '+') + Math.round(Math.abs(x) * 100) + '%';
const PCT  = x => Math.round(x * 100) + '%';
const INT  = v => Math.round(v).toLocaleString('pt-BR');
REL.fmt = {BRL, BRLk, NUM, RET, ROI, PCT, INT};
const FMT = {brl: BRL, brlk: BRLk, ret: RET, roi: ROI, pct: PCT, int: INT, txt: v => v};

const MES_NOME = {'01': 'jan', '02': 'fev', '03': 'mar', '04': 'abr', '05': 'mai', '06': 'jun',
                  '07': 'jul', '08': 'ago', '09': 'set', '10': 'out', '11': 'nov', '12': 'dez'};
REL.mesNome = m => MES_NOME[m.slice(-2)];

let MEDIA = 1.46;
function verdict(custo, r) {
  if (!custo || custo < 100) return {cls: 'none', ic: '○', txt: 'sem gasto no período'};
  const x = r / custo;
  if (x >= MEDIA) return {cls: 'ok',  ic: '▲', txt: 'acima da média'};
  if (x >= 1)     return {cls: 'mid', ic: '●', txt: 'se pagou'};
  return {cls: 'bad', ic: '▼', txt: 'não se pagou'};
}
const pill = v => `<span class="pill ${v.cls}"><span class="ic">${v.ic}</span>${v.txt}</span>`;
const hit = d => d.ads ? d.rodou / d.ads : null;
const corRet = vd => vd.cls === 'ok' ? ' style="color:var(--good-ink);font-weight:600"'
                   : vd.cls === 'bad' ? ' style="color:var(--crit-ink);font-weight:600"' : '';
REL.verdict = verdict; REL.pill = pill;

/* ── tooltip ─────────────────────────────────────────────── */
let tip;
function showTip(e, html) {
  tip.innerHTML = html; tip.style.opacity = '1';
  const r = tip.getBoundingClientRect();
  let x = e.clientX + 14, y = e.clientY - r.height - 10;
  if (x + r.width > window.innerWidth - 8) x = e.clientX - r.width - 14;
  if (y < 8) y = e.clientY + 18;
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
}
const hideTip = () => { tip.style.opacity = '0'; };
function bindTip(el, html) {
  el.classList.add('hit'); el.setAttribute('tabindex', '0');
  el.addEventListener('mousemove', e => showTip(e, html));
  el.addEventListener('mouseleave', hideTip);
  el.addEventListener('focus', () => {
    const b = el.getBoundingClientRect();
    showTip({clientX: b.left + b.width / 2, clientY: b.top}, html);
  });
  el.addEventListener('blur', hideTip);
}
REL.bindTip = bindTip;

const SVGNS = 'http://www.w3.org/2000/svg';
function el(tag, attrs) {
  const n = document.createElementNS(SVGNS, tag);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  return n;
}
REL.el = el;

/* ── estado: recorte atual ──────────────────────────────── */
let D, VIEW = 'todos', PER = 'total';
const renders = [];
REL.onRender = fn => renders.push(fn);

const LABEL = {todos: 'Todos os influenciadores', recorrentes: 'Só os recorrentes'};

const P = () => D.periodos[PER];
REL.periodo = () => PER;
/* meses do período escolhido, no formato AAAA-MM */
REL.mesesSel = () => PER === 'total' ? D.meta.meses : [PER];

/* números derivados que o texto cita e que não vêm prontos no data.json */
function calc(V, view) {
  const r = V.receita, g = V.gasto;
  const so_canal = view === 'todos';
  return {
    n_cache: Object.keys(V.cache).length,
    pct_comercial: r.anuncio_total ? r.anuncio_comercial / r.anuncio_total : 0,
    pct_atrasada: r.anuncio_total ? r.venda_atrasada / r.anuncio_total : 0,
    pct_cache: g.total ? g.cache / g.total : 0,
    share_meta: g.midia / P().casa.spend_meta_total,
    hit: V.pecas.no_ar ? V.pecas.escaladas / V.pecas.no_ar : 0,
    receita_canal: so_canal ? r.canal_total : r.anuncio_total,
    vendas_canal: so_canal ? r.vendas_total + r.vendas_lead_parceria + r.vendas_link_proprio : r.vendas_total,
    periodo_txt: PER === 'total' ? 'em dois meses' : 'em ' + NOME_MES_LONGO[PER.slice(-2)],
    n_influs_pagos: V.influs.filter(d => d.s >= 100 && !d.n.startsWith('Outros')).length,
  };
}

function resolve(path, ctx) {
  return path.split('.').reduce((o, k) => (o == null ? o : o[k]), ctx);
}

function apply() {
  const V = P()[VIEW];
  MEDIA = P().casa.retorno_medio_casa_caixa;
  const ctx = {...V, calc: calc(V, VIEW), casa: P().casa, mensal: D.mensal, D};
  document.querySelectorAll('[data-v]').forEach(n => {
    const v = resolve(n.dataset.v, ctx);
    n.textContent = v == null ? '—' : (FMT[n.dataset.f || 'txt'])(v);
  });
  document.querySelectorAll('[data-only]').forEach(n => { n.hidden = n.dataset.only !== VIEW; });
  document.querySelectorAll('.vt button').forEach(b => {
    const on = b.dataset.view ? b.dataset.view === VIEW : b.dataset.per === PER;
    b.classList.toggle('on', on); b.setAttribute('aria-pressed', on);
  });
  document.querySelectorAll('[data-vt-label]').forEach(n => { n.textContent = LABEL[VIEW]; });
  /* o texto de análise é dos dois meses juntos; com um mês só, avisa */
  document.querySelectorAll('[data-per-note]').forEach(n => {
    n.hidden = PER === 'total';
    n.textContent = PER === 'total' ? '' : `Mostrando só ${NOME_MES_LONGO[PER.slice(-2)]}. Os gráficos, tabelas e números destacados são do mês; os parágrafos de análise falam de agosto e setembro juntos.`;
  });
  renders.forEach(fn => fn(V, VIEW));
  checa(V);
}

const NOME_MES_LONGO = {'08': 'agosto', '09': 'setembro', '10': 'outubro', '11': 'novembro', '12': 'dezembro',
  '01': 'janeiro', '02': 'fevereiro', '03': 'março', '04': 'abril', '05': 'maio', '06': 'junho', '07': 'julho'};

function hash() {
  const partes = [VIEW === 'todos' ? '' : VIEW, PER === 'total' ? '' : REL.mesNome(PER)].filter(Boolean);
  history.replaceState(null, '', partes.length ? '#' + partes.join('-') : location.pathname + location.search);
}
REL.setView = function (view) {
  if (!D.periodos.total[view] || view === VIEW) return;
  VIEW = view; hash(); apply();
};
REL.setPeriodo = function (per) {
  if (!D.periodos[per] || per === PER) return;
  PER = per; hash(); apply();
};

/* toggle: um controle em cada [data-vt] — clicar em qualquer um muda a página inteira */
function mountToggles() {
  const n = D.meta.recorrentes.length;
  document.querySelectorAll('[data-vp]').forEach(host => {
    host.classList.add('vt');
    host.setAttribute('role', 'group');
    host.setAttribute('aria-label', 'Período dos gráficos e tabelas');
    host.innerHTML = `<button type="button" data-per="total">${D.meta.meses.map(REL.mesNome).join(' + ')}</button>` +
      D.meta.meses.map(m => `<button type="button" data-per="${m}">${REL.mesNome(m)}</button>`).join('');
    host.addEventListener('click', e => {
      const b = e.target.closest('button[data-per]');
      if (b) REL.setPeriodo(b.dataset.per);
    });
  });
  document.querySelectorAll('[data-vt]').forEach(host => {
    host.classList.add('vt');
    host.setAttribute('role', 'group');
    host.setAttribute('aria-label', 'Recorte dos gráficos e tabelas');
    host.innerHTML =
      `<button type="button" data-view="todos">Todos</button>` +
      `<button type="button" data-view="recorrentes" title="${D.meta.recorrentes.join(', ')}">Recorrentes <span class="n">${n}</span></button>`;
    host.addEventListener('click', e => {
      const b = e.target.closest('button[data-view]');
      if (b) REL.setView(b.dataset.view);
    });
  });
}

/* guarda de consistência: o texto narrativo é escrito à mão a cada fechamento.
   Se o data.json mudar e o texto não for revisto, isto avisa no console. */
function checa(V) {
  const som = (a, k) => a.reduce((t, d) => t + (d[k] || 0), 0);
  [['anúncio',  Math.round(som(V.influs, 's')),                   V.gasto.midia],
   ['cachê',    Math.round(som(V.influs, 'f')),                   V.gasto.cache],
   ['receita',  Math.round(som(V.influs, 'ra') + som(V.influs, 'rc')), V.receita.anuncio_total],
   ['peças',    som(V.influs, 'ads'),                             V.pecas.no_ar],
   ['escaladas',som(V.influs, 'rodou'),                           V.pecas.escaladas]
  ].forEach(([nome, c, decl]) => {
    if (Math.abs(c - decl) > 2) console.warn(`[influs:${VIEW}] ${nome}: soma ${c} x declarado ${decl}`);
  });
}

REL.init = async function () {
  D = await (await fetch('./data.json')).json();
  tip = document.getElementById('tip');
  mountToggles();
  /* #recorrentes, #set, #recorrentes-set */
  location.hash.slice(1).split('-').forEach(t => {
    if (D.periodos.total[t]) VIEW = t;
    const m = D.meta.meses.find(x => REL.mesNome(x) === t);
    if (m) PER = m;
  });
  apply();
  return D;
};
REL.data = () => D;

/* ── tabelas e gráficos comuns ──────────────────────────── */

/* cachê por influenciador, mês a mês */
REL.tblCache = function (id) {
  REL.onRender((V, view) => {
    const t = document.getElementById(id);
    const meses = REL.mesesSel(), um = meses.length === 1;
    const nomes = Object.keys(V.cache).sort((a, b) => V.cache[b] - V.cache[a]);
    const tot = meses.map(() => 0);
    t.innerHTML =
      `<thead><tr><th>Cachê de peça de venda</th>${meses.map(m => `<th>${REL.mesNome(m)}</th>`).join('')}${um ? '' : '<th>Total</th>'}</tr></thead>` +
      '<tbody>' + nomes.map(n => '<tr><td>' + n + '</td>' + meses.map((m, i) => {
        const v = D.mensal[m][view].cache[n] || 0; tot[i] += v;
        return `<td class="mono${v ? '' : ' zero'}">${v ? BRL(v) : '—'}</td>`;
      }).join('') + (um ? '' : `<td class="mono">${BRL(V.cache[n])}</td>`) + '</tr>').join('') + '</tbody>' +
      `<tfoot><tr><td>Total</td>${tot.map(v => `<td class="mono">${BRL(v)}</td>`).join('')}${um ? '' : `<td class="mono">${BRL(V.gasto.cache)}</td>`}</tr></tfoot>`;
  });
};

/* como a venda chegou. Link próprio e lead de parceria não têm influ atribuível, então
   só aparecem no recorte "todos". */
REL.tblCaminhos = function (id, opts = {}) {
  REL.onRender((V, view) => {
    const r = V.receita;
    const linhas = [
      ['var(--s1)', 1, opts.direto || '<strong>Comprou sozinho, pelo anúncio</strong>', r.anuncio_direto, null],
      ['var(--s1)', .45, opts.comercial || '<strong>Fechou com o time comercial</strong> <span class="src">veio do anúncio, mas quem converteu foi o time</span>', r.anuncio_comercial, null],
    ];
    if (view === 'todos') linhas.push(
      ['var(--s2)', 1, 'Virou lead numa parceria e fechou depois', r.lead_parceria, r.vendas_lead_parceria],
      ['var(--s3)', 1, 'Usou o link do influenciador', r.link_proprio, r.vendas_link_proprio]);
    const total = linhas.reduce((t, l) => t + l[3], 0);
    const vendasTot = view === 'todos' ? r.vendas_total + r.vendas_lead_parceria + r.vendas_link_proprio : r.vendas_total;
    document.getElementById(id).innerHTML =
      '<thead><tr><th>Como a venda chegou</th><th>Receita</th><th>Vendas</th><th>Peso</th></tr></thead><tbody>' +
      linhas.map(([cor, op, txt, v, n], i) =>
        `<tr><td><span class="swatch" style="background:${cor};opacity:${op}"></span>${txt}</td>` +
        `<td class="mono">${BRL(v)}</td><td class="mono">${n == null ? (i === 0 ? INT(r.vendas_total) + '<span class="src"> no anúncio</span>' : '') : INT(n)}</td>` +
        `<td class="mono">${PCT(v / total)}</td></tr>`).join('') +
      `</tbody><tfoot><tr><td>Total</td><td class="mono">${BRL(total)}</td><td class="mono">${INT(vendasTot)}</td><td class="mono">100%</td></tr></tfoot>`;
  });
};

/* ROI em três degraus de exigência */
REL.tblRoi = function (id) {
  REL.onRender(V => {
    const g = V.gasto.total, r = V.receita;
    const rows = [['Tudo que entrou no caixa no período', r.anuncio_total],
                  ['Só as peças que rodaram no período', r.peca_que_rodou],
                  ['Só o que o próprio anúncio fechou', r.anuncio_direto]];
    document.getElementById(id).innerHTML =
      '<thead><tr><th>Base de cálculo</th><th>Voltou</th><th>Sobrou</th><th>ROI</th></tr></thead><tbody>' +
      rows.map(([t, v]) => {
        const x = v / g - 1, c = x >= 0.2 ? 'var(--good-ink)' : x >= 0 ? 'var(--warn-ink)' : 'var(--crit-ink)';
        return `<tr><td>${t}</td><td class="mono">${BRL(v)}</td>` +
          `<td class="mono" style="color:${c}">${x < 0 ? '− ' : '+ '}${BRL(Math.abs(v - g))}</td>` +
          `<td class="mono" style="color:${c};font-weight:600">${ROI(x)}</td></tr>`;
      }).join('') + '</tbody>';
  });
};

/* mês a mês, com a média da casa na mesma régua (só mídia, só peça que rodou) */
REL.tblMensal = function (id) {
  REL.onRender((V, view) => {
    const cols = D.meta.meses.map(m => ({t: REL.mesNome(m), v: D.mensal[m][view], casa: D.mensal[m].casa}));
    /* esta tabela é a comparação entre meses: mostra sempre todos, seja qual for o mês escolhido */
    cols.push({t: 'Período', v: D.periodos.total[view], casa: D.periodos.total.casa, tot: true});
    const linha = (rot, f, cls = '') => `<tr${cls}><td>${rot}</td>` +
      cols.map(c => `<td class="mono"${c.tot ? ' style="font-weight:600"' : ''}>${f(c)}</td>`).join('') + '</tr>';
    const rc = x => x == null ? '—' : `<span style="color:${x >= 1 ? 'inherit' : 'var(--crit-ink)'}">${RET(x)}</span>`;
    document.getElementById(id).innerHTML =
      `<thead><tr><th></th>${cols.map(c => `<th>${c.t}</th>`).join('')}</tr></thead><tbody>` +
      linha('Gastamos (anúncio + cachê)', c => BRL(c.v.gasto.total)) +
      linha('<span class="src">dos quais cachê</span>', c => BRL(c.v.gasto.cache)) +
      linha('Voltou pelo anúncio', c => BRL(c.v.receita.anuncio_total)) +
      linha('Cada R$ 1 virou — caixa', c => rc(c.v.retorno.caixa)) +
      linha('Cada R$ 1 virou — só o que rodou', c => rc(c.v.retorno.so_pecas_que_rodaram)) +
      '<tr class="sub-head"><td colspan="' + (cols.length + 1) + '">Mesma régua da casa: só anúncio, só peça que rodou</td></tr>' +
      linha('Influenciadores', c => RET(c.v.retorno.midia_so_ativas)) +
      linha('Média da Brasil Paralelo', c => RET(c.casa.retorno_medio_casa_so_ativas)) +
      '</tbody>';
  });
};

/* barras: gasto (anúncio + cachê) x retorno, por influenciador */
REL.chartInflus = function (id, opts = {}) {
  REL.onRender(V => {
    const data = V.influs.filter(d => d.s > 0 || d.f > 0 || d.r > 0);
    const rowH = 36, padL = opts.padL || 168, padR = 112, padT = 4, padB = 28;
    const W = 900, H = padT + data.length * rowH + padB;
    const max = Math.max(...data.map(d => Math.max(d.s + d.f, d.r)));
    const x = v => padL + (v / max) * (W - padL - padR);
    const svg = el('svg', {viewBox: `0 0 ${W} ${H}`, role: 'img',
      'aria-label': 'Gasto com anúncio e cachê comparado à venda gerada, por influenciador'});

    [0, max / 2, max].forEach(t => {
      svg.appendChild(el('line', {x1: x(t), x2: x(t), y1: padT, y2: H - padB, stroke: 'var(--rule)', 'stroke-width': 1}));
      const tx = el('text', {x: x(t), y: H - padB + 17, 'text-anchor': t === 0 ? 'start' : 'middle', fill: 'var(--muted)', 'font-size': 11});
      tx.textContent = t === 0 ? '0' : BRLk(t);
      svg.appendChild(tx);
    });

    data.forEach((d, i) => {
      const y = padT + i * rowH, bh = 11, gap = 2;
      const custo = d.s + d.f, vd = verdict(custo, d.r);
      const ret = custo >= 100 ? d.r / custo : null;

      const lbl = el('text', {x: padL - 12, y: y + rowH / 2 + (d.f > 0 ? -4 : 1), 'text-anchor': 'end',
        fill: 'var(--ink)', 'font-size': 12, 'dominant-baseline': 'middle'});
      lbl.textContent = d.n.length > 22 ? d.n.slice(0, 21) + '…' : d.n;
      svg.appendChild(lbl);
      if (d.f > 0) {
        const tag = el('text', {x: padL - 12, y: y + rowH / 2 + 12, 'text-anchor': 'end', fill: 'var(--muted)', 'font-size': 9.5});
        tag.textContent = '+ cachê';
        svg.appendChild(tag);
      }

      const g = el('g', {});
      g.appendChild(el('rect', {x: 0, y: y, width: W, height: rowH, fill: 'transparent'}));
      /* anúncio + cachê num único traço — a divisão vive na tabela e no tooltip */
      if (custo > 0) g.appendChild(el('rect', {x: padL, y: y + rowH / 2 - bh - gap / 2,
        width: Math.max(x(custo) - padL, 1.5), height: bh, rx: 3, fill: 'var(--s1)'}));
      if (d.r > 0) g.appendChild(el('rect', {x: padL, y: y + rowH / 2 + gap / 2,
        width: Math.max(x(d.r) - padL, 1.5), height: bh, rx: 3, fill: 'var(--s2)'}));
      if (ret !== null) {
        const color = vd.cls === 'ok' ? 'var(--good-ink)' : vd.cls === 'bad' ? 'var(--crit-ink)' : 'var(--ink-2)';
        const rl = el('text', {x: Math.max(x(custo), x(d.r)) + 10, y: y + rowH / 2 + 1, fill: color,
          'font-size': 11.5, 'dominant-baseline': 'middle', 'font-weight': vd.cls === 'mid' ? 400 : 600});
        rl.textContent = RET(ret);
        g.appendChild(rl);
      }
      bindTip(g, `<div class="t-name">${d.n}</div>
        <div class="t-row"><span>Anúncio</span><span>${d.s >= 1 ? BRL(d.s) : '—'}</span></div>
        <div class="t-row"><span>Cachê</span><span>${d.f ? BRL(d.f) : '—'}</span></div>
        <div class="t-row"><span>Voltou</span><span>${BRL(d.r)}</span></div>
        <div class="t-row"><span>&nbsp;&nbsp;venda atrasada</span><span>${d.rc ? BRL(d.rc) : '—'}</span></div>
        <div class="t-row"><span>Cada R$ 1 virou</span><span>${ret === null ? '—' : RET(ret)}</span></div>
        <div class="t-row"><span>Só o que rodou</span><span>${custo >= 100 ? RET(d.ra / custo) : '—'}</span></div>
        <div class="t-row"><span>Fechada pelo comercial</span><span>${d.r ? PCT(d.rcom / d.r) : '—'}</span></div>
        <div class="t-row"><span>Peças · escaladas</span><span>${d.ads} · ${d.rodou}</span></div>
        <div class="t-verdict">${pill(vd)}</div>`);
      svg.appendChild(g);
    });
    const host = document.getElementById(id);
    host.replaceChildren(svg);
  });
};

/* tabela por influenciador. detalhado = colunas de venda atrasada e comercial */
REL.tblInflus = function (id, detalhado) {
  REL.onRender(V => {
    const t = document.getElementById(id);
    const head = ['Influenciador', 'Gastamos', 'Voltou']
      .concat(detalhado ? ['Venda atrasada', 'Fechada pelo comercial'] : [])
      .concat(['Cada R$ 1', 'Só o que rodou', 'Situação', 'Peças enviadas', 'Escaladas', 'Hit rate']);
    let ts = 0, tf = 0, tr = 0, tra = 0, tc = 0, tcom = 0, tads = 0, trod = 0;
    const rows = V.influs.map(d => {
      const custo = d.s + d.f, vd = verdict(custo, d.r);
      ts += d.s; tf += d.f; tr += d.r; tra += d.ra; tc += d.rc; tcom += d.rcom; tads += d.ads; trod += d.rodou;
      const ativo = custo >= 100 ? d.ra / custo : null, h = hit(d);
      const pCauda = d.r ? d.rc / d.r : 0, pCom = d.r ? d.rcom / d.r : 0;
      const corHit = h === null ? '' : h < 0.15 ? ' style="color:var(--crit-ink);font-weight:600"'
                   : h >= 0.5 ? ' style="color:var(--good-ink);font-weight:600"' : '';
      return '<tr>' +
        `<td>${d.n}${d.f ? ` <span class="src">+ cachê ${BRL(d.f)}</span>` : ''}</td>` +
        `<td>${custo >= 1 ? BRL(custo) : '—'}</td><td>${BRL(d.r)}</td>` +
        (detalhado ?
          `<td${pCauda >= 0.3 ? ' style="color:var(--warn-ink);font-weight:600"' : ' class="zero"'}>${d.rc ? BRL(d.rc) + ' · ' + PCT(pCauda) : '—'}</td>` +
          `<td${pCom >= 0.5 ? ' style="color:var(--warn-ink);font-weight:600"' : ' class="zero"'}>${d.rcom ? PCT(pCom) : '—'}</td>` : '') +
        `<td${corRet(vd)}>${custo >= 100 ? RET(d.r / custo) : '—'}</td>` +
        `<td${ativo !== null && ativo < 1 ? ' style="color:var(--crit-ink);font-weight:600"' : ''}>${ativo === null ? '—' : RET(ativo)}</td>` +
        `<td>${pill(vd)}</td><td>${d.ads}</td><td>${d.rodou}</td>` +
        `<td${corHit}>${h === null ? '—' : PCT(h)}</td></tr>`;
    });
    t.innerHTML = `<thead><tr>${head.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody>` +
      `<tfoot><tr><td>Total</td><td>${BRL(ts + tf)}</td><td>${BRL(tr)}</td>` +
      (detalhado ? `<td>${BRL(tc)} · ${PCT(tc / tr)}</td><td>${PCT(tcom / tr)}</td>` : '') +
      `<td>${RET(tr / (ts + tf))}</td><td>${RET(tra / (ts + tf))}</td>` +
      `<td>${pill(verdict(ts + tf, tr))}</td><td>${tads}</td><td>${trod}</td><td>${PCT(trod / tads)}</td></tr></tfoot>`;
  });
};

/* melhores anúncios — dias no ar contados por dia COM veiculação (impressões > 0) */
REL.tblAds = function (id) {
  REL.onRender(V => {
    const rows = V.ads_top.map(d => {
      const vd = verdict(d.s, d.r);
      return `<tr><td style="white-space:normal">${d.ad}</td><td>${d.s >= 1 ? BRL(d.s) : '—'}</td>` +
        `<td>${BRL(d.r)}</td><td${corRet(vd)}>${d.s >= 100 ? RET(d.r / d.s) : '—'}</td>` +
        `<td>${pill(vd)}</td><td>${d.v}</td>` +
        `<td${d.d === 0 ? ' class="zero"' : ''}>${d.d === 0 ? 'não rodou' : d.d + ' dias'}</td></tr>`;
    });
    document.getElementById(id).innerHTML =
      '<thead><tr><th>Anúncio</th><th>Anúncio pago</th><th>Voltou</th><th>Cada R$ 1</th><th>Situação</th><th>Vendas</th><th>Dias no ar</th></tr></thead>' +
      `<tbody>${rows.join('')}</tbody>`;
  });
};

/* por campanha */
REL.tblCamp = function (id) {
  REL.onRender(V => {
    let ts = 0, tr = 0, tv = 0;
    const rows = V.campanhas.map(d => {
      ts += d.s; tr += d.r; tv += d.v;
      const vd = verdict(d.s, d.r);
      return `<tr><td>${d.n}</td><td>${d.s >= 1 ? BRL(d.s) : '—'}</td><td>${BRL(d.r)}</td>` +
        `<td${corRet(vd)}>${d.s >= 100 ? RET(d.r / d.s) : '—'}</td><td>${pill(vd)}</td>` +
        `<td>${d.v}</td><td>${d.v ? BRL(d.r / d.v) : '—'}</td></tr>`;
    });
    document.getElementById(id).innerHTML =
      '<thead><tr><th>Campanha</th><th>Anúncio pago</th><th>Voltou</th><th>Cada R$ 1</th><th>Situação</th><th>Vendas</th><th>Valor médio da venda</th></tr></thead>' +
      `<tbody>${rows.join('')}</tbody>` +
      `<tfoot><tr><td>Total</td><td>${BRL(ts)}</td><td>${BRL(tr)}</td><td>${RET(tr / ts)}</td>` +
      `<td>${pill(verdict(ts, tr))}</td><td>${tv}</td><td>${BRL(tr / tv)}</td></tr></tfoot>`;
  });
};
})();
