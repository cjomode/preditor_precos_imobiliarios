import pandas as pd
import sqlite3


df = pd.read_csv('data/dados_banco_central.csv', sep=';')

print(df.head())      
print(df.columns)      


conn = sqlite3.connect('db/dados_banco_central.db')


df.to_sql('tabela_dados_banco_central', conn, if_exists='replace', index=False)

conn.close()