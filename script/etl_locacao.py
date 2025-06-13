# import pandas as pd
# import sqlite3

# # df = pd.read_csv('data/dados_locacao_recife_tratado.csv', sep=';')
# # df = pd.read_csv('data/dados_locacao_fortaleza_tratado.csv', sep=';')
# # df = pd.read_csv('data/dados_locacao_natal_tratado.csv', sep=';')
# # df = pd.read_csv('data/dados_locacao_maceio_tratado.csv', sep=';')
# df = pd.read_csv('data/dados_locacao_aracaju_tratado.csv', sep=';')

# print(df.head())      
# print(df.columns)      


# conn = sqlite3.connect('db/dados_locacao_aracaju.db')

# df.to_sql('tabela_dados_locacao', conn, index=False)

# conn.close()

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
    nome_csv = f'data/dados_locacao_{cidade}_tratado.csv'
    nome_db = f'db/dados_locacao_{cidade}.db'

    df = pd.read_csv(nome_csv, sep=';')
 
    conn = sqlite3.connect(nome_db)
    df.to_sql('tabela_dados_locacao', conn, if_exists='replace', index=False)
    conn.close()