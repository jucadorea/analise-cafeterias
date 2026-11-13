-- Pergunta 3: tendência do faturamento diário (médias móveis de 7 e 30 dias)
-- Mostra só as janelas completas e um dia por semana (domingo), para o resultado ficar curto.
SELECT dia,
       faturamento,
       media_movel_7d,
       media_movel_30d
FROM (
    SELECT dia,
           ROUND(faturamento, 2) AS faturamento,
           ROUND(AVG(faturamento) OVER (ORDER BY dia ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2)  AS media_movel_7d,
           ROUND(AVG(faturamento) OVER (ORDER BY dia ROWS BETWEEN 29 PRECEDING AND CURRENT ROW), 2) AS media_movel_30d,
           COUNT(*) OVER (ORDER BY dia ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS dias_na_janela
    FROM (
        SELECT transaction_date AS dia, SUM(total_bill) AS faturamento
        FROM transacoes
        GROUP BY transaction_date
    )
)
WHERE dias_na_janela = 30
  AND strftime('%w', dia) = '0'
ORDER BY dia;

-- Pergunta 3: padrão semanal (faturamento do dia / média centrada de 7 dias)
-- Índice 100 = dia na média da semana; remove o efeito da tendência de alta.
WITH diario AS (
    SELECT transaction_date AS dia, SUM(total_bill) AS fat
    FROM transacoes
    GROUP BY transaction_date),
c AS (
    SELECT dia, fat,
           AVG(fat)   OVER (ORDER BY dia ROWS BETWEEN 3 PRECEDING AND 3 FOLLOWING) AS mm7c,
           COUNT(*)   OVER (ORDER BY dia ROWS BETWEEN 3 PRECEDING AND 3 FOLLOWING) AS n
    FROM diario)
SELECT CASE strftime('%w', dia)
         WHEN '1' THEN '1 segunda' WHEN '2' THEN '2 terça'  WHEN '3' THEN '3 quarta'
         WHEN '4' THEN '4 quinta'  WHEN '5' THEN '5 sexta'  WHEN '6' THEN '6 sábado'
         ELSE '7 domingo' END AS dia_semana,
       COUNT(*)                     AS dias,
       ROUND(AVG(fat), 0)           AS fat_medio,
       ROUND(100 * AVG(fat / mm7c), 1) AS indice
FROM c
WHERE n = 7
GROUP BY strftime('%w', dia)
ORDER BY (CAST(strftime('%w', dia) AS INTEGER) + 6) % 7;