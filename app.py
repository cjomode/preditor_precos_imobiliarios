# -*- coding: utf-8 -*-
# app.py — RF01, RF02, RF03 + RNFs (versão “à prova de susto”)
import os
import sqlite3
from datetime import date, datetime
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ML
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.tree import DecisionTreeRegressor
from sklearn.linear_model import LinearRegression

# ----------------- CONFIG -----------------
st.set_page_config(page_title="Preditor Imobiliário", layout="wide")

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "db", "warehouse.db")   # produzido pela ETL
PREC_COL = 'Preço médio (R$/m²)Total'                 # métrica-alvo padrão

# ----------------- DB HELPERS -----------------
def _connect() -> sqlite3.Connection:
    """Conexão confiável (RNF02)."""
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    with conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
    return conn

@st.cache_data(show_spinner=False, ttl=300)
def _sql(q: str, params: tuple | None = None) -> pd.DataFrame:
    with _connect() as conn:
        return pd.read_sql_query(q, conn, params=params)

def _exec(q: str, params: tuple = ()) -> None:
    with _connect() as conn:
        conn.execute("BEGIN")
        conn.execute(q, params)
        conn.commit()

def _exec_many(q: str, rows: list[tuple]) -> None:
    with _connect() as conn:
        conn.execute("BEGIN")
        conn.executemany(q, rows)
        conn.commit()

@st.cache_data(show_spinner=False)
def _lista_cidades(tabela: str) -> List[str]:
    df = _sql(f"SELECT DISTINCT Cidade FROM {tabela} ORDER BY Cidade;")
    return df["Cidade"].dropna().tolist()

@st.cache_data(show_spinner=False)
def _carregar_cidade(tabela: str, cidade: str) -> pd.DataFrame:
    df = _sql(f"SELECT * FROM {tabela} WHERE Cidade = ? ORDER BY Data;", (cidade,))
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df = df.dropna(subset=["Data"]).sort_values("Data")
    return df.reset_index(drop=True)

def _cols_tabela(tabela: str) -> List[str]:
    with _connect() as conn:
        cur = conn.execute(f'PRAGMA table_info("{tabela}");')
        return [r[1] for r in cur.fetchall()]

# ----------------- VALIDAÇÃO (RNF03) -----------------
def _num_ok(x: float) -> bool:
    return x is not None and np.isfinite(x) and x > 0

def _date_ok(s: str) -> bool:
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except Exception:
        return False

# ----------------- HELPERS RF01 (lote/tempo) -----------------
def _date_range_months(start: str, end: str) -> list[str]:
    """Primeiro dia de cada mês entre start e end (YYYY-MM-DD)."""
    s = pd.to_datetime(start, errors="coerce")
    e = pd.to_datetime(end, errors="coerce")
    if pd.isna(s) or pd.isna(e) or s > e:
        return []
    rng = pd.date_range(s, e, freq="MS")
    return [d.strftime("%Y-%m-%d") for d in rng]

def _last_price_or(df: pd.DataFrame, default: float = 0.0) -> float:
    col = PREC_COL if PREC_COL in df.columns else None
    if col and len(df):
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(s):
            return float(s.iloc[-1])
    return float(default)

