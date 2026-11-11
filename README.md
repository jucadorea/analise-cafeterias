# Análise de uma rede de cafeterias

Análise de cerca de 149 mil transações de 3 lojas de uma rede de cafeterias (janeiro a junho de 2023), com SQL, Python (pandas) e um dashboard em Power BI, para responder se a rede vai bem e por quê.

> **Status:** em andamento. Estrutura criada; importação dos dados, análises e dashboard em construção.

## Perguntas de negócio

1. **Saúde da rede:** como está a rede de cafeterias no geral? Está indo bem ou mal?
2. **Causas:** existe algum motivo para a rede estar indo bem ou mal? O que explica o resultado: volume de pedidos, preço, lojas ou produtos?
3. **Tendência:** qual é a tendência do faturamento diário e existe algum padrão semanal?

## Dados
Coffee Sales Analysis Dataset https://www.kaggle.com/datasets/ankitrajmishra/coffee-sales-analysis-dataset/data
- **Arquivo:** `dados/transacoes_cafeterias.csv` (149.116 linhas e 18 colunas, de 01/01/2023 a 30/06/2023).
- **Lojas:** Astoria, Hell's Kitchen e Lower Manhattan.
- **Colunas principais:** `transaction_id`, `transaction_date`, `transaction_time`, `store_location`, `product_category`, `product_type`, `product_detail`, `transaction_qty`, `unit_price`, `Total_Bill`.
- **Origem:** dataset público de transações de cafeteria usado em cursos de análise de dados. *(Preencher: fonte, link e licença antes de publicar.)*
- **Dicionário de dados:** a escrever (semana 1).
- **Qualidade:** a base não tem ids duplicados nem valores nulos, e o total da conta é coerente com quantidade × preço unitário. Em 15 produtos o preço unitário varia no mesmo tamanho (por exemplo, biscoitos a 4,06 em vez de 3,25 em 21 linhas).

## Estrutura do repositório

```
analise-cafeterias/
├── dados/        # base de transações em CSV
├── sql/          # consultas SQL por pergunta
├── notebooks/    # análises em Python (pandas)
├── scripts/      # importação e utilitários
├── requirements.txt
└── README.md
```

## Ferramentas

SQL (SQLite), Python (pandas, matplotlib, Jupyter) e Power BI.

## Como reproduzir

*(A preencher conforme o projeto avançar.)*

```bash
git clone https://github.com/jucadorea/analise-cafeterias.git
cd analise-cafeterias
pip install -r requirements.txt
```

## Principais achados

*(A preencher ao concluir as perguntas 1, 2 e 3.)*

## Roteiro do projeto

- [ ] Importar a base em SQLite e checar a qualidade dos dados
- [ ] Pergunta 1: saúde da rede (SQL e pandas)
- [ ] Pergunta 2: causas (volume, preço, lojas, produtos)
- [ ] Pergunta 3: série temporal com média móvel de 30 dias
- [ ] Dashboard em Power BI
- [ ] Conclusões e recomendações

## Autor

Juca Dorea de Castro Chaves · [LinkedIn](https://www.linkedin.com/in/juca-dorea/) · [GitHub](https://github.com/jucadorea)
