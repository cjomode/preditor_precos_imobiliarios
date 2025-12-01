# test_pdf_generator.py
import pytest

# Mock
def mock_gerar_pdf(conteudo):
    if not conteudo:
        return None
    return "PDF gerado com sucesso."

# Testes
def test_gerar_pdf_com_conteudo():
    resultado = mock_gerar_pdf("Relatório de teste")
    assert resultado == "PDF gerado com sucesso."

def test_gerar_pdf_sem_conteudo():
    resultado = mock_gerar_pdf("")
    assert resultado is None
