#encoding: UTF-8
#language: pt

Funcionalidade: Previsões de preços futuros
    Como usuário do dashboard
    Quero ver as projeções SARIMA
    Para analisar o comportamento futuro do mercado

    Cenário: Visualizar previsões para uma cidade e mercado
        Dado que estou na aba Previsões Inteligentes
        Quando seleciono cidade "Recife" e mercado "Locação"
        Então devo ver o gráfico com histórico real e projeções SARIMA
        E devo ver a linha vertical indicando o início da projeção

    Cenário: Ouvir explicação das previsões
        Dado que filtrei os dados de previsão
        Quando clico no botão "Ouvir explicação das previsões"
        Então devo ouvir a leitura em voz alta das previsões
