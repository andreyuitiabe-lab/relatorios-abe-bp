-- EV de referência por faixa (tabela vigente do scorecard).
SELECT nm_band, vl_reference_ev, cd_version FROM `bp-datawarehouse.masterdata.dim_iql_cutoffs`
ORDER BY CASE nm_band WHEN 'A+' THEN 0 WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 ELSE 4 END
