#encoding: UTF-8
#language: pt

Funcionalidade: Visualização de preços históricos
    Como usuário do dashboard
    Quero filtrar por cidade e tipo de mercado
    Para analisar a evolução do preço médio

    Cenário: Selecionar cidade e mercado
        Dado que estou no dashboard de Visualização de Dados
        Quando eu seleciono a cidade "Recife"
        E seleciono o tipo de mercado "Locação"
        Então devo ver um gráfico de linha do preço médio ao longo do tempo

    Cenário: Ouvir explicação da seção
        Dado que filtrei os dados por cidade e tipo de mercado
        Quando clico no botão "Ouvir explicação desta seção"
        Então devo ouvir a leitura em voz alta do resumo histórico
