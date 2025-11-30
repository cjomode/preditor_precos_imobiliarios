#encoding: UTF-8
#language: pt

Funcionalidade: Login com MFA
    Eu como usuário do sistema PredImóveis
    Quero realizar o login com autenticação multifator
    Para visualizar os dados

    Cenário: Login com sucesso e MFA válido
        Dado que estou na página de login
        E preencho corretamente os campos de usuário e senha
        Quando tento realizar o login
        E insiro o código MFA correto
        Então devo receber acesso ao sistema e visualizar o dashboard

    Cenário: Login básico correto, MFA inválido
        Dado que estou na página de login
        E preencho corretamente os campos de usuário e senha
        Quando tento realizar o login
        E insiro um código MFA incorreto
        Então devo ver a mensagem "Código inválido. Tente novamente."


    Cenário: MFA correto
        Dado que realizei login básico com sucesso
        E eu escaneio o QR code e digito o código MFA correto
        Quando clico no botão "Verificar MFA"
        Então devo acessar o dashboard

    Cenário: Login com usuário ou senha incorretos
        Dado que estou na página de login
        E preencho incorretamente os campos de usuário e senha
        Quando tento realizar o login
        Então devo receber uma mensagem de "Usuário ou senha incorretos"

    Cenário: Campos vazios no login
        Dado que estou na página de login
        E não preencho os campos de usuário e senha
        Quando tento realizar o login
        Então devo receber uma mensagem de "Usuário ou senha incorretos"

