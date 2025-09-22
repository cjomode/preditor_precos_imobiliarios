# -*- coding: utf-8 -*-
"""
ETL enxuta para montar db/warehouse.db a partir de data/*.csv

• Procura CSVs na RAIZ do projeto (../data) – não em script/data
• Aceita singular/plural: tratado / tratados
• Normaliza colunas PT-BR (Data, R$, %, NBSP)
• Cria índices só se as tabelas existirem
• Logs claros do que entrou / faltou
"""

import os
import re
import glob
import sqlite3
from datetime import datetime
import pandas as pd

# ========= PATHS =========
HERE = os.path.dirname(os.path.abspath(__file__))      # .../script
ROOT = os.path.dirname(HERE)                           # .../
DATA_DIR = os.path.join(ROOT, "data")                  # .../data
DB_DIR = os.path.join(ROOT, "db")                      # .../db
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "warehouse.db")

# ========= CIDADES =========
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

# ========= RENAMES/FORMATAÇÃO =========
COL_RENAME = {
    "Preço médio (R$/m²) Total": "Preço médio (R$/m²)Total",
    "Preço médio (R$/m²)Total ": "Preço médio (R$/m²)Total",
    " Preço médio (R$/m²)Total": "Preço médio (R$/m²)Total",
    "Var. Mensal (%) Total": "Var. Mensal (%)Total",
    "Var. Mensal (%)Total ": "Var. Mensal (%)Total",
    " Var. Mensal (%)Total": "Var. Mensal (%)Total",
}

