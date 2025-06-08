import pandas as pd
import sqlite3

df = pd.read_csv('data/dados_vendas_tratados.csv', sep=';')

print(df.head())      
print(df.columns)      


conn = sqlite3.connect('db/dados_locacao.db')

df.to_sql('tabela_dados_locacao', conn, index=False)

conn.close()