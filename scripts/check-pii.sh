#!/usr/bin/env bash
# Bloqueio de PII — este repo serve GitHub Pages PÚBLICO.
# Usado pelo hook local de pre-commit (e por CI, se habilitado).
# Em jul/2026 o histórico precisou ser reescrito para remover listas de
# clientes; este check existe para isso nunca se repetir.
# Uso: scripts/check-pii.sh [--staged]   (--staged = só arquivos no index)
set -u

if [ "${1:-}" = "--staged" ]; then
  FILES=$(git diff --cached --name-only --diff-filter=ACM)
else
  FILES=$(git ls-files)
fi
[ -z "$FILES" ] && exit 0

FAIL=0

# 1) Arquivos de dados proibidos
DATA=$(echo "$FILES" | grep -E '\.(csv|xlsx|pdf)$' | grep -v '_template/' || true)
if [ -n "$DATA" ]; then
  echo "❌ Arquivos de dados num repo público:"
  echo "$DATA" | sed 's/^/   /'
  echo "   Listas/exports são entregues FORA do repo (ver CLAUDE.md do BigQuery)."
  FAIL=1
fi

# 2) PII em massa em json/html/md
for f in $(echo "$FILES" | grep -E '\.(json|html|md)$'); do
  [ -f "$f" ] || continue
  EMAILS=$(grep -oE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}' "$f" 2>/dev/null \
    | grep -viE 'brasilparalelo\.com|andreyuitiabe|example\.com|noreply' | sort -u | wc -l | tr -d ' ')
  CPFS=$(grep -oE '[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}' "$f" 2>/dev/null | sort -u | wc -l | tr -d ' ')
  FONES=$(grep -oE '(^|[^0-9.])55[1-9][1-9]9?[0-9]{8}([^0-9.]|$)' "$f" 2>/dev/null | grep -oE '55[0-9]+' | sort -u | wc -l | tr -d ' ')
  if [ "$EMAILS" -gt 5 ] || [ "$CPFS" -gt 0 ] || [ "$FONES" -gt 5 ]; then
    echo "❌ Possível PII em $f: $EMAILS emails únicos, $CPFS CPFs, $FONES telefones"
    FAIL=1
  fi
done

if [ "$FAIL" -eq 1 ]; then
  echo ""
  echo "Anonimizar (agregar, remover contatos) ou entregar fora do repo."
  echo "Para exceção consciente: git commit --no-verify (pense duas vezes)."
  exit 1
fi
exit 0
