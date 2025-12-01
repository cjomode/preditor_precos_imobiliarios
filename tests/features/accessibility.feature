#encoding: UTF-8
#language: pt

Funcionalidade: Acessibilidade de áudio
  Como usuário com deficiência visual
  Quero ouvir o resumo das seções
  Para compreender os dados sem ler a tela

  Cenário: Ouvir resumo de relatório
    Dado que estou na aba Relatórios e PDF
    Quando clico no botão "Ouvir resumo desta seção"
    Então devo ouvir a leitura em voz alta do resumo do período
