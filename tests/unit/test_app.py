import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import pandas as pd
from io import BytesIO
from app import (
    detectar_coluna,
    detectar_coluna_data,
    detectar_coluna_cidade,
    detectar_coluna_tipo,
    detectar_coluna_preco,
    texto_dashboard_acessivel,
    texto_previsoes_acessivel,
    texto_relatorio_acessivel,
    gerar_pdf_relatorio
)

def test_detectar_coluna():
    cols = ["DataVenda", "Cidade", "Preco_m2"]
    assert detectar_coluna(cols, ["data", "dt"]) == "DataVenda"
    assert detectar_coluna(cols, ["cidade", "municipio"]) == "Cidade"
    assert detectar_coluna(cols, ["preco", "valor_m2"]) == "Preco_m2"

def test_detectar_coluna_data():
    cols = ["DataVenda", "Cidade"]
    assert detectar_coluna_data(cols) == "DataVenda"

def test_detectar_coluna_cidade():
    cols = ["DataVenda", "Cidade"]
    assert detectar_coluna_cidade(cols) == "Cidade"

def test_detectar_coluna_tipo():
    cols = ["Tipo_Mercado", "Cidade"]
    assert detectar_coluna_tipo(cols) == "Tipo_Mercado"

def test_detectar_coluna_preco():
    cols = ["Preco_m2", "Cidade"]
    assert detectar_coluna_preco(cols) == "Preco_m2"


def test_texto_dashboard_acessivel():
    df = pd.DataFrame({
        "data": pd.date_range("2025-01-01", periods=3, freq='M'),
        "cidade": ["Recife"]*3,
        "tipo_mercado": ["Locação"]*3,
        "preco_m2": [1000, 1100, 1200]
    })
    txt = texto_dashboard_acessivel(df, "Recife", "Locação")
    assert "Recife" in txt
    assert "Locação" in txt
    assert "Preço médio do período" in txt

def test_texto_previsoes_acessivel():
    df = pd.DataFrame({
        "data": pd.date_range("2025-01-01", periods=3, freq='M'),
        "preco_previsto": [1300, 1350, 1400]
    })
    ultima_data_hist = pd.Timestamp("2024-12-31")
    txt = texto_previsoes_acessivel(df, "Recife", "Venda", ultima_data_hist)
    assert "Recife" in txt
    assert "Venda" in txt
    assert "Preço previsto no último mês" in txt

def test_texto_relatorio_acessivel():
    resumo = "Resumo do mercado"
    kpis = {"Média": 1000, "Máximo": 1200}
    txt = texto_relatorio_acessivel(resumo, kpis)
    assert "Resumo do mercado" in txt
    assert "Média" in txt
    assert "Máximo" in txt

def test_gerar_pdf_relatorio():
    df = pd.DataFrame({
        "data": pd.date_range("2025-01-01", periods=3, freq='M'),
        "preco_m2": [1000, 1100, 1200]
    })
    resumo_kpis = {"Média": "1000", "Máximo": "1200"}
    texto_resumo = "Resumo do relatório"
    pdf_bytes = gerar_pdf_relatorio("Recife", "Locação", df, resumo_kpis, texto_resumo)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b"%PDF"

