"""Cálculos do dashboard, sem Streamlit, para poderem ser testados (tests/test_calculos.py).

Regra de ouro: o rótulo de variação mostrado em qualquer gráfico é calculado sobre o MESMO
valor que a barra ou a linha desenha: o total do período ou, quando o usuário pede,
a média por dia. Assim o sinal do rótulo sempre bate com o que o gráfico mostra.
"""
from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]  # índice 0 = segunda-feira
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
FREQ = {"Dia": "D", "Semana": "W-SUN", "Mês": "M"}  # semana de segunda a domingo


# ----------------------------------------------------------------------------- dados
def carregar_consultas(caminho) -> dict[str, str]:
    """Lê um .sql e devolve {nome: consulta}, usando os marcadores '-- name: <nome>'."""
    texto = Path(caminho).read_text(encoding="utf-8")
    blocos = re.split(r"^-- name:\s*(\w+)\s*$", texto, flags=re.M)
    return {nome: sql.strip() for nome, sql in zip(blocos[1::2], blocos[2::2])}


def carregar_base(banco, arquivo_sql) -> pd.DataFrame:
    """Carrega a base (uma linha por item vendido) a partir do SQLite."""
    sql = carregar_consultas(arquivo_sql)["base"]
    with closing(sqlite3.connect(banco)) as con:
        return pd.read_sql(sql, con, parse_dates=["data"])


# --------------------------------------------------------------------------- filtros
@dataclass(frozen=True)
class Filtros:
    inicio: pd.Timestamp
    fim: pd.Timestamp
    lojas: tuple = ()          # tupla vazia = todas
    categorias: tuple = ()
    tipos: tuple = ()
    produtos: tuple = ()
    dias_semana: tuple = ()    # índices 0 (segunda) a 6 (domingo)
    hora_min: int = 0
    hora_max: int = 23


def filtrar(df: pd.DataFrame, f: Filtros) -> pd.DataFrame:
    m = (df["data"] >= f.inicio) & (df["data"] <= f.fim) & df["hora"].between(f.hora_min, f.hora_max)
    for coluna, valores in [("loja", f.lojas), ("categoria", f.categorias), ("tipo", f.tipos),
                            ("produto", f.produtos), ("dia_semana", f.dias_semana)]:
        if valores:
            m &= df[coluna].isin(valores)
    return df[m]


def calendario(f: Filtros) -> pd.DatetimeIndex:
    """Datas do período escolhido (só dos dias da semana selecionados).

    É a base para contar dias, inclusive dias sem nenhuma venda no recorte."""
    datas = pd.date_range(f.inicio, f.fim, freq="D")
    if f.dias_semana:
        datas = datas[datas.dayofweek.isin(f.dias_semana)]
    return datas


# ------------------------------------------------------------------------ indicadores
def kpis(df: pd.DataFrame, f: Filtros) -> dict:
    dias = len(calendario(f))
    n = len(df)
    fat = float(df["faturamento"].sum())
    unid = int(df["unidades"].sum())
    return {
        "faturamento": fat,
        "transacoes": n,
        "unidades": unid,
        "dias": dias,
        "receita_por_transacao": fat / n if n else np.nan,
        "unidades_por_transacao": unid / n if n else np.nan,
        "faturamento_dia": fat / dias if dias else np.nan,
    }


def variacao(atual, anterior):
    """Variação percentual; None quando não há base de comparação."""
    if anterior is None or pd.isna(anterior) or anterior == 0 or pd.isna(atual):
        return None
    return (atual / anterior - 1) * 100


def periodo_anterior(f: Filtros, data_min) -> Filtros | None:
    """Período de mesmo tamanho imediatamente antes do escolhido; None se sair da base."""
    tamanho = (f.fim - f.inicio).days + 1
    ant_fim = f.inicio - pd.Timedelta(days=1)
    ant_inicio = ant_fim - pd.Timedelta(days=tamanho - 1)
    if ant_inicio < pd.Timestamp(data_min):
        return None
    return replace(f, inicio=ant_inicio, fim=ant_fim)


