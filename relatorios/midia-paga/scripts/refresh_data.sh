#!/bin/bash
# Atualiza todos os datasets usados nas análises de mídia paga.
# Roda as queries de queries/ e salva em ~/meu_projeto/BigQuery/dados/midia_paga/
#
# Uso: bash refresh_data.sh

set -euo pipefail

PROJECT_ID="bp-datawarehouse"
QUERIES_DIR="$(dirname "$0")/../queries"
OUTPUT_DIR="$HOME/meu_projeto/BigQuery/dados/midia_paga"
mkdir -p "$OUTPUT_DIR"

run_query() {
  local sql_file="$1"
  local output_csv="$2"
  echo "→ $sql_file → $output_csv"
  bq query --use_legacy_sql=false --format=csv --max_rows=20000 \
    --project_id="$PROJECT_ID" --quiet < "$QUERIES_DIR/$sql_file" 2>/dev/null > "$output_csv"
  local lines=$(wc -l < "$output_csv")
  echo "  ✓ $lines linhas"
}

echo "== Refresh dados mídia paga =="

run_query "daily_spend_venda.sql"     "$OUTPUT_DIR/daily_spend_venda.csv"
run_query "scatter_campaign_daily.sql" "$OUTPUT_DIR/scatter_campaign_daily.csv"

# All camps (VENDA + LEAD + outros) — usado em segmentação
run_query "all_camps.sql" "/tmp/all_camps.csv"

# Métricas de funil — para análise ad-hoc de hook/CTR
run_query "daily_funnel_metrics.sql" "/tmp/funnel_daily.csv"

echo ""
echo "Feito. Última data disponível:"
tail -1 "$OUTPUT_DIR/daily_spend_venda.csv" | cut -d, -f1
