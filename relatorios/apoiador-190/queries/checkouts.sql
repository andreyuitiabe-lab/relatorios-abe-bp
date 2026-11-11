-- One-click por checkout de entrada, só a partir de 02/11 (antes o one-click não existia em nenhum).
SELECT ck0 AS checkout, COUNT(*) AS pessoas, COUNTIF(up1h) AS up1h
FROM pessoa
WHERE t0 >= '2026-11-02'
GROUP BY 1
HAVING pessoas >= 100
ORDER BY pessoas DESC
