#encoding: UTF-8
#language: pt

Funcionalidade: Exportação de relatório
    Como usuário do dashboard
    Quero baixar um relatório em PDF
    Para registrar os KPIs e análise histórica

    Cenário: Gerar relatório em PDF
        Dado que filtrei a cidade "Recife" e mercado "Locação"
        Quando clico no botão "Baixar relatório em PDF"
        Então um arquivo PDF deve ser gerado com resumo e KPIs
        E devo poder salvar o arquivo localmente
