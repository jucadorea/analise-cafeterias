"""Conferência dos cálculos do dashboard contra consultas SQL diretas no banco.

Rodar na raiz do repositório:  pytest tests -q
(precisa do dados/cafeterias.db; rode scripts/importar_para_sqlite.py antes)
"""
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))
import calculos as c  # noqa: E402

BANCO = RAIZ / "dados" / "cafeterias.db"
pytestmark = pytest.mark.skipif(not BANCO.exists(), reason="dados/cafeterias.db não encontrado")


@pytest.fixture(scope="module")
def con():
    conexao = sqlite3.connect(BANCO)
    yield conexao
    conexao.close()


@pytest.fixture(scope="module")
def base():
    return c.carregar_base(BANCO, RAIZ / "sql" / "dashboard.sql")


@pytest.fixture(scope="module")
def tudo(base):
    return c.Filtros(base["data"].min(), base["data"].max())


def sql(con, consulta, params=()):
    return pd.read_sql(consulta, con, params=params)


def test_kpis_batem_com_sql(con, base, tudo):
    k = c.kpis(c.filtrar(base, tudo), tudo)
    ref = sql(con, "SELECT SUM(total_bill) f, COUNT(*) n, SUM(transaction_qty) u, "
                   "COUNT(DISTINCT transaction_date) d FROM transacoes").iloc[0]
    assert k["faturamento"] == pytest.approx(ref["f"])
    assert k["transacoes"] == ref["n"] == 149116
    assert k["unidades"] == ref["u"]
    assert k["dias"] == ref["d"] == 181
    assert k["receita_por_transacao"] == pytest.approx(ref["f"] / ref["n"])


def test_serie_mensal_bate_com_sql(con, base, tudo):
    s = c.serie_temporal(c.filtrar(base, tudo), tudo, "M")
    ref = sql(con, "SELECT strftime('%Y-%m', transaction_date) mes, COUNT(DISTINCT transaction_date) dias, "
                   "SUM(total_bill) fat, COUNT(*) n FROM transacoes GROUP BY mes ORDER BY mes")
    assert list(s["periodo"].astype(str)) == list(ref["mes"])
    assert list(s["dias"]) == list(ref["dias"])
    assert s["faturamento"].to_numpy() == pytest.approx(ref["fat"].to_numpy())
    assert list(s["transacoes"]) == list(ref["n"])


def test_sinal_da_variacao_bate_com_o_valor_desenhado(base, tudo):
    """O erro que motivou os testes: rótulo de variação com sinal diferente da barra."""
    s = c.serie_temporal(c.filtrar(base, tudo), tudo, "M")
    for metrica in ["faturamento", "transacoes"]:
        for por_dia in [False, True]:
            v = c.com_variacao(s, metrica, por_dia)
            diferenca = v["valor"].diff().iloc[1:]
            variacao = v["variacao_pct"].iloc[1:]
            assert (np.sign(diferenca) == np.sign(variacao)).all(), (metrica, por_dia)


def test_fevereiro_cai_no_total_e_sobe_por_dia(base, tudo):
    s = c.serie_temporal(c.filtrar(base, tudo), tudo, "M")
    total = c.com_variacao(s, "faturamento", False)
    por_dia = c.com_variacao(s, "faturamento", True)
    assert total["variacao_pct"].iloc[1] == pytest.approx((76145.19 / 81677.74 - 1) * 100, abs=0.01)
    assert total["variacao_pct"].iloc[1] < 0
    assert por_dia["variacao_pct"].iloc[1] == pytest.approx(3.21, abs=0.01)


def test_lojas_somam_o_total_e_participacao_fecha_100(base, tudo):
    df = c.filtrar(base, tudo)
    total = c.serie_temporal(df, tudo, "M")
    sl = c.serie_por_loja(df, tudo, "M")
    soma = sl.groupby("periodo")["faturamento"].sum()
    assert soma.to_numpy() == pytest.approx(total["faturamento"].to_numpy())
    part = c.participacao(sl, "faturamento").groupby("periodo")["participacao_pct"].sum()
    assert part.to_numpy() == pytest.approx(100.0)


def test_indice_tem_base_100_e_faturamento_e_produto_dos_outros(base, tudo):
    idx = c.indice_decomposicao(c.filtrar(base, tudo), tudo)
    for col in ["faturamento_dia_idx", "transacoes_dia_idx", "receita_por_transacao_idx"]:
        assert idx[col].iloc[0] == pytest.approx(100.0)
    produto = idx["transacoes_dia_idx"] * idx["receita_por_transacao_idx"] / 100
    assert idx["faturamento_dia_idx"].to_numpy() == pytest.approx(produto.to_numpy())
    # outro mês-base também vira 100
    idx2 = c.indice_decomposicao(c.filtrar(base, tudo), tudo, mes_base=pd.Period("2023-03", "M"))
    assert idx2.loc[idx2["periodo"] == pd.Period("2023-03", "M"), "faturamento_dia_idx"].iloc[0] == pytest.approx(100.0)


def test_filtros_batem_com_sql(con, base, tudo):
    f = c.Filtros(pd.Timestamp("2023-02-10"), pd.Timestamp("2023-05-20"), lojas=("Astoria",),
                  categorias=("Coffee",), dias_semana=(0, 4), hora_min=7, hora_max=10)
    df = c.filtrar(base, f)
    ref = sql(con, "SELECT SUM(total_bill) f, COUNT(*) n FROM transacoes WHERE transaction_date BETWEEN ? AND ? "
                   "AND store_location = ? AND product_category = ? AND day_of_week IN (0, 4) AND hour BETWEEN 7 AND 10",
              ("2023-02-10", "2023-05-20", "Astoria", "Coffee")).iloc[0]
    assert df["faturamento"].sum() == pytest.approx(ref["f"])
    assert len(df) == ref["n"]


def test_calendario_conta_so_os_dias_da_semana_escolhidos():
    f = c.Filtros(pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-31"), dias_semana=(0,))  # segundas
    assert len(c.calendario(f)) == 5  # segundas: 2, 9, 16, 23 e 30 de janeiro


def test_mes_cortado_e_marcado_como_parcial(base):
    f = c.Filtros(pd.Timestamp("2023-02-15"), pd.Timestamp("2023-04-10"))
    s = c.serie_temporal(c.filtrar(base, f), f, "M")
    assert list(s["parcial"]) == [True, False, True]
    assert list(s["dias"]) == [14, 31, 10]


def test_dia_sem_venda_entra_com_zero_e_nao_gera_variacao_infinita(base):
    f = c.Filtros(pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-10"), produtos=("Ethiopia",), hora_min=20, hora_max=20)
    df = c.filtrar(base, f)
    s = c.serie_temporal(df, f, "D")
    assert len(s) == 10
    v = c.com_variacao(s, "faturamento")
    assert not np.isinf(v["variacao_pct"].dropna()).any()


def test_periodo_anterior(base, tudo):
    f = c.Filtros(pd.Timestamp("2023-03-01"), pd.Timestamp("2023-03-31"))
    ant = c.periodo_anterior(f, base["data"].min())
    assert (ant.inicio, ant.fim) == (pd.Timestamp("2023-01-29"), pd.Timestamp("2023-02-28"))
    assert c.periodo_anterior(tudo, base["data"].min()) is None


def test_variacao_sem_base_devolve_none():
    assert c.variacao(10, 0) is None and c.variacao(10, None) is None
    assert c.variacao(110, 100) == pytest.approx(10.0)
