#!/usr/bin/env python3
"""Grava em cada card do portal a data do último commit que tocou a pasta do relatório.

Lê os hrefs de relatorios/index.html, consulta o git e escreve (ou atualiza)
o atributo data-updated="AAAA-MM-DD" em cada <a class="card">.

A data da análise (data-date + o texto de .card-date) continua manual: ela diz
quando o número foi apurado, não quando o arquivo mudou.

Uso:
    python3 scripts/atualiza-datas.py           # grava
    python3 scripts/atualiza-datas.py --check   # só relata divergências, não escreve
"""

import io
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PORTAL = RAIZ / "relatorios" / "index.html"

CARD = re.compile(r'<a class="card" href="([^"]+)"([^>]*)>')
UPDATED = re.compile(r'\s*data-updated="[^"]*"')


def ultimo_commit(pasta: str, filhos: list[str]) -> str | None:
    """Data do último commit em relatorios/<pasta>, ignorando sub-relatórios."""
    alvo = f"relatorios/{pasta}"
    cmd = ["git", "log", "-1", "--format=%ad", "--date=short", "--", alvo]
    # um relatório aninhado (campanhas/aniversario-2026/) não conta como
    # atualização do pai (campanhas/) — senão todo pai parece sempre recente
    cmd += [f":!relatorios/{f}" for f in filhos]
    saida = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True)
    return saida.stdout.strip() or None


def main() -> int:
    check = "--check" in sys.argv
    html = io.open(PORTAL, encoding="utf-8").read()
    hrefs = [m.group(1) for m in CARD.finditer(html)]

    faltando, mudou = [], []

    def troca(m: re.Match) -> str:
        href, resto = m.group(1), m.group(2)
        filhos = [h for h in hrefs if h != href and h.startswith(href)]
        data = ultimo_commit(href, filhos)
        if not data:
            faltando.append(href)
            return m.group(0)
        antes = re.search(r'data-updated="([^"]*)"', resto)
        if not antes or antes.group(1) != data:
            mudou.append((href, antes.group(1) if antes else "—", data))
        resto = UPDATED.sub("", resto)
        return f'<a class="card" href="{href}"{resto} data-updated="{data}">'

    novo = CARD.sub(troca, html)

    for href, de, para in mudou:
        print(f"  {href:<44} {de} → {para}")
    for href in faltando:
        print(f"  ! sem histórico no git: {href}")

    if check:
        print(f"\n{len(mudou)} card(s) desatualizado(s).")
        return 1 if mudou else 0

    if novo != html:
        io.open(PORTAL, "w", encoding="utf-8").write(novo)
    print(f"\n{len(mudou)} card(s) atualizado(s) em {PORTAL.relative_to(RAIZ)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
