# Análise de uma rede de cafeterias

[![Abrir no Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://djq3qxvkahlnwkqvhaals3.streamlit.app/)

**Dashboard online:** https://djq3qxvkahlnwkqvhaals3.streamlit.app/

Análise de cerca de 149 mil transações de 3 lojas de uma rede de cafeterias (janeiro a junho de 2023), com SQL, Python (pandas) e dashboards, para responder se a rede vai bem e por quê.


## Perguntas de negócio

1. **Saúde da rede:** como está a rede de cafeterias no geral? Está indo bem ou mal?
2. **Causas:** existe algum motivo para a rede estar indo bem ou mal? O que explica o resultado: volume de pedidos, preço, lojas ou produtos?
3. **Tendência:** qual é a tendência do faturamento diário e existe algum padrão semanal?

## Dados

Fonte: [Coffee Shop Sales (Maven Analytics)](https://mavenanalytics.io/data-playground/coffee-shop-sales), licença Public Domain. Os dados são de uma rede fictícia, a Maven Roasters, com três lojas em Nova York, e foram criados para prática de análise.

- **Arquivo:** `dados/transacoes_cafeterias.csv` (149.116 linhas e 18 colunas, de 01/01/2023 a 30/06/2023).
- **Lojas:** Astoria, Hell's Kitchen e Lower Manhattan.
- **Unidade da linha:** cada linha é um item vendido, sem id de pedido. Por isso "receita por transação" é a média por linha, e não o ticket por cliente. A moeda não é informada na fonte; os valores aparecem com `$`.
- **Qualidade:** a base não tem ids duplicados nem valores nulos, e o total da conta é coerente com quantidade × preço unitário. Em 15 produtos o preço unitário varia ao longo da base (1.262 linhas, 0,74% do faturamento; veja a Pergunta 2).

### Dicionário de dados

| Coluna | Descrição |
|---|---|
| `transaction_id` | identificador da linha (um item vendido) |
| `transaction_date` | data da venda (AAAA-MM-DD) |
| `transaction_time` | hora da venda (HH:MM:SS) |
| `store_id` | código da loja |
| `store_location` | nome da loja |
| `product_id` | código do produto |
| `transaction_qty` | unidades vendidas na linha |
| `unit_price` | preço unitário |
| `total_bill` | valor da linha (quantidade × preço unitário) |
| `product_category` | categoria do produto (por exemplo, Coffee, Tea, Bakery) |
| `product_type` | tipo de produto dentro da categoria |
| `product_detail` | nome do produto |
| `size` | tamanho do item (`Not Defined` nos itens sem tamanho) |
| `month_name` | nome do mês |
| `day_name` | nome do dia da semana |
| `hour` | hora cheia da venda |
| `month` | número do mês |
| `day_of_week` | dia da semana (0 = segunda-feira) |

## Estrutura do repositório

```
analise-cafeterias/
├── dados/        # base de transações em CSV (o banco SQLite é gerado a partir dele)
├── sql/          # consultas: checagem de qualidade, Pergunta 1, Pergunta 2 e camada de dados do dashboard
├── scripts/      # importação do CSV para SQLite
├── notebooks/    # análises em Python (pandas)
├── app/          # dashboard interativo (Streamlit)
├── tests/        # conferência dos cálculos contra consultas SQL
├── figuras/      # gráficos exportados pelos notebooks
├── .streamlit/   # tema do dashboard
├── requirements.txt       # dependências do dashboard
├── requirements-dev.txt   # dependências para notebooks e testes
└── README.md
```

## Ferramentas

SQL (SQLite), Python (pandas, matplotlib, Plotly, Streamlit, Jupyter) e Power BI.

## Como reproduzir

```bash
git clone https://github.com/jucadorea/analise-cafeterias.git
cd analise-cafeterias
pip install -r requirements-dev.txt

python scripts/importar_para_sqlite.py     # cria dados/cafeterias.db (149.116 linhas)
```

- **Consultas SQL:** abra `dados/cafeterias.db` no [DB Browser for SQLite](https://sqlitebrowser.org/), carregue um arquivo de `sql/` (por exemplo, `00_checagem_qualidade.sql` ou `pergunta_2.sql`), selecione a consulta e aperte Ctrl+Enter.
- **Notebook da Pergunta 1:** abra `notebooks/pergunta_1.ipynb` e execute todas as células.
- **Dashboard interativo:** `streamlit run app/dashboard.py` (se o banco não existir, o app o cria a partir do CSV).
- **Conferência dos cálculos:** `pytest tests -q`.

## Dashboard interativo

O dashboard está publicado em https://djq3qxvkahlnwkqvhaals3.streamlit.app/. Se o app estiver hibernado (acontece depois de 12 horas sem visitas), basta abrir o link e aguardar alguns segundos.

Ele reúne os KPIs e os gráficos da Pergunta 1 com filtros na barra lateral:

- **Filtros:** período, loja, categoria, tipo e produto (em cascata), dia da semana e faixa de horário.
- **KPIs:** faturamento, transações, receita por transação, unidades por transação e faturamento por dia, com a variação sobre o período anterior de mesmo tamanho.
- **Evolução no tempo:** por dia, semana ou mês, em faturamento ou transações, com média móvel de 7 dias (dia) ou média por dia (semana e mês).
- **Comparação entre lojas:** em valores ou em participação (%).
- **Decomposição do crescimento:** índice com mês-base à escolha.

Os percentuais mostrados sempre comparam o mesmo valor que o gráfico desenha, e `tests/test_calculos.py` confere os totais, os sinais das variações e os filtros contra consultas SQL diretas.

## Principais achados

### Pergunta 1: a rede vai bem

A rede cresce com força, de forma equilibrada entre as lojas e puxada por volume de vendas.

![Visão geral](figuras/p1_g1_kpis.png)

- **Tendência:** o faturamento mensal foi de $81.678 em janeiro para $166.486 em junho, e o faturamento médio por dia foi multiplicado por 2,1. Fevereiro caiu 6,8% no total, mas tem só 28 dias; por dia, subiu 3,2%. O ritmo desacelerou em junho (+6,2% sobre maio, contra +31,8% de abril para maio).
- **Equilíbrio:** as três lojas ficam entre 32,9% e 33,8% do faturamento e crescem juntas.
- **Origem:** as transações por dia foram multiplicadas por 2,1 e a receita por transação ficou praticamente parada (índice 99,8). O crescimento vem de mais vendas, e não de preço maior.

![Faturamento mensal](figuras/p1_g2_faturamento_mensal.png)
![Faturamento por loja](figuras/p1_g3_faturamento_por_loja.png)
![Decomposição do crescimento](figuras/p1_g5_decomposicao_indice.png)

**Cuidados:** são só seis meses e não há ano anterior, então parte da alta pode ser sazonalidade; sem meta, "bem" significa crescimento em relação a janeiro.

#### Conclusão da Pergunta 1

**Sim, a rede vai bem.** O faturamento mensal praticamente dobrou de janeiro ($81.678) a junho ($166.486), e o faturamento médio por dia foi multiplicado por 2,1. O crescimento é equilibrado (cada loja fica entre 32,9% e 33,8% do total) e vem de mais vendas, não de preço maior: as transações por dia também foram multiplicadas por 2,1, enquanto a receita por transação ficou estável (índice 99,8).

Dois alertas: o ritmo desacelerou em junho (+6,2% sobre maio, contra +31,8% de abril para maio), e seis meses sem ano anterior não permitem separar crescimento real de sazonalidade.

### Pergunta 2: o que explica o crescimento

**Resposta curta:** o volume de vendas. Não é preço, não é uma loja nem um produto específico: todas as lojas e quase todas as categorias dobraram, e nenhum produto sozinho responde por mais de 3,1% do crescimento. As consultas estão em `sql/pergunta_2.sql`.

#### Volume, preço ou mistura de produtos?

Mês a mês, o preço médio por unidade e o tamanho da compra ficaram parados enquanto as transações dobraram:

| Mês | Dias | Faturamento | Transações | Receita por transação | Unidades por transação | Preço médio por unidade |
|---|---|---|---|---|---|---|
| jan/23 | 31 | $81.678 | 17.314 | $4,72 | 1,44 | $3,28 |
| fev/23 | 28 | $76.145 | 16.359 | $4,65 | 1,44 | $3,23 |
| mar/23 | 31 | $98.835 | 21.229 | $4,66 | 1,43 | $3,25 |
| abr/23 | 30 | $118.941 | 25.335 | $4,69 | 1,44 | $3,26 |
| mai/23 | 31 | $156.728 | 33.527 | $4,67 | 1,44 | $3,25 |
| jun/23 | 30 | $166.486 | 35.352 | $4,71 | 1,44 | $3,27 |

Decompondo a variação do faturamento entre janeiro e junho (+$84.808), por produto:

| Efeito | Valor | Parte da variação |
|---|---|---|
| Volume (mais itens vendidos) | +$85.625 | 101,0% |
| Mistura de produtos | −$740 | −0,9% |
| Preço | −$77 | −0,1% |
| **Variação total** | **+$84.808** | **100%** |

O volume explica todo o crescimento; mistura de produtos e preço são desprezíveis.

#### Lojas

O crescimento é parecido nas três lojas:

| Loja | Janeiro | Junho | Crescimento |
|---|---|---|---|
| Hell's Kitchen | $27.821 | $56.957 | +104,7% |
| Astoria | $27.314 | $55.083 | +101,7% |
| Lower Manhattan | $26.543 | $54.446 | +105,1% |

#### Categorias

Todas as categorias cresceram. Café e chá (Coffee e Tea) respondem por 67,4% do crescimento, proporção parecida com a que tinham no faturamento de janeiro (66%), então o cardápio vendido não mudou de perfil. As categorias de produtos que não são bebidas (grãos de café, itens da marca e chocolate embalado) cresceram menos que a média, entre +80,6% e +90,1%, e somam 7,9% do crescimento.

| Categoria | Janeiro | Junho | Crescimento | Parte do crescimento |
|---|---|---|---|---|
| Coffee | $31.257 | $64.789 | +107,3% | 39,5% |
| Tea | $22.622 | $46.243 | +104,4% | 27,9% |
| Bakery | $9.536 | $19.251 | +101,9% | 11,5% |
| Drinking Chocolate | $8.338 | $17.106 | +105,2% | 10,3% |
| Coffee beans | $5.245 | $9.913 | +89,0% | 5,5% |
| Branded | $1.890 | $3.413 | +80,6% | 1,8% |
| Loose Tea | $1.294 | $2.771 | +114,1% | 1,7% |
| Flavours | $974 | $2.008 | +106,1% | 1,2% |
| Packaged Chocolate | $522 | $992 | +90,1% | 0,6% |

#### Produtos

O crescimento é espalhado: o maior contribuinte individual (um item do cardápio, por tamanho) responde por 3,1% do aumento, e os 10 maiores somam 26,6%. Entre eles aparecem cafés (Latte, Cappuccino, Ethiopia, Jamaican Coffee River), chás (Morning Sunrise Chai), chocolate (Dark chocolate) e o Sustainably Grown Organic.

#### Preços inconsistentes na base

Em 15 produtos o preço unitário não é único (1.262 linhas, 0,85% das linhas e 0,74% do faturamento). Os padrões encontrados:

- **Doces e scones:** um segundo preço cerca de 25% mais alto em poucas linhas, quase todas em Lower Manhattan (por exemplo, Scottish Cream Scone a $5,63 em 15 linhas, contra $4,50 nas demais).
- **Ouro Brasileiro shot:** $2,10 e $3,00 convivem no mesmo período (15/01 a 30/06), o que descarta reajuste e indica inconsistência de cadastro. É o item que mais pesa nas linhas atípicas (750 de 1.262).
- **Cadastro misturado:** Latte cup, camiseta e Organic Decaf Blend aparecem com preços de outros itens da loja em poucas linhas.

Esses casos não alteram a conclusão: o efeito de preço medido na decomposição é de −0,1%.

#### Conclusão da Pergunta 2

O crescimento da rede vem do aumento do volume de vendas, espalhado por todas as lojas e quase todas as categorias, e não de reajuste de preço, mudança de cardápio ou de um produto específico. Isso aponta para algo que afeta a rede inteira (mais movimento nas lojas, campanha, sazonalidade), mas a base não traz clientes, campanhas nem um ano anterior, então ela não permite dizer qual foi a causa.

**Limites:** sem id de pedido, não dá para separar "mais clientes" de "mais itens por cliente" (embora as unidades por transação tenham ficado estáveis); janeiro tem 31 dias e junho 30, o que subestima levemente o efeito volume; seis meses não excluem sazonalidade.

### Pergunta 3: tendência do faturamento diário

**Resposta curta:** a tendência é de alta contínua, em três fases, com perda de ritmo em junho. As consultas estão em `sql/pergunta_3.sql`.

A média móvel de 30 dias do faturamento diário passou de $2.657 (05/02) para $5.445 (25/06), cerca de +105%, sem queda em nenhuma semana. O ritmo mudou ao longo do período:

- **Fevereiro:** estável, em torno de $2.650 por dia.
- **Março a maio:** aceleração. O ganho semanal da média foi de cerca de $130 em março, $158 em abril e $257 em maio.
- **Junho:** o ganho semanal caiu para cerca de $113, menos da metade do de maio. A média de 7 dias teve pico de $5.902 em 18/06 e ficou em $5.824 em 25/06 (−1,3%).

**Limites:** a média de 30 dias reage com atraso de cerca de 15 dias, então a desaceleração de junho é um sinal, não uma virada confirmada; sem ano anterior, não dá para separar tendência de sazonalidade.

**Padrão semanal:** praticamente não há. Dividindo o faturamento de cada dia pela média dos 7 dias ao redor dele (índice 100 = dia típico, o que remove o efeito da tendência de alta), os dias da semana ficam entre 98,7 (terça) e 102,0 (segunda), uma diferença de 3,3 pontos. Sábado (99,9) e domingo (98,9) vendem como os dias úteis. A segunda é o dia mais forte, mas com 25 observações de cada dia a diferença é pequena demais para ser tratada como padrão.

#### Conclusão da Pergunta 3

O faturamento diário tem tendência de alta contínua, em três fases (estável em fevereiro, aceleração de março a maio, perda de ritmo em junho), e não tem ciclo semanal relevante. Para quem planeja a operação, isso significa que o que muda a demanda é o mês, e não o dia da semana.

## Conclusões e recomendações

### O que a análise mostra

1. **A rede vai bem e cresce de forma saudável.** O faturamento mensal passou de $81.678 (janeiro) para $166.486 (junho), e a média móvel de 30 dias do faturamento diário subiu cerca de 105% entre fevereiro e junho, sem queda em nenhuma semana.
2. **O crescimento vem de volume.** Na decomposição entre janeiro e junho, o volume explica 101% da variação; preço (−0,1%) e mistura de produtos (−0,9%) são desprezíveis.
3. **O crescimento é amplo.** As três lojas crescem entre +101,7% e +105,1%, todas as categorias cresceram e nenhum produto sozinho passa de 3,1% do aumento.
4. **O ritmo mudou em junho.** O ganho semanal da média de 30 dias foi de cerca de $257 em maio e de $113 em junho.
5. **Não há padrão semanal relevante.** O índice por dia da semana fica entre 98,7 e 102,0, e fim de semana vende como dia útil.

### Recomendações

1. **Descobrir o que causou o aumento de volume.** A base mostra *que* o volume cresceu, não *por quê*. Cruzar o calendário de campanhas, aberturas de horário, promoções e fluxo de pessoas no entorno das lojas com a curva da Pergunta 3 é o passo que falta. Enquanto a causa não for conhecida, não dá para saber se o ritmo se mantém.
2. **Acompanhar julho e agosto antes de projetar a demanda.** A desaceleração de junho é um sinal, não uma virada confirmada, e sem ano anterior não dá para separar tendência de sazonalidade. Com os dois meses seguintes (e, idealmente, os mesmos meses de 2022), a conclusão fica firme.
3. **Planejar escala e estoque pelo mês, não pelo dia da semana.** A demanda diária quase não muda entre segunda e domingo, então escalas diferentes para fim de semana não têm respaldo nestes dados. A análise por horário do dia ainda não foi feita e pode mostrar picos relevantes.
4. **Olhar para as categorias que cresceram menos.** Café em grão (+89,0%), Branded (+80,6%) e chocolate embalado (+90,1%) ficaram abaixo da média. Vale verificar se há ruptura de estoque, exposição ruim ou falta de divulgação antes de concluir que a demanda é menor.
5. **Padronizar o cadastro de preços.** 15 produtos têm mais de um preço (1.262 linhas, 0,74% do faturamento). Não muda as conclusões, mas dificulta qualquer análise futura de preço. O caso do Ouro Brasileiro shot ($2,10 e $3,00 no mesmo período) deve ser conferido primeiro.
6. **Registrar o id do pedido.** Sem ele, não se separa "mais clientes" de "mais itens por cliente", que é a pergunta mais útil para campanhas e fidelização.

### Limites desta análise

Seis meses de dados, sem ano anterior, sem meta, sem clientes e sem campanhas. As conclusões descrevem o que aconteceu, e as causas ficam como hipóteses a testar com dados adicionais.

## Roteiro do projeto

- [x] Importar a base em SQLite e checar a qualidade dos dados
- [x] Pergunta 1: saúde da rede (SQL e pandas)
- [x] Dashboard interativo (Streamlit) publicado
- [x] Pergunta 2: causas (volume, preço, lojas, produtos)
- [X] Pergunta 3: série temporal com média móvel de 30 dias
- [X] Conclusões e recomendações

## Autor

Juca Dorea de Castro Chaves · [LinkedIn](https://www.linkedin.com/in/juca-dorea/) · [GitHub](https://github.com/jucadorea)
