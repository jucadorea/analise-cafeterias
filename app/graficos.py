"""Gráficos Plotly do dashboard. Os números vêm de calculos.py."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from calculos import (com_valor, com_variacao, fmt_int, fmt_money, fmt_num, fmt_pct,
                      participacao, rotulo_periodo)

COR = {"principal": "#6F4E37", "destaque": "#C8873A", "cinza": "#8C8C8C", "claro": "#CDB9A7",
       "Astoria": "#6F4E37", "Hell's Kitchen": "#C8873A", "Lower Manhattan": "#3E7C8C"}
PALETA_EXTRA = ["#A04668", "#5B8C5A", "#7A6FAC", "#B5543B"]
NOMES_FREQ = {"D": "dia", "W-SUN": "semana", "M": "mês"}
NOMES_METRICA = {"faturamento": "Faturamento", "transacoes": "Transações"}


def _formatador(metrica: str):
    return (lambda v: fmt_money(v, 0)) if metrica == "faturamento" else fmt_int


def _base(fig: go.Figure, titulo: str, prefixo: str = "", sufixo: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(text=titulo, x=0, font=dict(size=16)),
        separators=",.",  # vírgula decimal e ponto de milhar
        height=420, margin=dict(l=10, r=10, t=60, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.12), showlegend=False,
    )
    fig.update_yaxes(tickprefix=prefixo, ticksuffix=sufixo, tickformat=",.0f", rangemode="tozero",
                     gridcolor="rgba(128,128,128,0.25)", zeroline=False)
    fig.update_xaxes(showgrid=False)
    return fig


def _cor_loja(loja: str, i: int) -> str:
    return COR.get(loja, PALETA_EXTRA[i % len(PALETA_EXTRA)])


def fig_tendencia(serie: pd.DataFrame, freq: str, metrica: str, por_dia: bool = False,
                  media_movel: bool = False) -> go.Figure:
    """Gráfico 2: faturamento (ou transações) no tempo.

    O rótulo de variação é calculado sobre o mesmo valor que a barra desenha."""
    por_dia = por_dia and freq != "D"
    s = com_variacao(serie, metrica, por_dia)
    fmt = _formatador(metrica)
    if por_dia:
        fmt_valor = (lambda v: fmt_money(v, 0) + "/dia") if metrica == "faturamento" else (lambda v: fmt_num(v, 0) + "/dia")
    else:
        fmt_valor = fmt
    rot = [rotulo_periodo(p, freq) for p in s["periodo"]]
    hover = []
    for r, (_, l) in zip(rot, s.iterrows()):
        txt = f"<b>{r}</b><br>{NOMES_METRICA[metrica]}: {fmt_valor(l['valor'])}"
        txt += f"<br>Variação: {fmt_pct(l['variacao_pct'])}"
        if freq != "D":
            txt += f"<br>Dias no período: {int(l['dias'])}" + (" (parcial)" if l["parcial"] else "")
        hover.append(txt)

    fig = go.Figure()
    if freq == "D":
        fig.add_trace(go.Scatter(x=s["inicio"], y=s["valor"], mode="lines", hovertext=hover, hoverinfo="text",
                                 line=dict(color=COR["claro"] if media_movel else COR["principal"], width=1.6),
                                 name="Dia"))
        if media_movel:
            mm = s["valor"].rolling(7).mean()
            fig.add_trace(go.Scatter(x=s["inicio"], y=mm, mode="lines", name="Média móvel de 7 dias",
                                     line=dict(color=COR["principal"], width=3),
                                     hovertemplate="Média móvel de 7 dias: %{y:,.0f}<extra></extra>"))
            fig.update_layout(showlegend=True)
    else:
        textos = None
        if freq == "M":
            textos = [fmt_valor(l["valor"]) + ("" if pd.isna(l["variacao_pct"]) else "<br>" + fmt_pct(l["variacao_pct"]))
                      for _, l in s.iterrows()]
        fig.add_trace(go.Bar(x=rot, y=s["valor"], text=textos, textposition="outside", cliponaxis=False,
                             marker_color=[COR["claro"] if p else COR["principal"] for p in s["parcial"]],
                             hovertext=hover, hoverinfo="text"))
        fig.update_xaxes(type="category", categoryorder="array", categoryarray=rot)
        if textos:
            fig.update_yaxes(range=[0, float(s["valor"].max()) * 1.22 if s["valor"].max() > 0 else 1])
    titulo = f"{NOMES_METRICA[metrica]} por {NOMES_FREQ[freq]}" + (" (média por dia)" if por_dia else "")
    return _base(fig, titulo, "$" if metrica == "faturamento" else "")


def fig_lojas(serie_loja: pd.DataFrame, freq: str, metrica: str, modo: str, por_dia: bool = False) -> go.Figure:
    """Gráfico 3: uma linha por loja, em valores ou em participação (%)."""
    em_pct = modo.startswith("Participação")
    por_dia = por_dia and freq != "D" and not em_pct
    sl = participacao(serie_loja, metrica) if em_pct else serie_loja.copy()
    fmt = _formatador(metrica)
    fig = go.Figure()
    for i, (loja, g) in enumerate(sl.groupby("loja")):
        g = g.sort_values("inicio")
        y = g["participacao_pct"] if em_pct else com_valor(g, metrica, por_dia)
        rot = [rotulo_periodo(p, freq) for p in g["periodo"]]
        if em_pct:
            hover = [f"<b>{loja}</b> · {r}<br>Participação: {fmt_pct(v, sinal=False)}" for r, v in zip(rot, y)]
        else:
            hover = [f"<b>{loja}</b> · {r}<br>{NOMES_METRICA[metrica]}: {fmt(v)}" + ("/dia" if por_dia else "")
                     for r, v in zip(rot, y)]
        x = g["inicio"] if freq == "D" else rot
        fig.add_trace(go.Scatter(x=x, y=y, name=loja, mode="lines" if freq == "D" else "lines+markers",
                                 line=dict(color=_cor_loja(loja, i), width=2.4), hovertext=hover, hoverinfo="text"))
    if freq != "D" and not sl.empty:
        ordem = [rotulo_periodo(p, freq) for p in sorted(sl["periodo"].unique())]
        fig.update_xaxes(type="category", categoryorder="array", categoryarray=ordem)
    titulo = (f"Participação de cada loja ({NOMES_METRICA[metrica].lower()}) por {NOMES_FREQ[freq]}" if em_pct
              else f"{NOMES_METRICA[metrica]} por loja, por {NOMES_FREQ[freq]}" + (" (média por dia)" if por_dia else ""))
    fig = _base(fig, titulo, "" if em_pct or metrica != "faturamento" else "$", "%" if em_pct else "")
    fig.update_layout(showlegend=True)
    if em_pct:
        fig.update_yaxes(range=[0, 100])
    return fig


def fig_indice(idx: pd.DataFrame, rotulo_base: str) -> go.Figure:
    """Gráfico 5: índice (mês-base = 100) de faturamento por dia, transações por dia e receita por transação."""
    series = [("Faturamento por dia", "faturamento_dia_idx", COR["principal"], "solid", 3.2),
              ("Transações por dia", "transacoes_dia_idx", COR["destaque"], "dash", 2.4),
              ("Receita por transação", "receita_por_transacao_idx", COR["cinza"], "solid", 2.4)]
    rot = [rotulo_periodo(p, "M") for p in idx["periodo"]]
    fig = go.Figure()
    for nome, col, cor, tracejado, largura in series:
        fig.add_trace(go.Scatter(x=rot, y=idx[col], name=nome, mode="lines+markers",
                                 line=dict(color=cor, dash=tracejado, width=largura),
                                 hovertemplate=nome + ": %{y:.1f}<extra>%{x}</extra>"))
    fig.add_hline(y=100, line_width=1, line_color="rgba(128,128,128,0.6)")
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=rot)
    fig = _base(fig, f"De onde vem o crescimento? (índice, {rotulo_base} = 100)")
    fig.update_layout(showlegend=True)
    fig.update_yaxes(rangemode="normal", tickformat=".0f")
    return fig