# ------------------------------------------------------------------- séries temporais
def serie_temporal(df: pd.DataFrame, f: Filtros, freq: str) -> pd.DataFrame:
    """Faturamento, transações e dias por período (freq: 'D', 'W-SUN' ou 'M').

    Períodos sem venda entram com zero. 'parcial' marca períodos que passam das
    datas escolhidas (por exemplo, um mês cortado no meio)."""
    cal = calendario(f)
    dias = pd.Series(1, index=cal.to_period(freq)).groupby(level=0).sum().rename("dias")
    if len(df):
        agrupado = df.assign(periodo=df["data"].dt.to_period(freq)).groupby("periodo").agg(
            faturamento=("faturamento", "sum"),
            transacoes=("faturamento", "size"),
            unidades=("unidades", "sum"),
        )
    else:
        agrupado = pd.DataFrame(columns=["faturamento", "transacoes", "unidades"])
    s = dias.to_frame().join(agrupado).fillna(0)
    s["transacoes"] = s["transacoes"].astype(int)
    s["inicio"] = s.index.start_time
    s["parcial"] = (s.index.start_time < f.inicio) | (s.index.end_time.normalize() > f.fim)
    s["receita_por_transacao"] = s["faturamento"] / s["transacoes"].replace(0, np.nan)
    s.index.name = "periodo"
    return s.reset_index()


def com_valor(s: pd.DataFrame, metrica: str, por_dia: bool) -> pd.Series:
    """Valor que o gráfico desenha: total do período ou média por dia."""
    if por_dia:
        return s[metrica] / s["dias"].where(s["dias"] > 0)
    return s[metrica].astype(float)


def com_variacao(s: pd.DataFrame, metrica: str, por_dia: bool = False) -> pd.DataFrame:
    """Acrescenta 'valor' (o que o gráfico mostra) e 'variacao_pct' (sobre o período anterior,
    calculada sobre esse mesmo valor)."""
    s = s.copy()
    s["valor"] = com_valor(s, metrica, por_dia)
    anterior = s["valor"].shift(1)
    s["variacao_pct"] = (s["valor"] / anterior.where(anterior > 0) - 1) * 100
    return s


def serie_por_loja(df: pd.DataFrame, f: Filtros, freq: str) -> pd.DataFrame:
    partes = []
    for loja, g in df.groupby("loja"):
        s = serie_temporal(g, f, freq)
        s["loja"] = loja
        partes.append(s)
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def participacao(sl: pd.DataFrame, metrica: str) -> pd.DataFrame:
    """Participação de cada loja no total do período (%)."""
    sl = sl.copy()
    total = sl.groupby("periodo")[metrica].transform("sum")
    sl["participacao_pct"] = sl[metrica] / total.where(total > 0) * 100
    return sl


def indice_decomposicao(df: pd.DataFrame, f: Filtros, mes_base=None) -> pd.DataFrame:
    """Índice (mês-base = 100) de faturamento por dia, transações por dia e receita por transação.

    Faturamento por dia = transações por dia × receita por transação, então o índice do
    faturamento é o produto dos outros dois (dividido por 100)."""
    s = serie_temporal(df, f, "M")
    s = s[s["dias"] > 0].reset_index(drop=True)
    s["faturamento_dia"] = s["faturamento"] / s["dias"]
    s["transacoes_dia"] = s["transacoes"] / s["dias"]
    colunas = ["faturamento_dia", "transacoes_dia", "receita_por_transacao"]
    if s.empty:
        return s
    if mes_base is None:
        com_venda = s[s["faturamento"] > 0]
        if com_venda.empty:
            return s.iloc[0:0]
        base = com_venda.iloc[0]
    else:
        linha = s[s["periodo"] == mes_base]
        if linha.empty:
            return s.iloc[0:0]
        base = linha.iloc[0]
    for c in colunas:
        denominador = base[c] if base[c] and not pd.isna(base[c]) else np.nan
        s[c + "_idx"] = s[c] / denominador * 100
    return s


# ------------------------------------------------------------------------ formatação
def _milhar(x, casas=0) -> str:
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int(x) -> str:
    return "—" if x is None or pd.isna(x) else _milhar(x, 0)


def fmt_money(x, casas=0) -> str:
    return "—" if x is None or pd.isna(x) else "$" + _milhar(x, casas)


def fmt_num(x, casas=2) -> str:
    return "—" if x is None or pd.isna(x) else _milhar(x, casas)


def fmt_pct(x, sinal=True, casas=1) -> str:
    if x is None or pd.isna(x):
        return "—"
    return (f"{x:+.{casas}f}%" if sinal else f"{x:.{casas}f}%").replace(".", ",")


def rotulo_periodo(periodo: pd.Period, freq: str) -> str:
    if freq == "M":
        return f"{MESES[periodo.month - 1]}/{str(periodo.year)[2:]}"
    if freq == "D":
        return periodo.start_time.strftime("%d/%m/%y")
    return "sem. " + periodo.start_time.strftime("%d/%m")