# ----------------- RF01: CAPTURA/ARMAZENAMENTO -----------------
def painel_captura():
    st.subheader("🧾 Captura de dados (RF01)")
    st.caption("Salva no SQLite — modo único ou em lote por período.")

    tipo_map = {"Locação": "locacao", "Venda": "vendas"}
    tipo_label = st.selectbox("Tipo de mercado", list(tipo_map.keys()))
    tabela = tipo_map[tipo_label]

    cidades = _lista_cidades(tabela) or _lista_cidades("locacao") or _lista_cidades("vendas")
    if not cidades:
        st.error("Nenhuma cidade encontrada. Rode a ETL primeiro.")
        return
    cidade = st.selectbox("Cidade", cidades)

    cols = _cols_tabela(tabela)
    col_ok = PREC_COL in cols
    if not col_ok:
        st.warning(f"Atenção: coluna '{PREC_COL}' não existe em {tabela}. O registro terá apenas metadados.")

    modo = st.radio("Modo de captura", ["Único", "Lote (período)"], horizontal=True)

    if modo == "Único":
        data_str = st.date_input("Data (AAAA-MM-DD)", value=date.today()).strftime("%Y-%m-%d")
        preco = st.number_input(f"{PREC_COL}", min_value=0.0, step=0.1, format="%.2f",
                                value=_last_price_or(_carregar_cidade(tabela, cidade), 0.0))
        st.info("Validações: data válida, preço > 0 e cidade definida. (RNF03)")

        if st.button("💾 Salvar registro"):
            if not _date_ok(data_str):
                st.error("Data inválida.")
                return
            if col_ok and not _num_ok(preco):
                st.error("Preço deve ser maior que zero.")
                return

            payload = {"Data": data_str, "Cidade": cidade, "UF": None, "TipoMercado": tipo_label}
            if col_ok:
                payload[PREC_COL] = float(preco)

            use_cols = [c for c in payload if c in cols]
            placeholders = ",".join(["?"] * len(use_cols))
            quoted_cols = ",".join([f'"{c}"' for c in use_cols])
            params = tuple(payload[c] for c in use_cols)

            _exec(f'INSERT INTO {tabela} ({quoted_cols}) VALUES ({placeholders});', params)
            st.success(f"1 registro inserido em **{tabela}** para **{cidade}** em **{data_str}**.")
            _lista_cidades.clear(); _carregar_cidade.clear(); _sql.clear()

    else:
        c1, c2 = st.columns(2)
        with c1:
            inicio = st.date_input("Início (mês incluso)", value=pd.Timestamp("2022-01-01")).strftime("%Y-%m-%d")
        with c2:
            fim = st.date_input("Fim (mês incluso)", value=pd.Timestamp("2025-08-01")).strftime("%Y-%m-%d")

        base = _last_price_or(_carregar_cidade(tabela, cidade), 0.0)
        preco_base = st.number_input(f"Valor base para {PREC_COL}", min_value=0.0, step=0.1, format="%.2f", value=base)
        ramp = st.checkbox("Aplicar rampa (crescimento linear no período)?", value=False)
        delta_total = st.number_input("Variação total no período (ex.: +2.50)", value=0.00, step=0.10, format="%.2f") if ramp else 0.0

        datas = _date_range_months(inicio, fim)
        st.caption(f"Período gerará **{len(datas)}** linhas (1ª de cada mês).")

        if st.button("💾 Salvar lote de registros"):
            if not datas:
                st.error("Período inválido.")
                return
            if col_ok and not _num_ok(preco_base):
                st.error("Preço base deve ser maior que zero.")
                return

            valores = []
            for i, _d in enumerate(datas):
                v = float(preco_base)
                if ramp and len(datas) > 1:
                    v += (delta_total * (i / (len(datas) - 1)))
                valores.append(v)

            base_cols = ["Data", "Cidade", "UF", "TipoMercado"]
            use_cols = [c for c in base_cols + ([PREC_COL] if col_ok else []) if c in cols]
            quoted_cols = ",".join([f'"{c}"' for c in use_cols])
            placeholders = ",".join(["?"] * len(use_cols))

            rows = []
            for d, v in zip(datas, valores):
                payload = {"Data": d, "Cidade": cidade, "UF": None, "TipoMercado": tipo_label}
                if col_ok:
                    payload[PREC_COL] = float(v)
                rows.append(tuple(payload[c] for c in use_cols))

            # política: não duplica — apaga o range & reinsere
            with _connect() as conn:
                conn.execute("BEGIN")
                conn.execute(f'DELETE FROM {tabela} WHERE Cidade = ? AND Data BETWEEN ? AND ?;', (cidade, inicio, fim))
                conn.executemany(f'INSERT INTO {tabela} ({quoted_cols}) VALUES ({placeholders});', rows)
                conn.commit()

            st.success(f"{len(rows)} registros inseridos em **{tabela}** para **{cidade}** ({inicio} → {fim}).")
            _lista_cidades.clear(); _carregar_cidade.clear(); _sql.clear()

