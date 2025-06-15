# 🏠 Preditor de Preços Imobiliários Regionais

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-orange?logo=streamlit)
![Plotly](https://img.shields.io/badge/Charts-Plotly-lightgrey?logo=plotly)
![Terraform](https://img.shields.io/badge/Terraform-Used-5f43e9?logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-EC2-informational?logo=amazon-aws&logoColor=white&color=232F3E)
![CI/CD](https://img.shields.io/github/actions/workflow/status/cjomode/preditor_precos_imobiliarios/deploy.yml?label=CI%2FCD&logo=github)
![MFA](https://img.shields.io/badge/🔐_MFA-Ativado-success)
![Pytest](https://img.shields.io/badge/Testes-Pytest-yellow?logo=pytest)
![Selenium](https://img.shields.io/badge/Testes%20UI-Selenium-43B02A?logo=selenium&logoColor=white)
![Status](https://img.shields.io/badge/Status-Finalizado-brightgreen)
![Open%20Source](https://img.shields.io/badge/Open%20Source-Yes-brightgreen)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-blue)
![Contribuição](https://img.shields.io/badge/Feito%20com%20💜%20por-Gabriel,%20Juliana,%20Luana%20e%20Vitor-blueviolet)



## 📖 Descrição do Projeto
Bem-vindo ao Preditor de Preços Imobiliários Regionais! Este projeto inovador utiliza Big Data para prever a valorização ou desvalorização imobiliária na região Nordeste do Brasil. 
### 🎯 Desenvolvido como parte de uma disciplina de Big Data, o objetivo é auxiliar corretores, consultores imobiliários e gestores urbanos a antecipar tendências de mercado, permitindo decisões mais informadas e estratégicas. Com uma interface web interativa e dados abrangentes de diversas capitais nordestinas, nossa aplicação oferece insights valiosos sobre o comportamento do mercado imobiliário regional.

## ✨ Destaques do Projeto
   🔒 Autenticação MFA: Aplicação construída em Streamlit com autenticação de múltiplos fatores (MFA). Somente usuários autorizados conseguem acessar o dashboard, garantindo segurança extra ao sistema.
   
   📊 Visualização Interativa: Integração com Plotly para gráficos dinâmicos e interativos. Explore os dados de imóveis (vendas, aluguel, etc.) através de visuais ricos, filtrando por cidade e período para identificar padrões de valorização/desvalorização.
   
   🤖 Modelo Preditivo Inteligente: Modelo de machine learning treinado em um amplo conjunto de dados regionais (incluindo informações de diversas capitais do NE e indicadores econômicos). Ele estima a probabilidade de um imóvel valorizar ou desvalorizar, fornecendo recomendações de forma simples e intuitiva.
   
  🛠️ Infraestrutura como Código: Uso de Terraform para definir toda a infraestrutura em nuvem. A configuração abrange a criação de uma instância AWS EC2, grupos de segurança, chaves de acesso e scripts de inicialização (user data) que executam o Streamlit automaticamente. Isso torna o deploy reproduzível e escalável com apenas um comando!
  
  🚀 CI/CD Automatizado: Pipeline de GitHub Actions incluído (deploy.yml) para futuramente automatizar o processo de deploy. Assim, sempre que houver atualizações, será possível implementar rapidamente a aplicação em produção de forma contínua e confiável.

# 📁 Estrutura do Projeto
A organização do repositório foi planejada para clareza e modularidade. 
```bash
preditor_precos_imobiliarios/
├── app/                    # Módulos do app Streamlit (interface e autenticação)
├── data/                   # Dados tratados de imóveis (venda e aluguel)
├── db/                     # Bancos locais e modelos pré-processados
├── infra/                  # Infraestrutura como código (Terraform + user_data.sh)
│   ├── main.tf
│   ├── outputs.tf
│   ├── user_data.sh
│   └── variables.tf
├── notebooks/              # Notebooks de EDA e desenvolvimento de modelo
├── script/                 # Scripts auxiliares para tratamento de dados e ML
├── .github/
│   └── workflows/
│       └── deploy.yml      # GitHub Actions para deploy automatizado
├── .gitignore              # Ignora arquivos sensíveis e diretórios de build
├── app.py                  # Código principal do app com MFA + dashboard
├── LICENSE                 # Licença MIT do projeto
├── README.md               # Documentação do projeto (você está aqui!)
└── requirements.txt        # Dependências do projeto (pip)
```
# 🛠️ Tecnologias e Ferramentas Utilizadas

### Este projeto reúne um ecossistema moderno de tecnologias de ciência de dados, desenvolvimento web e DevOps:

Linguagem: Python 3 – núcleo do projeto, utilizado tanto na análise de dados quanto no back-end do aplicativo.

### Bibliotecas Principais:

Streamlit (framework web para criar a interface do dashboard de forma rápida e Pythonica),

Plotly (visualização de dados interativa em gráficos, embutida no Streamlit),

Pandas (manipulação e análise de dados tabulares),

Scikit-Learn (ou bibliotecas equivalentes de ML, para treinar o modelo preditivo),

PyTest e Selenium (utilizados para testes automatizados da aplicação e da interface).

Jupyter Notebook: Ambiente usado para exploração inicial e limpeza dos dados.

Infraestrutura: Terraform para descrição da infraestrutura em código, provisionando serviços AWS (especialmente EC2 para hospedar o app).

Plataforma Cloud: AWS EC2 – máquina virtual na nuvem onde o dashboard Streamlit poderá rodar continuamente para acesso dos usuários finais.

CI/CD: GitHub Actions – pipeline configurado para integrar e futuramente implantar o projeto automaticamente (build, testes e deploy). Isso garante qualidade e agilidade nas entregas.

Controle de Versão: Git & GitHub – colaboração da equipe e versionamento de todo o código fonte, notebooks e infra, permitindo rastreabilidade das contribuições e trabalho em paralelo via branches.


# 🧭 Instalação e Execução Local

Siga os passos abaixo para rodar o projeto localmente em seu ambiente de desenvolvimento:

#### 1. Clone o repositório:
```bash
git clone https://github.com/cjomode/preditor_precos_imobiliarios.git
```
Entre no diretório do projeto: cd preditor_precos_imobiliarios.

#### 2. Crie um ambiente virtual (opcional, mas recomendável):
```bash
python3 -m venv venv
source venv/bin/activate  # no Windows: venv\Scripts\activate
```

#### 3. Instale as dependências:
```bash
pip install -r requirements.txt
```
Certifique-se de que todas as bibliotecas sejam instaladas corretamente.

#### 4. Execute a aplicação Streamlit:
```bash
streamlit run app.py
```
Isso iniciará o servidor local do Streamlit. O console exibirá um URL (por padrão http://localhost:8501) – abra esse endereço no seu navegador web.

#### 5. Use o dashboard: Ao acessar o app, você será apresentado à tela de login com MFA. Insira suas credenciais de acesso e o código de autenticação de dois fatores (conforme configurado) para entrar.
Uma vez autenticado, você poderá navegar pelos gráficos interativos e consultar previsões de valorização/desvalorização para diferentes cidades e cenários. 🎉

# ☁️ Deploy Futuro em EC2 com Terraform

Deploy automatizado está a caminho! Em breve, planejamos disponibilizar este aplicativo na nuvem usando a infraestrutura definida por Terraform. Todo o necessário já está configurado no diretório infra/. Em resumo, o plano de deploy é:

Infra AWS: O Terraform configura uma instância EC2 com ambiente para rodar o Streamlit. Ao executar terraform apply, uma VM é criada e provisionada automaticamente (incluindo regras de firewall via Security Group para acesso web).

O script de inicialização (user_data.sh) garante que, assim que a máquina for lançada, o app Streamlit inicie automaticamente em background.

Automação: A integração com GitHub Actions (deploy.yml) permitirá acionar o deploy com um simples push ou comando manual. Isso significa que atualizações no código poderão refletir no servidor em poucos minutos, sem passos manuais complexos. 🚀
Acesso: Após o deploy, a aplicação estará acessível via o IP público da EC2 (ou domain configurado) – prático para demonstrações e uso real pelos interessados. Teremos um ambiente persistente onde o dashboard ficará online 24/7.

#### Nota: Para realizar o deploy por conta própria, é necessário ter o Terraform instalado e credenciais AWS configuradas em sua máquina. Embora seja opcional para usuários finais, essa etapa mostra como o projeto está pronto para escalabilidade e implantação profissional em ambiente de produção.

# 🙌 Créditos

Este projeto foi idealizado e desenvolvido com muita dedicação por: Gabriel, Juliana, Luana e Vitor.

Cada colaborador contribuiu com habilidades únicas em data science, desenvolvimento e infraestrutura para tornar o Preditor de Preços Imobiliários uma realidade.

💙 Agradecemos por conferir nosso projeto! Esperamos que Preditor de Preços Imobiliários Regionais seja útil e inspirador. 

Sinta-se à vontade para contribuir, sugerir melhorias ou relatar issues. Boas previsões e bons negócios! 👋😊

# 📄 Licença

Este projeto está licenciado sob os termos da Licença MIT.

Isso significa que você pode usar, copiar, modificar, mesclar, publicar, distribuir e até vender o software, desde que mantenha os créditos originais. 💖

 #### “Com liberdade vem responsabilidade.” – Use com sabedoria! 😄
