import pandas as pd
import sqlite3

df = pd.read_csv('Recife_Dados_imoveis.csv')

conn = sqlite3.connect('dados_recife.db')

df.to_sql('tabela_dados_recife', conn, index=False)