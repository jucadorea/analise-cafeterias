-- Checagem de qualidade da tabela transacoes
-- Cada consulta responde a uma pergunta; o resultado esperado está no comentário.

-- 1. Total de linhas e período coberto (esperado: 149.116 linhas, 2023-01-01 a 2023-06-30)
SELECT COUNT(*) AS linhas,
       MIN(transaction_date) AS primeira_data,
       MAX(transaction_date) AS ultima_data,
       COUNT(DISTINCT transaction_date) AS dias_distintos
FROM transacoes;

-- 2. Duplicados em transaction_id (esperado: 0)
SELECT COUNT(*) - COUNT(DISTINCT transaction_id) AS ids_duplicados
FROM transacoes;

-- 3. Nulos por coluna (esperado: 0 em todas)
SELECT SUM(transaction_date IS NULL)  AS data_nula,
       SUM(transaction_time IS NULL)  AS hora_nula,
       SUM(store_location   IS NULL)  AS loja_nula,
       SUM(product_id       IS NULL)  AS produto_nulo,
       SUM(transaction_qty  IS NULL)  AS qtd_nula,
       SUM(unit_price       IS NULL)  AS preco_nulo,
       SUM(total_bill       IS NULL)  AS total_nulo
FROM transacoes;

-- 4. Quantidades e preços inválidos (esperado: 0)
SELECT SUM(transaction_qty <= 0) AS qtd_invalida,
       SUM(unit_price <= 0)      AS preco_invalido,
       SUM(total_bill <= 0)      AS total_invalido
FROM transacoes;

-- 5. Total_Bill coerente com quantidade x preço unitário (esperado: 0 linhas divergentes)
SELECT COUNT(*) AS linhas_divergentes
FROM transacoes
WHERE ABS(total_bill - transaction_qty * unit_price) > 0.005;

-- 6. Distribuição da quantidade por transação (procure valores extremos)
SELECT transaction_qty, COUNT(*) AS transacoes
FROM transacoes
GROUP BY transaction_qty
ORDER BY transaction_qty;

-- 7. Lojas: cada store_id deve ter um único nome (esperado: 3 linhas, 1 nome por id)
SELECT store_id, store_location, COUNT(*) AS transacoes
FROM transacoes
GROUP BY store_id, store_location;

-- 8. Produtos com mais de um preço unitário (esperado: 0; se houver, o preço mudou ou há erro)
SELECT product_id, COUNT(DISTINCT unit_price) AS precos_distintos
FROM transacoes
GROUP BY product_id
HAVING COUNT(DISTINCT unit_price) > 1;

-- 9. Produtos com mais de uma categoria ou tipo (esperado: 0)
SELECT product_id,
       COUNT(DISTINCT product_category) AS categorias,
       COUNT(DISTINCT product_type)     AS tipos
FROM transacoes
GROUP BY product_id
HAVING categorias > 1 OR tipos > 1;

-- 10. Mês da coluna month coerente com a data (esperado: 0 linhas divergentes)
SELECT COUNT(*) AS linhas_divergentes
FROM transacoes
WHERE CAST(strftime('%m', transaction_date) AS INTEGER) <> month;

-- 11. Horários de funcionamento (hora em que há vendas; procure horas fora do esperado)
SELECT hour, COUNT(*) AS transacoes
FROM transacoes
GROUP BY hour
ORDER BY hour;

-- 12. Transações por dia: dias sem venda ou com volume muito fora do padrão
SELECT transaction_date, COUNT(*) AS transacoes
FROM transacoes
GROUP BY transaction_date
ORDER BY transacoes ASC
LIMIT 5;
