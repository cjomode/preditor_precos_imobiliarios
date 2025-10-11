import pandas as pd
from app import gerar_codigo_mfa, gerar_grafico_imobiliario, gerar_grafico_bcb



def test_gerar_grafico_imobiliario():
    df = pd.DataFrame({
        "Data": pd.date_range(start="2023-01-01", periods=3, freq='M'),
        "Preço médio (R$/m²)Total": [5000, 5100, 5200]
    })
    fig = gerar_grafico_imobiliario(df, "Recife", "Preço médio (R$/m²)Total")
    assert fig.data, "Gráfico deve conter dados"
    assert fig.layout.title.text == "Preço médio (R$/m²)Total - Recife"


def test_gerar_grafico_bcb():
    df = pd.DataFrame({
        "Indicador": ["IPCA"] * 3,
        "Data": ["2023-01-01", "2023-02-01", "2023-03-01"],
        "Media": ["5,2", "5,4", "5,3"],
        "Mediana": ["5,0", "5,2", "5,1"],
        "DesvioPadrao": ["0,2", "0,3", "0,2"],
        "Minimo": ["4,8", "4,9", "5,0"],
        "Maximo": ["5,5", "5,6", "5,4"]
    })
    fig, df_filtrado = gerar_grafico_bcb(df, "IPCA")
    assert not df_filtrado.empty, "DataFrame filtrado não pode estar vazio"
    assert "Media" in df_filtrado.columns
    assert fig.layout.title.text == "Indicador: IPCA"
