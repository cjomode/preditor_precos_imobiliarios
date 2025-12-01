from behave import given, when, then

def mock_filtrar_historico(cidade, mercado):
    if cidade == "Recife" and mercado == "Locação":
        return {
            "cidade": cidade,
            "mercado": mercado,
            "dados": [1800, 1850, 1900, 2000, 2100] 
        }
    return None


def mock_gerar_grafico_linha(historico):
    if not historico:
        return None
    
    return {
        "grafico": True,
        "tipo": "linha",
        "dados": historico["dados"]
    }


def mock_gerar_resumo_historico(historico):
    if historico:
        return (
            f"O histórico para {historico['cidade']} no mercado de "
            f"{historico['mercado']} mostra tendência de crescimento."
        )
    return None


def mock_tts(texto):
    if texto:
        return "A leitura do resumo histórico foi iniciada."
    return None

@given("que estou no dashboard de Visualização de Dados")
def step_impl(context):
    context.pagina_atual = "Visualização de Dados"
    assert context.pagina_atual == "Visualização de Dados"


@when('eu seleciono a cidade "Recife"')
def step_impl(context):
    context.cidade = "Recife"


@when('seleciono o tipo de mercado "Locação"')
def step_impl(context):
    context.mercado = "Locação"
    context.historico = mock_filtrar_historico(context.cidade, context.mercado)
    assert context.historico is not None


@then("devo ver um gráfico de linha do preço médio ao longo do tempo")
def step_impl(context):
    context.grafico = mock_gerar_grafico_linha(context.historico)
    assert context.grafico is not None
    assert context.grafico["tipo"] == "linha"
    assert len(context.grafico["dados"]) >= 1


@given("que filtrei os dados por cidade e tipo de mercado")
def step_impl(context):
    context.historico = mock_filtrar_historico("Recife", "Locação")
    assert context.historico is not None


@when('clico no botão "Ouvir explicação desta seção"')
def step_impl(context):
    context.resumo = mock_gerar_resumo_historico(context.historico)
    context.audio = mock_tts(context.resumo)


@then("devo ouvir a leitura em voz alta do resumo histórico")
def step_impl(context):
    assert context.audio is not None
    assert context.audio == "A leitura do resumo histórico foi iniciada."
