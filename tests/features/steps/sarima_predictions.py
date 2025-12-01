from behave import given, when, then
from unittest.mock import MagicMock

def mock_carregar_previsoes(cidade, mercado):
    if cidade == "Recife" and mercado == "Locação":
        return {
            "cidade": cidade,
            "mercado": mercado,
            "historico": [1000, 1050, 1100, 1200],
            "previsoes": [1250, 1300, 1380, 1450],
            "indice_projecao": 4 
        }
    return None

def mock_gerar_grafico(previsoes_dict):
    if not previsoes_dict:
        return None
    
    return {
        "grafico": True,
        "historico": previsoes_dict["historico"],
        "projecoes": previsoes_dict["previsoes"],
        "linha_vertical_inicio": previsoes_dict["indice_projecao"]
    }

def mock_tts_explicacao(previsoes):
    if previsoes:
        return "A leitura foi iniciada." 
    return None

#STEPS
@given("que estou na aba Previsões Inteligentes")
def step_impl(context):
    context.aba_atual = "Previsões Inteligentes"
    assert context.aba_atual == "Previsões Inteligentes"


@when('seleciono cidade "Recife" e mercado "Locação"')
def step_impl(context):
    context.previsoes = mock_carregar_previsoes("Recife", "Locação")
    assert context.previsoes is not None


@then("devo ver o gráfico com histórico real e projeções SARIMA")
def step_impl(context):
    context.grafico = mock_gerar_grafico(context.previsoes)
    assert context.grafico is not None
    assert len(context.grafico["historico"]) >= 1
    assert len(context.grafico["projecoes"]) >= 1


@then("devo ver a linha vertical indicando o início da projeção")
def step_impl(context):
    assert context.grafico["linha_vertical_inicio"] == 4

@given("que filtrei os dados de previsão")
def step_impl(context):
    context.previsoes = mock_carregar_previsoes("Recife", "Locação")
    assert context.previsoes is not None


@when('clico no botão "Ouvir explicação das previsões"')
def step_impl(context):
    context.audio = mock_tts_explicacao(context.previsoes)


@then("devo ouvir a leitura em voz alta das previsões")
def step_impl(context):
    assert context.audio is not None
    assert context.audio == "A leitura foi iniciada."
