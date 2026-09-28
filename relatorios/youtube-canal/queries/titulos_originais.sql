-- Títulos originais BP assistidos na plataforma desde 2025 — usados para classificar os termos de busca do
-- YouTube em "título nosso" (quem procura o nome de uma produção BP já conhece a marca).
SELECT DISTINCT nm_playlist
FROM `bp-datawarehouse.datamart.obt_kafka__view_sessions`
WHERE DATE(dt_created_at) >= '2025-01-01'
  AND bl_is_original_bp
  AND nm_playlist IS NOT NULL
