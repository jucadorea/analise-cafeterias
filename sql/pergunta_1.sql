-- Pergunta 1: como está a saúde da rede?
-- Cada bloco começa com "-- name: <nome>"; o notebook notebooks/pergunta_1.ipynb lê este arquivo.
-- Obs.: cada linha da tabela é um item vendido (não há id de pedido), então
-- "receita por transação" é a receita média por linha, e não o ticket por cliente.

-- name: kpis
-- Visão geral do período inteiro (esperado: 149.116 transações em 181 dias)
SELECT ROUND(SUM(total_bill), 2)            AS faturamento,
       COUNT(*)                             AS transacoes,
       ROUND(SUM(total_bill) / COUNT(*), 2) AS receita_por_transacao,
       ROUND(AVG(transaction_qty), 2)       AS unidades_por_transacao,
       COUNT(DISTINCT transaction_date)     AS dias
FROM transacoes;

-- name: mensal
-- Faturamento e volume por mês, com o número de dias (fevereiro tem 28)
SELECT strftime('%Y-%m', transaction_date)  AS mes,
       COUNT(DISTINCT transaction_date)     AS dias,
       ROUND(SUM(total_bill), 2)            AS faturamento,
       COUNT(*)                             AS transacoes,
       ROUND(SUM(total_bill) / COUNT(*), 4) AS receita_por_transacao
FROM transacoes
GROUP BY mes
ORDER BY mes;

-- name: mensal_loja
-- Faturamento mensal por loja
SELECT strftime('%Y-%m', transaction_date) AS mes,
       store_location                      AS loja,
       ROUND(SUM(total_bill), 2)           AS faturamento,
       COUNT(*)                            AS transacoes
FROM transacoes
GROUP BY mes, loja
ORDER BY mes, loja;
