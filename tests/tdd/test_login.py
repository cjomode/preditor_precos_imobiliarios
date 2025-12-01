import pytest

def mock_login_basico(usuario, senha):
    if usuario == "admin" and senha == "123":
        return True
    else:
        return False

def mock_verificar_mfa(codigo):
    return codigo == "000000"

def test_login_sucesso():
    assert mock_login_basico("admin", "123") is True
    assert mock_verificar_mfa("000000") is True

def test_login_falha_usuario():
    assert mock_login_basico("user", "123") is False

def test_login_falha_mfa():
    assert mock_verificar_mfa("111111") is False
