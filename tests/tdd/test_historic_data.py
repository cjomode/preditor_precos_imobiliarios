# test_historic_data.py
import pytest

# Mock
def mock_filtrar_historico(dados, coluna, valor):
    return [d for d in dados if d.get(coluna) == valor]

# Teste
def test_filtrar_historico():
    dados = [
        {"cidade": "Recife", "preco": 100},
        {"cidade": "Fortaleza", "preco": 120}
    ]
    resultado = mock_filtrar_historico(dados, "cidade", "Recife")
    assert len(resultado) == 1
    assert resultado[0]["cidade"] == "Recife"
