-- Pergunta 2: o que explica o crescimento da rede? (volume, preço, lojas ou produtos)
-- Abra no DB Browser for SQLite. Para rodar UMA consulta: selecione o texto dela e aperte Ctrl+Enter.
-- Todas usam a tabela transacoes; cada linha da tabela é um item vendido (não há id de pedido).

-- =====================================================================================
-- PARTE A. Os preços da base são confiáveis? (investigação já feita)
-- =====================================================================================

-- A1. Produtos com mais de um preço unitário
-- Resultado: 15 produtos, todos com size = 'Not Defined' (itens sem tamanho).
-- Quase todos os doces têm um segundo preço ~25% maior (biscotti 3,25 e 4,06; croissant 3,75 e 4,69).
SELECT product_id, product_detail, size,
       COUNT(*)                   AS linhas,
       COUNT(DISTINCT unit_price) AS n_precos,
       MIN(unit_price)            AS preco_min,
       MAX(unit_price)            AS preco_max
FROM transacoes
GROUP BY product_id, product_detail, size
HAVING COUNT(DISTINCT unit_price) > 1
ORDER BY n_precos DESC, linhas DESC;

-- A2. Em que lojas aparece cada preço desses produtos
-- Resultado (parcial): os preços mais altos dos scones aparecem só em Lower Manhattan (23 e 15 linhas);
-- Latte cup, camiseta e Organic Decaf Blend têm preços que parecem trocados entre produtos da loja;
-- Ouro Brasileiro shot tem 2,10 e 3,00 em Hell's Kitchen e Lower Manhattan, e nenhum caso em Astoria.
SELECT product_detail, unit_price, store_location, COUNT(*) AS linhas
FROM transacoes
WHERE product_id IN (
    SELECT product_id FROM transacoes
    GROUP BY product_id HAVING COUNT(DISTINCT unit_price) > 1)
GROUP BY product_detail, unit_price, store_location
ORDER BY product_detail, unit_price, store_location;

-- A3. Tamanho do problema: linhas que fogem do preço mais comum (a "moda") de cada produto
-- Resultado: 1.262 linhas (0,85%), US$ 5.160,59 (0,74% do faturamento). Efeito pequeno.
WITH moda AS (
    SELECT product_id, unit_price AS preco_moda
    FROM (SELECT product_id, unit_price,
                 ROW_NUMBER() OVER (PARTITION BY product_id
                                    ORDER BY COUNT(*) DESC) AS rk
          FROM transacoes
          GROUP BY product_id, unit_price)
    WHERE rk = 1)
SELECT COUNT(*) AS linhas_atipicas,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM transacoes), 2) AS pct_linhas,
       ROUND(SUM(t.total_bill), 2) AS fat_atipico,
       ROUND(100 * SUM(t.total_bill) / (SELECT SUM(total_bill) FROM transacoes), 2) AS pct_faturamento
FROM transacoes t
JOIN moda m ON m.product_id = t.product_id
WHERE t.unit_price <> m.preco_moda;

-- A4. Ouro Brasileiro shot: reajuste ou inconsistência?
-- Resultado: 2,10 de 15/01 a 30/06 (750 linhas) e 3,00 de 01/01 a 30/06 (1.472 linhas).
-- Os dois preços convivem no mesmo período, então NÃO é um reajuste no tempo. Causa desconhecida
-- (não dá para saber pela base se é promoção, variação do item ou erro de cadastro).
SELECT unit_price,
       MIN(transaction_date) AS primeira_data,
       MAX(transaction_date) AS ultima_data,
       COUNT(*)              AS linhas
FROM transacoes
WHERE product_detail = 'Ouro Brasileiro shot'
GROUP BY unit_price;

-- =====================================================================================
-- PARTE B. De onde vem o crescimento? (a rodar)
-- Identidade usada: receita por linha = unidades por linha x preço médio por unidade.
-- =====================================================================================

-- B1. Mês a mês: faturamento, volume, itens por linha e preço médio por unidade
-- Esperado pelo que vimos na Pergunta 1: linhas e faturamento sobem junto; preço médio por unidade parado.
SELECT strftime('%Y-%m', transaction_date)                   AS mes,
       COUNT(DISTINCT transaction_date)                      AS dias,
       ROUND(SUM(total_bill), 2)                             AS faturamento,
       COUNT(*)                                              AS linhas,
       SUM(transaction_qty)                                  AS unidades,
       ROUND(SUM(total_bill) / COUNT(*), 3)                  AS receita_por_linha,
       ROUND(1.0 * SUM(transaction_qty) / COUNT(*), 3)       AS unidades_por_linha,
       ROUND(SUM(total_bill) / SUM(transaction_qty), 3)      AS preco_medio_unidade
FROM transacoes
GROUP BY mes
ORDER BY mes;

