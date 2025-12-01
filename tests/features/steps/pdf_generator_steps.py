from behave import given, when, then
from unittest.mock import MagicMock


#MOCKS
def mock_filtrar_dados(cidade, mercado):
    if cidade == "Recife" and mercado == "Locação":
        return {
            "cidade": cidade,
            "mercado": mercado,
            "kpis": {"vagas": 120, "val_med": 2150},
            "historico": [100, 110, 120]
        }
    return None


def mock_gerar_pdf(dados):
    if not dados:
        return None
    
    return {
        "arquivo": b"%PDF-MOCK%",
        "conteudo": f"Relatório de {dados['cidade']} - {dados['mercado']}",
        "kpis": dados["kpis"],
        "historico": dados["historico"]
    }


def mock_salvar_arquivo(pdf_mock):
    if pdf_mock and pdf_mock.get("arquivo"):
        return "C:/Mock/relatorio.pdf"
    return None

#STEPS
@given('que filtrei a cidade "Recife" e mercado "Locação"')
def step_impl(context):
    context.filtro = mock_filtrar_dados("Recife", "Locação")
    assert context.filtro is not None


@when('clico no botão "Baixar relatório em PDF"')
def step_impl(context):
    context.pdf = mock_gerar_pdf(context.filtro)


@then("um arquivo PDF deve ser gerado com resumo e KPIs")
def step_impl(context):
    assert context.pdf is not None
    assert context.pdf["arquivo"].startswith(b"%PDF")
    assert "Recife" in context.pdf["conteudo"]
    assert "Locação" in context.pdf["conteudo"]
    assert "kpis" in context.pdf
    assert "historico" in context.pdf


@then("devo poder salvar o arquivo localmente")
def step_impl(context):
    caminho = mock_salvar_arquivo(context.pdf)
    assert caminho.endswith(".pdf")
