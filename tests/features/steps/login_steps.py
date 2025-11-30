from behave import given, when, then
from unittest.mock import MagicMock


def mock_login_basico(usuario, senha):
    if usuario == "" or senha == "":
        return {"sucesso": False, "mensagem": "Usuário ou senha incorretos"}

    if usuario == "admin" and senha == "123":
        return {"sucesso": True, "mensagem": "Login básico realizado! Agora configure o MFA."}
    else:
        return {"sucesso": False, "mensagem": "Usuário ou senha incorretos"}


def mock_verificar_mfa(codigo):
    if codigo == "000000":
        return {"sucesso": True, "mensagem": "MFA válido"}
    else:
        return {"sucesso": False, "mensagem": "Código inválido. Tente novamente."}

#STEPS
@given("que estou na página de login")
def step_impl(context):
    context.usuario = None
    context.senha = None
    context.login_response = None
    context.mfa_response = None


@given("preencho corretamente os campos de usuário e senha")
def step_impl(context):
    context.usuario = "admin"
    context.senha = "123"


@given("preencho incorretamente os campos de usuário e senha")
def step_impl(context):
    context.usuario = "errado"
    context.senha = "senha_errada"


@given("não preencho os campos de usuário e senha")
def step_impl(context):
    context.usuario = ""
    context.senha = ""


@when("tento realizar o login")
def step_impl(context):
    context.login_response = mock_login_basico(context.usuario, context.senha)


@when("insiro o código MFA correto")
def step_impl(context):
    context.mfa_response = mock_verificar_mfa("000000")


@when("insiro um código MFA incorreto")
def step_impl(context):
    context.mfa_response = mock_verificar_mfa("999999")


@then("devo receber acesso ao sistema e visualizar o dashboard")
def step_impl(context):
    assert context.login_response["sucesso"] is True
    assert context.mfa_response["sucesso"] is True


@then('devo ver a mensagem "Código inválido. Tente novamente."')
def step_impl(context):
    assert context.mfa_response["mensagem"] == "Código inválido. Tente novamente."


# MFA após login básico 
@given("que realizei login básico com sucesso")
def step_impl(context):
    context.login_response = mock_login_basico("admin", "123")
    assert context.login_response["sucesso"] is True


@given("eu escaneio o QR code e digito o código MFA correto")
def step_impl(context):
    context.codigo_mfa = "000000"


@when('clico no botão "Verificar MFA"')
def step_impl(context):
    context.mfa_response = mock_verificar_mfa(context.codigo_mfa)


@then("devo acessar o dashboard")
def step_impl(context):
    assert context.mfa_response["sucesso"] is True


#Erro de login
@then('devo receber uma mensagem de "Usuário ou senha incorretos"')
def step_impl(context):
    assert context.login_response["mensagem"] == "Usuário ou senha incorretos"