-- B2. Por loja: faturamento de janeiro e de junho e crescimento
SELECT store_location,
       ROUND(SUM(CASE WHEN month = 1 THEN total_bill ELSE 0 END), 2) AS fat_jan,
       ROUND(SUM(CASE WHEN month = 6 THEN total_bill ELSE 0 END), 2) AS fat_jun,
       ROUND(100.0 * (SUM(CASE WHEN month = 6 THEN total_bill ELSE 0 END)
                      / SUM(CASE WHEN month = 1 THEN total_bill ELSE 0 END) - 1), 1) AS cresc_pct
FROM transacoes
GROUP BY store_location
ORDER BY fat_jun DESC;

-- B3. Por categoria: quanto de cada uma entra no crescimento de janeiro para junho
WITH c AS (
    SELECT product_category,
           SUM(CASE WHEN month = 1 THEN total_bill ELSE 0 END) AS fat_jan,
           SUM(CASE WHEN month = 6 THEN total_bill ELSE 0 END) AS fat_jun
    FROM transacoes
    GROUP BY product_category),
d AS (
    SELECT product_category, fat_jan, fat_jun, fat_jun - fat_jan AS delta FROM c)
SELECT product_category,
       ROUND(fat_jan, 2) AS fat_jan,
       ROUND(fat_jun, 2) AS fat_jun,
       ROUND(delta, 2)   AS delta,
       ROUND(100.0 * delta / SUM(delta) OVER (), 1) AS pct_do_crescimento,
       ROUND(100.0 * (fat_jun / fat_jan - 1), 1)    AS cresc_pct
FROM d
ORDER BY delta DESC;

-- B4. Os 10 produtos que mais contribuem para o crescimento de janeiro para junho
WITH p AS (
    SELECT product_id, MAX(product_detail) AS produto,
           SUM(CASE WHEN month = 1 THEN total_bill ELSE 0 END) AS fat_jan,
           SUM(CASE WHEN month = 6 THEN total_bill ELSE 0 END) AS fat_jun
    FROM transacoes
    GROUP BY product_id, product_type),
d AS (
    SELECT produto, fat_jan, fat_jun, fat_jun - fat_jan AS delta FROM p)
SELECT produto,
       ROUND(fat_jan, 2) AS fat_jan,
       ROUND(fat_jun, 2) AS fat_jun,
       ROUND(delta, 2)   AS delta,
       ROUND(100.0 * delta / SUM(delta) OVER (), 1) AS pct_do_crescimento
FROM d
ORDER BY delta DESC
LIMIT 10;

-- B5. Decomposição do crescimento (janeiro -> junho) em preço, volume e mistura de produtos
-- Por produto: efeito preço = (preço médio jun - preço médio jan) x unidades jun.
--              efeito quantidade = variação total do produto - efeito preço.
-- Depois: volume puro = variação das unidades totais x preço médio geral de janeiro;
--         mistura = efeito quantidade - volume puro (mudança na composição de produtos).
-- Os três efeitos somam a variação total do faturamento. Obs.: janeiro tem 31 dias e junho 30.
WITH p AS (
    SELECT product_id,
           SUM(CASE WHEN month = 1 THEN transaction_qty ELSE 0 END) AS u0,
           SUM(CASE WHEN month = 1 THEN total_bill      ELSE 0 END) AS r0,
           SUM(CASE WHEN month = 6 THEN transaction_qty ELSE 0 END) AS u1,
           SUM(CASE WHEN month = 6 THEN total_bill      ELSE 0 END) AS r1
    FROM transacoes
    WHERE month IN (1, 6)
    GROUP BY product_id),
e AS (
    SELECT u0, r0, u1, r1,
           CASE WHEN u0 > 0 AND u1 > 0 THEN (r1 * 1.0 / u1 - r0 * 1.0 / u0) * u1 ELSE 0 END AS ef_preco
    FROM p),
t AS (
    SELECT SUM(r1) - SUM(r0)           AS delta_total,
           SUM(ef_preco)               AS efeito_preco,
           SUM(r1 - r0 - ef_preco)     AS efeito_quantidade,
           (SUM(u1) - SUM(u0)) * SUM(r0) * 1.0 / SUM(u0) AS efeito_volume
    FROM e)
SELECT ROUND(delta_total, 2)                          AS variacao_total,
       ROUND(efeito_volume, 2)                        AS volume,
       ROUND(efeito_quantidade - efeito_volume, 2)    AS mistura_de_produtos,
       ROUND(efeito_preco, 2)                         AS preco,
       ROUND(100.0 * efeito_volume / delta_total, 1)                       AS pct_volume,
       ROUND(100.0 * (efeito_quantidade - efeito_volume) / delta_total, 1) AS pct_mistura,
       ROUND(100.0 * efeito_preco / delta_total, 1)                        AS pct_preco
FROM t;
