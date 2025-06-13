import pandas as pd
import sqlite3

cidades = [
    'recife',
    'fortaleza'
    'maceio',
    'aracaju',
    'salvador',
    'sao_luis',
    'teresina',
    'joao_pessoa'
]

for cidade in cidades:
    nome_csv = f'data/dados_vendas_{cidade}_tratados.csv'
    nome_db = f'db/dados_vendas_{cidade}.db'

    df = pd.read_csv(nome_csv, sep=';')
 
    conn = sqlite3.connect(nome_db)
    df.to_sql('tabela_dados_vendas', conn, if_exists='replace', index=False)
    conn.close()



