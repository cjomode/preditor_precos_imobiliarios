# # test_login.py
# import pytest
# from login_steps import mock_login_basico, mock_verificar_mfa

# # --- Testes unitários das funções ---

# def test_mock_login_basico_sucesso():
#     resp = mock_login_basico("admin", "123")
#     assert resp["sucesso"] is True
#     assert resp["mensagem"] == "Login básico realizado! Agora configure o MFA."

# def test_mock_login_basico_erro():
#     resp = mock_login_basico("errado", "senha_errada")
#     assert resp["sucesso"] is False
#     assert resp["mensagem"] == "Usuário ou senha incorretos"

# def test_mock_login_basico_campos_vazios():
#     resp = mock_login_basico("", "")
#     assert resp["sucesso"] is False
#     assert resp["mensagem"] == "Usuário ou senha incorretos"

# def test_mock_verificar_mfa_valido():
#     resp = mock_verificar_mfa("000000")
#     assert resp["sucesso"] is True
#     assert resp["mensagem"] == "MFA válido"

# def test_mock_verificar_mfa_invalido():
#     resp = mock_verificar_mfa("999999")
#     assert resp["sucesso"] is False
#     assert resp["mensagem"] == "MFA inválido"

# # --- Testes integrados simulando fluxo de usuário ---

# def test_fluxo_login_completo_sucesso():
#     # Dado que estou na página de login e preencho corretamente
#     usuario = "admin"
#     senha = "123"
    
#     # Quando tento realizar login
#     login_resp = mock_login_basico(usuario, senha)
#     assert login_resp["sucesso"] is True
#     assert login_resp["mensagem"] == "Login básico realizado! Agora configure o MFA."
    
#     # E insiro MFA correto
#     mfa_resp = mock_verificar_mfa("000000")
    
#     # Então devo receber acesso
#     assert mfa_resp["sucesso"] is True
#     assert mfa_resp["mensagem"] == "MFA válido"

# def test_fluxo_login_com_erro_usuario_senha():
#     usuario = "errado"
#     senha = "senha_errada"
    
#     login_resp = mock_login_basico(usuario, senha)
#     assert login_resp["sucesso"] is False
#     assert login_resp["mensagem"] == "Usuário ou senha incorretos"

# def test_fluxo_login_com_mfa_invalido():
#     usuario = "admin"
#     senha = "123"
    
#     login_resp = mock_login_basico(usuario, senha)
#     assert login_resp["sucesso"] is True
    
#     mfa_resp = mock_verificar_mfa("999999")
#     assert mfa_resp["sucesso"] is False
#     assert mfa_resp["mensagem"] == "MFA inválido"

# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# import pytest
# from features.steps.login_steps import mock_login_basico, mock_verificar_mfa

# # --- Testes unitários das funções ---

# def test_mock_login_basico_sucesso():
#     resp = mock_login_basico("admin", "123")
#     assert resp["sucesso"] is True
#     assert resp["mensagem"] == "Login básico realizado! Agora configure o MFA."

# def test_mock_login_basico_erro():
#     resp = mock_login_basico("errado", "senha_errada")
#     assert resp["sucesso"] is False
#     assert resp["mensagem"] == "Usuário ou senha incorretos"

# def test_mock_login_basico_campos_vazios():
#     resp = mock_login_basico("", "")
#     assert resp["sucesso"] is False
#     assert resp["mensagem"] == "Usuário ou senha incorretos"

# def test_mock_verificar_mfa_valido():
#     resp = mock_verificar_mfa("000000")
#     assert resp["sucesso"] is True
#     assert resp["mensagem"] == "MFA válido"

# def test_mock_verificar_mfa_invalido():
#     resp = mock_verificar_mfa("999999")
#     assert resp["sucesso"] is False
#     assert resp["mensagem"] == "MFA inválido"

# # --- Testes integrados simulando fluxo de usuário ---

# def test_fluxo_login_completo_sucesso():
#     # Dado que estou na página de login e preencho corretamente
#     usuario = "admin"
#     senha = "123"
    
#     # Quando tento realizar login
#     login_resp = mock_login_basico(usuario, senha)
#     assert login_resp["sucesso"] is True
#     assert login_resp["mensagem"] == "Login básico realizado! Agora configure o MFA."
    
#     # E insiro MFA correto
#     mfa_resp = mock_verificar_mfa("000000")
    
#     # Então devo receber acesso
#     assert mfa_resp["sucesso"] is True
#     assert mfa_resp["mensagem"] == "MFA válido"

# def test_fluxo_login_com_erro_usuario_senha():
#     usuario = "errado"
#     senha = "senha_errada"
    
#     login_resp = mock_login_basico(usuario, senha)
#     assert login_resp["sucesso"] is False
#     assert login_resp["mensagem"] == "Usuário ou senha incorretos"

# def test_fluxo_login_com_mfa_invalido():
#     usuario = "admin"
#     senha = "123"
    
#     login_resp = mock_login_basico(usuario, senha)
#     assert login_resp["sucesso"] is True
    
#     mfa_resp = mock_verificar_mfa("999999")
#     assert mfa_resp["sucesso"] is False
#     assert mfa_resp["mensagem"] == "MFA inválido"

# test_login.py
import pytest

# Mocks
def mock_login_basico(usuario, senha):
    if usuario == "admin" and senha == "123":
        return True
    return False

def mock_verificar_mfa(codigo):
    return codigo == "000000"

# Testes
def test_login_sucesso():
    assert mock_login_basico("admin", "123") is True
    assert mock_verificar_mfa("000000") is True

def test_login_falha_usuario():
    assert mock_login_basico("user", "123") is False

def test_login_falha_mfa():
    assert mock_verificar_mfa("111111") is False
