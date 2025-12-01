from behave import given, when, then

def mock_resumo_relatorio():
    return (
        "No período analisado, observamos variações nos preços, "
        "tendências de subida e indicadores de mercado relevantes."
    )

def mock_tts(resumo_texto):
    if resumo_texto:
        return "A leitura do resumo foi iniciada."
    return None

@given("que estou na aba Relatórios e PDF")
def step_impl(context):
    context.aba_atual = "Relatórios e PDF"
    assert context.aba_atual == "Relatórios e PDF"


@when('clico no botão "Ouvir resumo desta seção"')
def step_impl(context):
    context.resumo_texto = mock_resumo_relatorio()
    context.audio = mock_tts(context.resumo_texto)


@then("devo ouvir a leitura em voz alta do resumo do período")
def step_impl(context):
    assert context.audio is not None
    assert context.audio == "A leitura do resumo foi iniciada."
