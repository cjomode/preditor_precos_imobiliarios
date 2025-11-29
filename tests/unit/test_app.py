# import sys
# import os
# import pytest
# import pandas as pd
# from datetime import datetime

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# from app import (
#     detectar_coluna,
#     detectar_coluna_cidade,
#     detectar_coluna_data,
#     detectar_coluna_tipo,
#     detectar_coluna_preco,
#     carregar_dados_historicos,
#     texto_dashboard_acessivel,
#     gerar_pdf_relatorio
# )


# @pytest.fixture
# def df_exemplo():
#     return pd.DataFrame({
#         "data": pd.date_range("2021-01-01", periods=6, freq="M"),
#         "cidade": ["Recife"] * 6,
#         "tipo_mercado": ["Residencial"] * 6,
#         "preco_m2": [3000, 3100, 3200, 3300, 3400, 3500]
#     })


# def test_detectar_coluna_cidade():
#     cols = ["Cidade", "Data", "Valor"]
#     assert detectar_coluna_cidade(cols) == "Cidade"


# def test_detectar_coluna_data():
#     cols = ["MesReferencia", "cidade"]
#     assert detectar_coluna_data(cols) == "MesReferencia"


# def test_detectar_coluna_tipo():
#     cols = ["Tipo_Mercado", "cidade"]
#     assert detectar_coluna_tipo(cols) == "Tipo_Mercado"


# def test_detectar_coluna_preco():
#     cols = ["Preço_médio_m2", "cidade"]
#     assert detectar_coluna_preco(cols) == "Preço_médio_m2"


# def test_carregar_dados_historicos(monkeypatch, tmp_path):
#     # Cria CSV fake
#     csv = tmp_path / "csv_unico.csv"
#     df = pd.DataFrame({
#         "Data": ["2024-01-01", "2024-02-01"],
#         "Cidade": ["Recife", "Recife"],
#         "Tipo_Mercado": ["Residencial", "Residencial"],
#         "Preco_m2": ["3.000", "3.200"],
#     })
#     df.to_csv(csv, index=False)

#     monkeypatch.setattr("app.CSV_PATH", str(csv))

#     df_res = carregar_dados_historicos()

#     assert not df_res.empty
#     assert list(df_res.columns) == ["data", "cidade", "tipo_mercado", "preco_m2"]
#     assert df_res["preco_m2"].iloc[0] == 3000.0


# def test_texto_dashboard(df_exemplo):
#     texto = texto_dashboard_acessivel(df_exemplo, "Recife", "Residencial")
#     assert "Recife" in texto
#     assert "Residencial" in texto
#     assert "Variação" in texto or "variação" in texto


# def test_gerar_pdf(df_exemplo):
#     resumo = {
#         "Preço Médio": "R$ 3.200/m²",
#         "Maior Preço": "R$ 3.500/m²"
#     }

#     texto = "Resumo do mercado."

#     pdf_bytes = gerar_pdf_relatorio(
#         cidade="Recife",
#         mercado="Residencial",
#         df_base=df_exemplo,
#         resumo_kpis=resumo,
#         texto_resumo=texto
#     )

#     assert isinstance(pdf_bytes, bytes)
#     assert len(pdf_bytes) > 1000

# test_app.py

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

# ----------------------------
# Testar funções de detecção
# ----------------------------
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

# ----------------------------
# Testar funções de texto
# ----------------------------
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

# ----------------------------
# Testar PDF
# ----------------------------
def test_gerar_pdf_relatorio():
    df = pd.DataFrame({
        "data": pd.date_range("2025-01-01", periods=3, freq='M'),
        "preco_m2": [1000, 1100, 1200]
    })
    resumo_kpis = {"Média": "1000", "Máximo": "1200"}
    texto_resumo = "Resumo do relatório"
    pdf_bytes = gerar_pdf_relatorio("Recife", "Locação", df, resumo_kpis, texto_resumo)
    assert isinstance(pdf_bytes, bytes)
    # Teste simples: PDF começa com %PDF
    assert pdf_bytes[:4] == b"%PDF"

