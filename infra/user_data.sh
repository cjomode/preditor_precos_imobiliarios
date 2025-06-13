#!/bin/bash

# Atualiza tudo
sudo apt update -y
sudo apt upgrade -y

# Instala Python, pip e Git
sudo apt install python3 python3-pip git -y

# Clona o repositório
cd /home/ubuntu
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
cd SEU_REPOSITORIO

# Instala dependências
pip3 install -r requirements.txt || pip3 install streamlit pandas plotly

# Executa o app na porta 8501 (liberada no security group)
nohup streamlit run app.py --server.port=8501 --server.enableCORS=false &
