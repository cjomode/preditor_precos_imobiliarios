# 🏠 Preditor de Preços Imobiliários Regionais  

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-orange?logo=streamlit)
![Plotly](https://img.shields.io/badge/Charts-Plotly-lightgrey?logo=plotly)
![AWS](https://img.shields.io/badge/AWS-EC2-informational?logo=amazon-aws&logoColor=white&color=232F3E)
![CI/CD](https://img.shields.io/github/actions/workflow/status/cjomode/preditor_precos_imobiliarios/deploy.yml?branch=main&label=CI%2FCD&logo=github)
![MFA](https://img.shields.io/badge/🔐_MFA-Ativado-success)
![Pytest](https://img.shields.io/badge/Testes-Pytest-yellow?logo=pytest)
![Selenium](https://img.shields.io/badge/Testes%20UI-Selenium-43B02A?logo=selenium&logoColor=white)
![Status](https://img.shields.io/badge/Status-Em%20desenvolvimento-blueviolet)
![Open%20Source](https://img.shields.io/badge/Open%20Source-Yes-brightgreen)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-blue)
![Contribuição](https://img.shields.io/badge/Feito%20com%20💜%20por-Gabriel,%20Juliana,%20Luana%20e%20Vitor-blueviolet)

---

## 📖 Descrição do Projeto  

O **Preditor de Preços Imobiliários Regionais** é um sistema de análise e previsão de valores de imóveis na região Nordeste do Brasil.  
Criado como parte de uma disciplina de **Big Data**, o projeto busca apoiar **corretores, consultores imobiliários e gestores urbanos** na tomada de decisão, oferecendo insights claros sobre tendências de valorização e desvalorização imobiliária.  

💡 A aplicação combina **ciência de dados**, **modelagem preditiva (SARIMA)** e **visualização interativa** via Streamlit, tornando a análise acessível e intuitiva até para quem não tem experiência técnica.

---

## ✨ Principais Funcionalidades  

🔒 **Autenticação MFA:** Sistema de login com múltiplos fatores de autenticação, garantindo acesso seguro ao painel.  

📊 **Dashboard Interativo:** Visualizações dinâmicas com Plotly, incluindo gráficos de linha, barras, boxplot e pizza, que mostram tendências e estatísticas descritivas dos preços por cidade e tipo de mercado.  

🧠 **Modelagem Preditiva (SARIMA):** Modelos treinados e armazenados em `joblib` que permitem estimar valores futuros com base em séries temporais históricas.  

🧾 **Relatórios Automáticos (PDF):** Geração de relatórios analíticos com texto descritivo, explicações automáticas e KPIs principais.  

🚀 **Testes Automatizados:** Conjunto de testes com **Pytest** e **Selenium**, cobrindo desde o login até as funcionalidades do dashboard.  

---

## 📁 Estrutura Atual do Projeto  

A estrutura do repositório foi atualizada para refletir o ambiente real de desenvolvimento:  

```bash
preditor_precos_imobiliarios/
├── .github/
│   └── workflows/
│       ├── deploy.yml           # GitHub Actions para deploy automatizado
│       └── tests.yml            # GitHub Actions para testes automatizados
│
├── tests/                       # Testes automatizados
│   ├── e2e/                     # Testes ponta-a-ponta (login, autenticação, etc.)
│   │   ├── test_login_falha.py
│   │   └── test_login_sucesso.py
│   └── unit/                    # Testes unitários (funções e módulos isolados)
│       └── test_app.py
│
├── venv/                        # Ambiente virtual local (não versionado)
│   ├── Lib/
│   ├── Scripts/
│   └── pyvenv.cfg
│
├── app.py                       # Aplicação principal (Streamlit + autenticação MFA)
├── csv_unico.csv                # Base de dados consolidada (histórico de preços)
├── modelos_sarima.joblib        # Modelos SARIMA pré-treinados
│
├── LICENSE                      # Licença MIT do projeto
├── README.md                    # Documentação principal (este arquivo)
└── requirements.txt              # Dependências do projeto (pip)
```

## 🛠️ Tecnologias e Ferramentas Utilizadas  

| 🧩 **Categoria** | 🛠️ **Ferramenta / Tecnologia** | 💬 **Descrição** |
|------------------|-------------------------------|------------------|
| **Linguagem** | Python 3.9+ | Núcleo do projeto |
| **Framework Web** | Streamlit | Interface interativa e responsiva |
| **Visualização** | Plotly | Criação de gráficos interativos |
| **Análise de Dados** | Pandas | Manipulação e análise de dados tabulares |
| **Modelagem** | Statsmodels (SARIMA) | Previsão de séries temporais |
| **Testes** | Pytest / Selenium | Testes automatizados (unitários e de interface) |
| **Infraestrutura** | Terraform + AWS EC2 | Provisionamento e hospedagem na nuvem |
| **CI/CD** | GitHub Actions | Automação de testes e deploy contínuo |
| **Controle de Versão** | Git & GitHub | Colaboração, versionamento e integração |


## 🧭 Instalação e Execução Local  

### 1️⃣ Clone o repositório  
```bash
git clone https://github.com/cjomode/preditor_precos_imobiliarios.git
cd preditor_precos_imobiliarios
```

### 2️⃣ Crie o ambiente virtual
```bash
python -m venv venv
# Ative o ambiente:
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```
### 3️⃣ Instale as dependências
```bash
pip install -r requirements.txt
```

### 4️⃣ Execute a aplicação
O app abrirá no navegador (por padrão em http://localhost:8501) com tela de login protegida por MFA.
Após autenticação, é possível explorar dashboards interativos e gerar relatórios completos. 🎯
```bash
streamlit run app.py
```

## ☁️ Deploy em AWS EC2

O deploy do app foi planejado para ocorrer de forma automatizada com **Terraform** e **GitHub Actions**.

- O **Terraform** define e cria uma instância **EC2** com todas as dependências do Streamlit.
- O script **`user_data.sh`** garante que o app inicie automaticamente no servidor assim que a máquina é criada.
- O pipeline **`deploy.yml`** permitirá acionar o deploy via push, garantindo entrega contínua.

💡 Com um simples `terraform apply`, o ambiente completo é criado, configurado e pronto para uso!

---

## 💡 Status Atual

- ✅ Estrutura do projeto revisada e modular  
- ✅ Dashboard interativo funcional  
- ✅ Relatórios automáticos (PDF)  
- ✅ Testes unitários e E2E implementados  
- 🔄 Deploy automatizado (em configuração final)  

---

## 🙌 Créditos

Este projeto foi idealizado e desenvolvido por:  
**Gabriel, Juliana, Luana e Vitor** 💜  

Combinando conhecimentos em *data science*, engenharia de software e infraestrutura, a equipe criou uma ferramenta moderna e acessível para análise imobiliária.

---

## 📄 Licença

Distribuído sob a licença **MIT**.  
Você pode usar, modificar e redistribuir este software livremente, desde que mantenha os créditos originais.

> “Com liberdade vem responsabilidade.”  
> — Use com sabedoria 😄


