import joblib

# Carrega o arquivo
caminho = "modelos_finais_completos.joblib"
dados = joblib.load(caminho)

print("🔍 Chaves principais:", list(dados.keys()))  # ['locacao', 'venda']

for cat, sub in dados.items():
    print(f"\n📁 Categoria: {cat} → Subchaves:", list(sub.keys()))  # ['prophet', 'sarima']
    for modelo, cidades in sub.items():
        print(f"  🧠 Modelo: {modelo} → {len(cidades)} cidades")
        exemplo = list(cidades.keys())[0]
        print(f"     📍 Exemplo: {exemplo}")
        print(f"     🔑 Subchaves internas: {list(cidades[exemplo].keys())}")
