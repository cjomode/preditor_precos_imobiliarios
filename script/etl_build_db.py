import os
import sqlite3
from datetime import datetime
import pandas as pd

DATA_DIR = "data"
DB_DIR = "db"
DB_PATH = os.path.join(DB_DIR, "warehouse.db")

os.makedirs(DB_DIR, exist_ok=True)

# ---- mapeamentos/nomes de arquivos
CITIES = [
    "aracaju", "fortaleza", "joao_pessoa", "maceio", "natal",
    "recife", "salvador", "sao_luis", "teresina",
]

CITY_LABEL = {
    "aracaju": "Aracaju",
    "fortaleza": "Fortaleza",
    "joao_pessoa": "João Pessoa",
    "maceio": "Maceió",
    "natal": "Natal",
    "recife": "Recife",
    "salvador": "Salvador",
    "sao_luis": "São Luís",
    "teresina": "Teresina",
}

CSV_PATTERN = {
    "locacao": "dados_locacao_{city}_tratado.csv",
    "vendas":  "dados_vendas_{city}_tratados.csv",  # atenção ao 'tratados'
}

# normalização de nomes problemáticos
COL_RENAME = {
    "Preço médio (R$/m²) Total": "Preço médio (R$/m²)Total",
    "Preço médio (R$/m²)Total ": "Preço médio (R$/m²)Total",
    " Preço médio (R$/m²)Total": "Preço médio (R$/m²)Total",
}

# -------- helpers de conversão PT-BR
def to_float_br_series(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip()
    s = (s
         .str.replace("\u00A0", "", regex=False)  # NBSP
         .str.replace("R$", "", regex=False)
         .str.replace("%", "", regex=False)
         .str.replace("–", "-", regex=False)      # en dash
         .str.replace("—", "-", regex=False)      # em dash
         .str.replace(" ", "", regex=False))

    # se tem vírgula decimal no fim, remove pontos de milhar e troca vírgula por ponto
    has_comma_dec = s.str.contains(r",\d+$", na=False)
    s_conv = s.copy()
    s_conv[has_comma_dec] = (s_conv[has_comma_dec]
                             .str.replace(".", "", regex=False)
                             .str.replace(",", ".", regex=False))
    return pd.to_numeric(s_conv, errors="coerce")

def coerce_numeric_br(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    obj_cols = out.select_dtypes(include=["object"]).columns
    for c in obj_cols:
        subset = out[c].dropna()
        if subset.empty: 
            continue
        conv = to_float_br_series(subset)
        if conv.notna().mean() >= 0.6:
            out[c] = to_float_br_series(out[c])
    return out

# -------- carregadores
def load_city_csv(kind: str, city: str) -> pd.DataFrame | None:
    fname = CSV_PATTERN[kind].format(city=city)
    path = os.path.join(DATA_DIR, fname)
    if not os.path.exists(path):
        print(f"[WARN] Arquivo não encontrado: {path}")
        return None
    df = pd.read_csv(path, sep=";")
    df.rename(columns=COL_RENAME, inplace=True)
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df = df.dropna(subset=["Data"])
    df = coerce_numeric_br(df)
    df["Cidade"] = CITY_LABEL[city]
    df["UF"] = None  # opcional: preencha via dicionário se tiver
    df["TipoMercado"] = "Locação" if kind == "locacao" else "Venda"
    return df

def load_bcb_csv() -> pd.DataFrame | None:
    path = os.path.join(DATA_DIR, "dados_banco_central.csv")
    if not os.path.exists(path):
        print(f"[WARN] BCB CSV não encontrado: {path}")
        return None
    df = pd.read_csv(path, sep=";")
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df = df.dropna(subset=["Data"])
    # colunas numéricas típicas do BCB
    for c in ["Media", "Mediana", "DesvioPadrao", "Minimo", "Maximo"]:
        if c in df.columns:
            df[c] = to_float_br_series(df[c].astype(str))
    return df

# -------- persistência
def init_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bcb (
            Data TEXT,
            Indicador TEXT,
            Media REAL, Mediana REAL, DesvioPadrao REAL, Minimo REAL, Maximo REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS locacao (
            Data TEXT,
            Cidade TEXT,
            UF TEXT,
            TipoMercado TEXT,
            -- demais colunas ficam dinâmicas no to_sql; mas garantimos algumas comuns:
            "Preço médio (R$/m²)Total" REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            Data TEXT,
            Cidade TEXT,
            UF TEXT,
            TipoMercado TEXT,
            "Preço médio (R$/m²)Total" REAL
        )
    """)
    # índices úteis
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bcb ON bcb(Indicador, Data)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_locacao ON locacao(Cidade, Data)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vendas ON vendas(Cidade, Data)")
    conn.commit()

def write_replace(conn: sqlite3.Connection, table: str, df: pd.DataFrame):
    # converte datetime para ISO date (YYYY-MM-DD) para padronizar
    if "Data" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Data"]):
        df = df.copy()
        df["Data"] = df["Data"].dt.strftime("%Y-%m-%d")
    df.to_sql(table, conn, if_exists="replace", index=False)

def write_append(conn: sqlite3.Connection, table: str, df: pd.DataFrame):
    if "Data" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Data"]):
        df = df.copy()
        df["Data"] = df["Data"].dt.strftime("%Y-%m-%d")
    df.to_sql(table, conn, if_exists="append", index=False)

def run():
    print(">> Construindo banco SQLite a partir dos CSVs reais...")
    conn = sqlite3.connect(DB_PATH)
    init_schema(conn)

    # ---- BCB
    bcb = load_bcb_csv()
    if bcb is not None:
        print(f"   - BCB: {len(bcb)} linhas")
        write_replace(conn, "bcb", bcb)

    # ---- Locação / Vendas (tabelas LONGAS)
    long_locacao = []
    long_vendas = []

    for city in CITIES:
        df_l = load_city_csv("locacao", city)
        if df_l is not None and len(df_l):
            long_locacao.append(df_l)
            print(f"   - Locação/{CITY_LABEL[city]}: {len(df_l)}")
        df_v = load_city_csv("vendas", city)
        if df_v is not None and len(df_v):
            long_vendas.append(df_v)
            print(f"   - Vendas/{CITY_LABEL[city]}: {len(df_v)}")

    if long_locacao:
        loc = pd.concat(long_locacao, ignore_index=True, sort=False)
        write_replace(conn, "locacao", loc)
        print(f"   -> locacao (long): {len(loc)} linhas")
    if long_vendas:
        ven = pd.concat(long_vendas, ignore_index=True, sort=False)
        write_replace(conn, "vendas", ven)
        print(f"   -> vendas  (long): {len(ven)} linhas")

    # snapshot simples de controle
    meta = {
        "built_at": datetime.utcnow().isoformat() + "Z",
        "bcb_rows": 0 if bcb is None else int(len(bcb)),
        "loc_rows": int(sum(len(x) for x in long_locacao)) if long_locacao else 0,
        "ven_rows": int(sum(len(x) for x in long_vendas)) if long_vendas else 0,
    }
    pd.DataFrame([meta]).to_json(os.path.join(DB_DIR, "warehouse_meta.json"), orient="records", indent=2, force_ascii=False)
    conn.close()
    print(">> OK! Banco em:", DB_PATH)

if __name__ == "__main__":
    run()
