-- Camada de dados do dashboard (app/dashboard.py).
-- Cada bloco começa com "-- name: <nome>"; o app lê este arquivo.

-- name: base
-- Uma linha por item vendido, com os nomes de coluna usados no app.
-- O app aplica os filtros (período, loja, produto, dia da semana, hora) sobre esta base.
SELECT date(transaction_date) AS data,
       hour                   AS hora,
       day_of_week            AS dia_semana,   -- 0 = segunda-feira
       store_location         AS loja,
       product_category       AS categoria,
       product_type           AS tipo,
       product_detail         AS produto,
       transaction_qty        AS unidades,
       total_bill             AS faturamento
FROM transacoes;
