import os
import pytest
import pandas as pd
from app import listar_cidades, carregar_cidade
import plotly.express as px


def test_listar_cidades():
    def test_listar_cidades():
    # Testa tabela existente
        cidades = listar_cidades("locacao")
        assert isinstance(cidades, list), "Deve retornar uma lista"
        if cidades:
            assert all(isinstance(c, str) for c in cidades), "Todos os elementos devem ser strings"

    # Para tabela inexistente
    cidades = listar_cidades("tabela_inexistente")
    assert cidades == []

def test_carregar_cidade():
    cidades = listar_cidades("locacao")
    if cidades:
        df = carregar_cidade("locacao", cidades[0])
        assert isinstance(df, pd.DataFrame)
        assert "Data" in df.columns

def test_grafico_gerado():
    # Dados simulando o gráfico que você enviou
    df = pd.DataFrame({
        "Data": pd.date_range(start="2022-01-01", periods=40, freq='M'),
        "Preço médio (R$/m²)Total": [
            17.1, 17.2, 17.0, 16.4, 16.2, 16.5, 17.0, 17.3, 17.5, 17.3,
            17.2, 17.4, 17.1, 16.9, 17.0, 17.8, 18.2, 18.9, 19.5, 20.2,
            21.0, 21.5, 21.6, 21.6, 22.4, 23.5, 23.7, 24.0, 23.8, 23.5,
            23.6, 23.8, 24.0, 24.2, 25.5, 25.7, 26.0, 25.8, 25.5, 26.3
        ]
    })

    # Cria gráfico
    fig = px.line(
        df,
        x="Data",
        y="Preço médio (R$/m²)Total",
        title="Mercado de Locação — Aracaju",
        markers=True,
        line_shape="spline"
    )

    # ✅ Testa se o gráfico possui dados
    assert fig.data, "Gráfico deve conter dados"

    # ✅ Testa título
    assert fig.layout.title.text == "Mercado de Locação — Aracaju"

    # ✅ Testa se eixo X contém datas
    x_values = [str(pt)[:10] for pt in df["Data"]]
    fig_x_values = [str(pt)[:10] for pt in fig.data[0].x]
    assert fig_x_values == x_values

    # ✅ Testa se eixo Y contém valores
    y_values = list(df["Preço médio (R$/m²)Total"])
    fig_y_values = list(fig.data[0].y)
    assert fig_y_values == y_values