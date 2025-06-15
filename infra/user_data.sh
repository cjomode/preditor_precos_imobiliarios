#!/bin/bash

sudo apt update -y
sudo apt upgrade -y

sudo apt install python3 python3-pip git -y

cd /home/ubuntu
git clone https://github.com/cjomode/preditor_precos_imobiliarios.git
cd preditor_precos_imobiliarios

pip3 install -r requirements.txt || pip3 install streamlit pandas plotly

nohup streamlit run app.py --server.port=8501 --server.enableCORS=false &
