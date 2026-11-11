"""Dashboard interativo da rede de cafeterias (Streamlit).

Rodar na raiz do repositório:  streamlit run app/dashboard.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))

import calculos as c  # noqa: E402
import graficos as g  # noqa: E402

BANCO = RAIZ / "dados" / "cafeterias.db"
SQL_DASHBOARD = RAIZ / "sql" / "dashboard.sql"
METRICAS = {"Faturamento": "faturamento", "Transações": "transacoes"}

st.set_page_config(page_title="Rede de cafeterias | Dashboard", page_icon="☕", layout="wide")


# ----------------------------------------------------------------------------- dados
@st.cache_data(show_spinner="Carregando a base...")
def carregar_base() -> pd.DataFrame:
    if not BANCO.exists():
        # primeira execução (por exemplo, repositório recém-clonado): cria o banco a partir do CSV
        sys.path.insert(0, str(RAIZ / "scripts"))
        import importar_para_sqlite
        importar_para_sqlite.main()
    return c.carregar_base(BANCO, SQL_DASHBOARD)


def mostrar_grafico(fig) -> None:
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:  # versões mais antigas do Streamlit
        st.plotly_chart(fig, use_container_width=True)


try:
    base = carregar_base()
except FileNotFoundError:
    st.error("Não encontrei `dados/transacoes_cafeterias.csv` nem `dados/cafeterias.db`. "
             "Coloque o CSV na pasta `dados/` e recarregue a página.")
    st.stop()

DMIN, DMAX = base["data"].min().date(), base["data"].max().date()
HMIN, HMAX = int(base["hora"].min()), int(base["hora"].max())


# --------------------------------------------------------------------------- filtros
def limpar_filtros() -> None:
    st.session_state.update(periodo=(DMIN, DMAX), lojas=[], categorias=[], tipos=[], produtos=[],
                            dias=[], horas=(HMIN, HMAX))


if "periodo" not in st.session_state:
    limpar_filtros()

st.sidebar.header("Filtros")
st.sidebar.button("Limpar filtros", on_click=limpar_filtros)
st.sidebar.caption("Em listas, deixar vazio significa todos.")

periodo = st.sidebar.date_input("Período", min_value=DMIN, max_value=DMAX, key="periodo", format="DD/MM/YYYY")
if not isinstance(periodo, tuple) or len(periodo) != 2:
    st.info("Escolha também a data final do período.")
    st.stop()

lojas = st.sidebar.multiselect("Loja", sorted(base["loja"].unique()), key="lojas", placeholder="Todas")
categorias = st.sidebar.multiselect("Categoria de produto", sorted(base["categoria"].unique()),
                                    key="categorias", placeholder="Todas")

opcoes_tipo = sorted(base[base["categoria"].isin(categorias)]["tipo"].unique() if categorias else base["tipo"].unique())
st.session_state["tipos"] = [t for t in st.session_state["tipos"] if t in opcoes_tipo]
tipos = st.sidebar.multiselect("Tipo de produto", opcoes_tipo, key="tipos", placeholder="Todos")

if tipos:
    mascara_produto = base["tipo"].isin(tipos)
elif categorias:
    mascara_produto = base["categoria"].isin(categorias)
else:
    mascara_produto = pd.Series(True, index=base.index)
opcoes_produto = sorted(base[mascara_produto]["produto"].unique())
st.session_state["produtos"] = [p for p in st.session_state["produtos"] if p in opcoes_produto]
produtos = st.sidebar.multiselect("Produto", opcoes_produto, key="produtos", placeholder="Todos")

dias_sel = st.sidebar.multiselect("Dia da semana", c.DIAS_SEMANA, key="dias", placeholder="Todos")
horas = st.sidebar.slider("Horário (hora do dia)", HMIN, HMAX, key="horas")

filtros = c.Filtros(
    inicio=pd.Timestamp(periodo[0]), fim=pd.Timestamp(periodo[1]),
    lojas=tuple(lojas), categorias=tuple(categorias), tipos=tuple(tipos), produtos=tuple(produtos),
    dias_semana=tuple(c.DIAS_SEMANA.index(d) for d in dias_sel), hora_min=horas[0], hora_max=horas[1],
)
df = c.filtrar(base, filtros)

# ---------------------------------------------------------------------------- cabeçalho
st.title("Rede de cafeterias: dashboard")
st.caption("3 lojas · janeiro a junho de 2023 · cada linha da base é um item vendido (não há id de pedido).")

if df.empty or len(c.calendario(filtros)) == 0:
    st.warning("Nenhuma venda com esses filtros. Ajuste ou limpe os filtros na barra lateral.")
    st.stop()
if len(df) < 300:
    st.warning(f"Só {len(df)} transações neste recorte. Os gráficos podem oscilar muito.")

# ------------------------------------------------------------------------------- KPIs
atual = c.kpis(df, filtros)
anterior_f = c.periodo_anterior(filtros, DMIN)
anterior = c.kpis(c.filtrar(base, anterior_f), anterior_f) if anterior_f else None


def delta(chave: str) -> str | None:
    if anterior is None:
        return None
    v = c.variacao(atual[chave], anterior[chave])
    return None if v is None else c.fmt_pct(v)


k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Faturamento", c.fmt_money(atual["faturamento"]), delta("faturamento"))
k2.metric("Transações", c.fmt_int(atual["transacoes"]), delta("transacoes"))
k3.metric("Receita por transação", c.fmt_money(atual["receita_por_transacao"], 2), delta("receita_por_transacao"),
          help="Média por linha da base (item vendido), não o ticket por cliente.")
k4.metric("Unidades por transação", c.fmt_num(atual["unidades_por_transacao"], 2), delta("unidades_por_transacao"))
k5.metric("Faturamento por dia", c.fmt_money(atual["faturamento_dia"]), delta("faturamento_dia"),
          help=f"Faturamento dividido por {atual['dias']} dias do período.")

if anterior_f is None:
    st.caption("Sem comparação: o período anterior de mesmo tamanho começaria antes do início da base.")
else:
    legenda = (f"Variações em relação ao período anterior de mesmo tamanho "
               f"({anterior_f.inicio:%d/%m} a {anterior_f.fim:%d/%m}).")
    if anterior["dias"] != atual["dias"]:
        legenda += " Os dois períodos têm número de dias diferente por causa do filtro de dia da semana."
    st.caption(legenda)

st.divider()

# ------------------------------------------------------------------- gráficos 2 e 3
col2, col3 = st.columns(2)

with col2:
    st.subheader("Evolução no tempo")
    a, b = st.columns(2)
    gran2 = a.radio("Agrupar por", list(c.FREQ), index=2, horizontal=True, key="gran2")
    metrica2 = b.radio("Métrica", ["Faturamento", "Transações"], horizontal=True, key="met2")
    freq2 = c.FREQ[gran2]
    if freq2 == "D":
        media_movel = st.checkbox("Média móvel de 7 dias", value=True, key="mm2")
        por_dia2 = False
    else:
        por_dia2 = st.checkbox("Média por dia", key="pd2",
                               help="Divide cada período pelo número de dias dele. Use para comparar meses de tamanhos diferentes.")
        media_movel = False
    serie2 = c.serie_temporal(df, filtros, freq2)
    mostrar_grafico(g.fig_tendencia(serie2, freq2, METRICAS[metrica2],
                                    por_dia2, media_movel))
    if freq2 != "D" and not por_dia2:
        st.caption("Os períodos têm tamanhos diferentes (fevereiro tem 28 dias, por exemplo), e os parciais aparecem em tom claro. "
                   "Marque **Média por dia** para compará-los em igualdade. O percentual sempre compara o valor que a barra mostra.")
    elif por_dia2:
        st.caption("Cada barra é o valor do período dividido pelo número de dias dele.")

with col3:
    st.subheader("Comparação entre lojas")
    a, b, d = st.columns(3)
    gran3 = a.radio("Agrupar por", list(c.FREQ), index=2, horizontal=True, key="gran3")
    metrica3 = b.radio("Métrica", ["Faturamento", "Transações"], horizontal=True, key="met3")
    modo3 = d.radio("Mostrar", ["Valores", "Participação (%)"], horizontal=True, key="modo3")
    freq3 = c.FREQ[gran3]
    por_dia3 = False
    if freq3 != "D" and modo3 == "Valores":
        por_dia3 = st.checkbox("Média por dia", key="pd3")
    serie3 = c.serie_por_loja(df, filtros, freq3)
    mostrar_grafico(g.fig_lojas(serie3, freq3, METRICAS[metrica3], modo3, por_dia3))

# ----------------------------------------------------------------------------- gráfico 5
st.divider()
st.subheader("De onde vem o crescimento?")
indice_bruto = c.indice_decomposicao(df, filtros)
if len(indice_bruto) < 2:
    st.info("Escolha um período com pelo menos dois meses para ver a decomposição.")
else:
    meses = list(indice_bruto["periodo"])
    rotulos = {c.rotulo_periodo(m, "M"): m for m in meses}
    escolhido = st.selectbox("Mês-base do índice (= 100)", list(rotulos), index=0, key="base5")
    idx = c.indice_decomposicao(df, filtros, mes_base=rotulos[escolhido])
    mostrar_grafico(g.fig_indice(idx, escolhido))
    ultimo = idx.iloc[-1]
    st.caption(
        f"Em {c.rotulo_periodo(ultimo['periodo'], 'M')}, com {escolhido} = 100: faturamento por dia em "
        f"{c.fmt_num(ultimo['faturamento_dia_idx'], 1)}, transações por dia em {c.fmt_num(ultimo['transacoes_dia_idx'], 1)} "
        f"e receita por transação em {c.fmt_num(ultimo['receita_por_transacao_idx'], 1)}. "
        "Faturamento por dia = transações por dia × receita por transação. Se o faturamento acompanha as transações "
        "e a receita por transação fica perto de 100, o crescimento vem de volume, e não de preço ou de itens maiores."
    )

# ------------------------------------------------------------------------ tabela e notas
with st.expander("Ver a tabela mensal do recorte (e baixar)"):
    mensal = c.serie_temporal(df, filtros, "M")
    tot = c.com_variacao(mensal, "faturamento", False)
    dia = c.com_variacao(mensal, "faturamento", True)
    tabela = pd.DataFrame({
        "Mês": [c.rotulo_periodo(p, "M") + (" (parcial)" if parcial else "") for p, parcial in zip(mensal["periodo"], mensal["parcial"])],
        "Dias": mensal["dias"], "Faturamento": mensal["faturamento"].round(2),
        "Variação do total (%)": tot["variacao_pct"].round(1),
        "Faturamento por dia": dia["valor"].round(2), "Variação por dia (%)": dia["variacao_pct"].round(1),
        "Transações": mensal["transacoes"], "Receita por transação": mensal["receita_por_transacao"].round(2),
    })
    st.dataframe(tabela, hide_index=True)
    st.download_button("Baixar CSV", tabela.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name="tabela_mensal_recorte.csv", mime="text/csv")

with st.expander("Notas sobre os dados"):
    st.markdown(
        "- Cada linha da base é um **item vendido**, sem id de pedido. Por isso *receita por transação* é a média por linha, "
        "não o ticket por cliente. Ao filtrar um produto, ela vira o preço médio pago por esse produto.\n"
        "- A moeda não é informada na fonte; os valores aparecem com `$`.\n"
        "- Em 15 produtos o preço unitário varia ao longo do período (investigação na Pergunta 2); recortes por produto "
        "podem ser afetados.\n"
        "- São só seis meses e não há ano anterior: parte do crescimento pode ser sazonalidade.\n"
        "- Fonte: Coffee Sales Analysis Dataset (Kaggle)."
    )
