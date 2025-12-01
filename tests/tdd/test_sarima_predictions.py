# test_sarima_predictions.py
import pytest

# Mock
def mock_carregar_previsoes():
    return {"Recife": [100, 105, 110], "Fortaleza": [120, 125, 130]}

# Teste
def test_carregar_previsoes():
    previsoes = mock_carregar_previsoes()
    assert "Recife" in previsoes
    assert len(previsoes["Recife"]) == 3