# ----------------- RF02: DASHBOARD -----------------
def painel_dashboard():
    st.subheader("📊 Dashboard inicial (RF02)")
    tipo_map = {"Locação": "locacao", "Venda": "vendas"}
    tipo_label = st.sidebar.selectbox("Tipo de mercado", list(tipo_map.keys()), key="dash_tipo")
    tabela = tipo_map[tipo_label]

    cidades = _lista_cidades(tabela)
    if not cidades:
        st.error("Nenhuma cidade encontrada. Rode a ETL.")
        return
    cidade = st.sidebar.selectbox("Cidade", cidades, key="dash_cidade")

    df = _carregar_cidade(tabela, cidade)
    if df.empty:
        st.warning("Sem dados para esta cidade.")
        return

    # Filtro de período
    if "Data" in df.columns:
        data_min, data_max = df["Data"].min(), df["Data"].max()
        d_ini, d_fim = st.sidebar.date_input(
            "Período",
            value=(data_min.to_pydatetime().date(), data_max.to_pydatetime().date())
        )
        if d_ini and d_fim:
            df = df[(df["Data"] >= pd.to_datetime(d_ini)) & (df["Data"] <= pd.to_datetime(d_fim))]

    num_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in {"Ano", "Mes", "Trimestre"}]
    default = PREC_COL if PREC_COL in df.columns else (num_cols[0] if num_cols else None)
    if not default:
        st.warning("Nenhuma métrica numérica encontrada.")
        return

    metrica = st.sidebar.selectbox("Métrica", [default] + [c for c in num_cols if c != default], key="dash_metrica")
    fig = px.line(df, x="Data", y=metrica, title=f"{tipo_label} • {cidade} • {metrica}", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ver dados brutos"):
        st.dataframe(df)

# ----------------- RF03: MODELO -----------------
def _avaliar(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = r2_score(y_true, y_pred)
    return {"MAE": float(mae), "RMSE": float(rmse), "R2": float(r2)}

def _prep_features_for_model(df: pd.DataFrame, alvo: str) -> pd.DataFrame:
    """Cria Ano/Mes/Trimestre, mantém só numéricas, elimina NaN/inf."""
    df = df.copy()
    if "Data" in df.columns:
        dt = pd.to_datetime(df["Data"], errors="coerce")
        df["Ano"] = dt.dt.year
        df["Mes"] = dt.dt.month
        df["Trimestre"] = dt.dt.quarter

    if df[alvo].dtype == "object":
        df[alvo] = pd.to_numeric(df[alvo], errors="coerce")

    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if alvo not in num_cols:
        return pd.DataFrame()

    keep = [c for c in num_cols if c != alvo]
    X = df[keep].replace([np.inf, -np.inf], np.nan).dropna()
    y = df.loc[X.index, alvo].astype(float)

    mask = y.notna()
    X, y = X.loc[mask], y.loc[mask]

    if X.shape[1] == 0 or len(X) < 10:
        return pd.DataFrame()

    X[alvo] = y
    return X

def painel_modelo():
    st.subheader("🧠 Modelo preditivo (RF03)")
    st.caption("Árvore de Decisão (exercício) ou Regressão Linear — com features numéricas e filtro de período.")

    tipo_map = {"Locação": "locacao", "Venda": "vendas"}
    tipo_label = st.selectbox("Tipo de mercado", list(tipo_map.keys()), key="mdl_tipo")
    tabela = tipo_map[tipo_label]

    cidades = _lista_cidades(tabela)
    if not cidades:
        st.error("Nenhuma cidade encontrada.")
        return
    cidade = st.selectbox("Cidade", cidades, key="mdl_cidade")

    df = _carregar_cidade(tabela, cidade)
    if df.empty:
        st.warning("Sem dados.")
        return

    # Filtro de período de treino
    if "Data" in df.columns:
        data_min, data_max = df["Data"].min(), df["Data"].max()
        d_ini, d_fim = st.date_input(
            "Período do treino",
            value=(data_min.to_pydatetime().date(), data_max.to_pydatetime().date())
        )
        if d_ini and d_fim:
            df = df[(df["Data"] >= pd.to_datetime(d_ini)) & (df["Data"] <= pd.to_datetime(d_fim))]

    alvo_default = PREC_COL if PREC_COL in df.columns else df.select_dtypes(include=[np.number]).columns[-1]
    alvo = st.selectbox("Coluna alvo", [alvo_default] + [c for c in df.select_dtypes(include=[np.number]).columns if c != alvo_default])

    data_num = _prep_features_for_model(df, alvo)
    if data_num.empty:
        st.error("Dados insuficientes para treinar (≥10 linhas e ≥1 feature numérica além do alvo).")
        return

    X = data_num.drop(columns=[alvo])
    y = data_num[alvo].astype(float)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    modelo_nome = st.radio("Modelo", ["Árvore de Decisão (exercício)", "Regressão Linear"], horizontal=True)
    mdl = DecisionTreeRegressor(random_state=42, max_depth=5) if modelo_nome.startswith("Árvore") else LinearRegression()

    mdl.fit(X_tr, y_tr)
    pred = mdl.predict(X_te)

    metrics = _avaliar(y_te.values, pred)
    c1, c2, c3 = st.columns(3)
    c1.metric("MAE", f"{metrics['MAE']:.2f}")
    c2.metric("RMSE", f"{metrics['RMSE']:.2f}")
    c3.metric("R²", f"{metrics['R2']:.3f}")

    if metrics["R2"] >= 0.5:
        st.success("Modelo pré-validado para consulta (R² ≥ 0,5).")
    else:
        st.warning("Modelo com baixo R² — tente outra cidade/período/feature.")

    eval_df = pd.DataFrame({"Real": y_te.values, "Previsto": pred})
    # Fallback: trendline só se statsmodels estiver instalado
    try:
        fig_sc = px.scatter(eval_df, x="Real", y="Previsto", title="Real vs Previsto", trendline="ols")
    except Exception:
        fig_sc = px.scatter(eval_df, x="Real", y="Previsto", title="Real vs Previsto")
    st.plotly_chart(fig_sc, use_container_width=True)

    st.plotly_chart(px.histogram(eval_df["Previsto"] - eval_df["Real"], nbins=30, title="Resíduos (Previsto - Real)"),
                    use_container_width=True)

# ----------------- LAYOUT -----------------
def main():
    st.title("🏠 Preditor Imobiliário")
    st.caption("Atende RF01, RF02, RF03 + RNF01..RNF04. Base: db/warehouse.db (ETL).")

    painel = st.sidebar.radio("Painel", ["Captura (RF01)", "Dashboard (RF02)", "Modelo (RF03)"], index=1)
    if painel.startswith("Captura"):
        painel_captura()
    elif painel.startswith("Dashboard"):
        painel_dashboard()
    else:
        painel_modelo()

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        st.error(f"Banco não encontrado em {DB_PATH}. Rode a ETL primeiro.")
    else:
        main()