def to_float_br_series(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip()
    s = (s
         .str.replace("\u00A0", " ", regex=False)  # NBSP -> espaço
         .str.replace("R$", "", regex=False)
         .str.replace("%", "", regex=False)
         .str.replace("–", "-", regex=False)      # en dash
         .str.replace("—", "-", regex=False)      # em dash
         .str.replace(" ", "", regex=False))
    has_comma_dec = s.str.contains(r",\d+$", na=False)
    s2 = s.copy()
    s2[has_comma_dec] = (s2[has_comma_dec]
                         .str.replace(".", "", regex=False)
                         .str.replace(",", ".", regex=False))
    return pd.to_numeric(s2, errors="coerce")

def coerce_numeric_br(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.select_dtypes(include=["object"]).columns:
        conv = to_float_br_series(out[c])
        if conv.notna().mean() >= 0.6:
            out[c] = conv
    return out

def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = (pd.Series(df.columns)
            .astype(str)
            .str.replace("\u00A0", " ", regex=False)
            .str.replace(r"\s+", " ", regex=True)
            .str.replace(r"\(\s*%\s*\)", "(%)", regex=True)
            .str.replace(r"\s+Total\b", "Total", regex=True)
            .str.strip())
    df = df.copy()
    df.columns = cols
    df.rename(columns=COL_RENAME, inplace=True)
    return df

def _sql_key(name: str) -> str:
    return re.sub(r"[\s%()\-/\.\u00A0]+", "", str(name)).lower()

def _uniqify_columns(cols) -> list[str]:
    seen, out = {}, []
    for c in list(cols):
        base = str(c)
        if base in seen:
            seen[base] += 1
            out.append(f"{base}__{seen[base]}")
        else:
            seen[base] = 0
            out.append(base)
    return out

def _ensure_unique(df: pd.DataFrame) -> pd.DataFrame:
    idx = pd.Index(df.columns)
    if idx.has_duplicates:
        df = df.copy()
        df.columns = _uniqify_columns(idx)
        mask = ~pd.Index(df.columns).duplicated()
        if not mask.all():
            df = df.loc[:, mask].copy()
    return df

def _dedup_for_sql(df: pd.DataFrame) -> pd.DataFrame:
    seen, keep = set(), []
    for c in df.columns:
        k = _sql_key(c)
        if k in seen:
            keep.append(False)
        else:
            seen.add(k)
            keep.append(True)
    return df.loc[:, keep].copy()

def _prep_for_sql(df: pd.DataFrame) -> pd.DataFrame:
    df = _clean_columns(df)
    df = _ensure_unique(df)
    df = _dedup_for_sql(df)
    if "Data" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Data"]):
        df = df.copy()
        df["Data"] = df["Data"].dt.strftime("%Y-%m-%d")
    return df

# ========= DETECÇÃO FLEX DE ARQUIVOS =========
def _find_city_csv(kind: str, city: str) -> str | None:
    pats = [
        f"dados_{kind}_{city}_tratado.csv",
        f"dados_{kind}_{city}_tratados.csv",
    ]
    for p in pats:
        full = os.path.join(DATA_DIR, p)
        if os.path.exists(full):
            return full
    globs = glob.glob(os.path.join(DATA_DIR, f"dados_{kind}_{city}_tratad*.csv"))
    return globs[0] if globs else None

def _find_bcb_csv() -> str | None:
    for name in ["dados_banco_central.csv",
                 "dados_banco_central_tratado.csv",
                 "dados_banco_central_tratados.csv"]:
        p = os.path.join(DATA_DIR, name)
        if os.path.exists(p):
            return p
    return None

# ========= CARREGADORES =========
def load_city_csv(kind: str, city: str) -> pd.DataFrame | None:
    path = _find_city_csv(kind, city)
    if not path:
        print(f"[WARN] faltou: data/dados_{kind}_{city}_tratado(s).csv")
        return None
    df = pd.read_csv(path, sep=";")
    df = _clean_columns(df)
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df = df.dropna(subset=["Data"])
    df = coerce_numeric_br(df)
    df["Cidade"] = CITY_LABEL[city]
    df["UF"] = None
    df["TipoMercado"] = "Locação" if kind == "locacao" else "Venda"
    return df

def load_bcb_csv() -> pd.DataFrame | None:
    path = _find_bcb_csv()
    if not path:
        print("[WARN] BCB CSV não encontrado em data/")
        return None
    df = pd.read_csv(path, sep=";")
    df = _clean_columns(df)
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df = df.dropna(subset=["Data"])
    for c in ["Media", "Mediana", "DesvioPadrao", "Minimo", "Maximo"]:
        if c in df.columns:
            df[c] = to_float_br_series(df[c].astype(str))
    return df

# ========= ÍNDICES (só se tabela existir) =========
def create_indices(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    have = {r[0] for r in cur.fetchall()}
    if "bcb" in have:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_bcb ON bcb(Indicador, Data)")
    if "locacao" in have:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_locacao ON locacao(Cidade, Data)")
    if "vendas" in have:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_vendas ON vendas(Cidade, Data)")
    conn.commit()

# ========= RUN =========
def run():
    print(">> Construindo banco SQLite a partir dos CSVs...")
    if not os.path.isdir(DATA_DIR):
        print(f"[ERRO] Pasta de dados não existe: {DATA_DIR}")
        return

    conn = sqlite3.connect(DB_PATH)

    # --- BCB
    bcb = load_bcb_csv()
    if bcb is not None and len(bcb):
        bcb = _prep_for_sql(bcb)
        bcb.to_sql("bcb", conn, if_exists="replace", index=False)
        print(f"   - bcb: {len(bcb)} linhas")

    # --- Locação / Vendas
    long_loc, long_ven = [], []
    for city in CITIES:
        dfl = load_city_csv("locacao", city)
        if dfl is not None and len(dfl):
            long_loc.append(dfl)
            print(f"   - locacao/{CITY_LABEL[city]}: {len(dfl)}")
        dfv = load_city_csv("vendas", city)
        if dfv is not None and len(dfv):
            long_ven.append(dfv)
            print(f"   - vendas/{CITY_LABEL[city]}: {len(dfv)}")

    if long_loc:
        loc = _prep_for_sql(pd.concat(long_loc, ignore_index=True, sort=False))
        loc.to_sql("locacao", conn, if_exists="replace", index=False)
        print(f"   -> locacao (long): {len(loc)} linhas")

    if long_ven:
        ven = _prep_for_sql(pd.concat(long_ven, ignore_index=True, sort=False))
        ven.to_sql("vendas", conn, if_exists="replace", index=False)
        print(f"   -> vendas  (long): {len(ven)} linhas")

    # índices sempre depois dos replaces
    create_indices(conn)

    meta = {
        "built_at": datetime.utcnow().isoformat() + "Z",
        "bcb_rows": 0 if bcb is None else int(len(bcb)),
        "loc_rows": int(sum(len(x) for x in long_loc)) if long_loc else 0,
        "ven_rows": int(sum(len(x) for x in long_ven)) if long_ven else 0,
    }
    pd.DataFrame([meta]).to_json(
        os.path.join(DB_DIR, "warehouse_meta.json"),
        orient="records", indent=2, force_ascii=False
    )
    conn.close()
    print(">> OK! Banco em:", DB_PATH)

if __name__ == "__main__":
    run()
