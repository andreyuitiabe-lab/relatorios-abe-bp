#!/usr/bin/env python3
"""
Refresh do dashboard Resumo BP × BP Ads (funil da newsletter por parceiro).

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push
"""

import datetime
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "data.json"

# Domínios BP / sociais — tudo que NÃO estiver aqui é tratado como anunciante
DOMINIOS_BP = {
    "brasilparalelo.com.br": "Notícias BP",
    "bp.app": "App BP",
    "sitebp.la": "Links BP (encurtador)",
}
DOMINIOS_SOCIAL = {
    "youtube.com": "YouTube BP",
    "youtu.be": "YouTube BP",
    "whatsapp.com": "WhatsApp (canal BP)",
    "instagram.com": "Instagram BP",
    "x.com": "X BP",
}
# Nome amigável dos anunciantes conhecidos (domínio → marca)
PARCEIROS_NOME = {
    "sndflw.com": "Sendflow",
    "vimansca.com.br": "Vimansca",
}
# Domínios externos que são fonte editorial (link de notícia), não anúncio
DOMINIOS_EDITORIAIS = {
    "vatican.va", "google.com", "substack.com", "uol.com.br", "cnnbrasil.com.br",
    "reuters.com", "globo.com", "sympla.com.br", "overton.digital", "docs.google.com",
}


def bq(sql: str, max_rows: int = 5000) -> list[dict]:
    # query via stdin — se passada como argv, um SQL começando com comentário "--"
    # é interpretado como flag pelo bq CLI
    r = subprocess.run(
        ["bq", "query", "--nouse_legacy_sql", "--format=json",
         "--project_id=bp-datawarehouse", f"--max_rows={max_rows}"],
        input=sql, capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(f"stdout: {r.stdout.strip()}\nstderr: {r.stderr.strip()}")
    out = r.stdout.strip()
    return json.loads(out) if out else []


def ii(v) -> int:
    try:
        return int(v) if v not in (None, "", "null") else 0
    except (TypeError, ValueError):
        return 0


def build() -> dict:
    print("  funil por edição...", flush=True)
    funil = bq((HERE / "queries" / "funil_edicao.sql").read_text())
    print("  cliques por domínio...", flush=True)
    dominios = bq((HERE / "queries" / "cliques_dominio.sql").read_text())

    def ed_label(dt: str) -> str:
        d = datetime.date.fromisoformat(dt)
        return f"{d.day:02d}/{d.month:02d}"

    edicoes = [{
        "ed": ed_label(r["dt_envio"]),
        "env": ii(r["qt_enviados"]),
        "ent": ii(r["qt_entregues"]),
        "abrT": ii(r["qt_abridores_total"]),
        "abr": ii(r["qt_abridores_humano"]),
        "cli": ii(r["qt_clicadores"]),
        "unsub": ii(r["qt_unsub"]),
    } for r in funil]

    parceiros: dict = {}
    destinos: dict = {}
    for r in dominios:
        dom = r["nm_dominio"] or ""
        cliq, pes = ii(r["qt_cliques"]), ii(r["qt_clicadores"])
        if dom in DOMINIOS_BP:
            grupo = DOMINIOS_BP[dom]
        elif dom in DOMINIOS_SOCIAL:
            grupo = DOMINIOS_SOCIAL[dom]
        elif dom in DOMINIOS_EDITORIAIS:
            grupo = "Links editoriais externos"
        else:
            nome = PARCEIROS_NOME.get(dom, dom)
            grupo = f"{nome} (anunciante)"
            p = parceiros.setdefault(dom, {"nome": nome, "cliques": []})
            p["cliques"].append({"ed": ed_label(r["dt_envio"]), "cliq": cliq, "pes": pes})
        destinos[grupo] = destinos.get(grupo, 0) + cliq

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "periodo": {"inicio": funil[0]["dt_envio"], "fim": funil[-1]["dt_envio"]} if funil else {},
        "edicoes": edicoes,
        "parceiros": parceiros,
        "destinos": sorted(
            [{"grupo": g, "cliq": c} for g, c in destinos.items()],
            key=lambda d: -d["cliq"]
        ),
    }


def main():
    print("Atualizando data.json...", flush=True)
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(f"OK: {OUT} ({len(data['edicoes'])} edições, {len(data['parceiros'])} anunciantes)")

    if "--push" in sys.argv:
        repo = HERE.parent.parent
        rel = OUT.relative_to(repo)
        subprocess.run(["git", "-C", str(repo), "add", str(rel)], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m",
                        "Atualiza dados: resumo-bp-ads"], check=True)
        subprocess.run(["git", "-C", str(repo), "push", "origin", "main"], check=True)
        print("Push feito.")


if __name__ == "__main__":
    main()
