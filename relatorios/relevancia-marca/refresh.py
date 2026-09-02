#!/usr/bin/env python3
"""
Relatório SNAPSHOT — Relevância de marca × vendas (estudo de 21–25/ago/2026).

Diferente dos relatórios vivos, o data.json daqui NÃO vem de queries BQ diretas:
os números são resultado das 6 rodadas do estudo (pareamento por spend, event
study, mCAC por saltos, Share of Search), produzidos pelos scripts em scripts/
sobre os CSVs de data/. Recalcular exige rodar os scripts — ver ANALISE.md.

Este script só valida o data.json e (com --push) publica. Não sobrescreve dados.

Usage:
  python refresh.py          # valida data.json
  python refresh.py --push   # valida + git add/commit/push
"""

import json, subprocess, sys, datetime
from pathlib import Path

OUT = Path(__file__).parent / "data.json"

REQUIRED_KEYS = [
    "updated_at", "periodo", "readout", "sabatinas_facts", "canais",
    "mcac", "fontes", "sos_facts", "lead_bars", "bolo_bars", "plano",
]

if __name__ == "__main__":
    push = "--push" in sys.argv
    try:
        data = json.loads(OUT.read_text(encoding="utf-8"))
        missing = [k for k in REQUIRED_KEYS if k not in data]
        if missing:
            raise ValueError(f"data.json sem as chaves: {missing}")
        print(f"✓ {OUT.name} válido — snapshot de {data['updated_at']}")
        print("  (relatório snapshot: para recalcular, rodar scripts/*.py — ver ANALISE.md)")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m", f"data: relevancia-marca {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
