import os
import json
import sqlite3
from datetime import datetime
from typing import List, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ML
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import joblib

# ---------- CONFIG ----------
st.set_page_config(page_title="Preditor Imobiliário", layout="wide")
DB_PATH = "db/warehouse.db"
MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

# ---------- HELPERS: DB ----------
@st.cache_data(show_spinner=False)
def _sql(q: str, params: tuple | None = None) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(q, conn, params=params)

@st.cache_data(show_spinner=False)
def lista_cidades(tabela: str) -> list[str]:
    df = _sql(f"SELECT DISTINCT Cidade FROM {tabela} ORDER BY Cidade;")
    return df["Cidade"].dropna().tolist()

@st.cache_data(show_spinner=False)
def carregar_cidade(tabela: str, cidade: str) -> pd.DataFrame:
    df = _sql(f"SELECT * FROM {tabela} WHERE Cidade = ? ORDER BY Data;", (cidade,))
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df = df.dropna(subset=["Data"]).sort_values("Data")
    return df.reset_index(drop=True)

@st.cache_data(show_spinner=False)
def carregar_bcb_wide() -> pd.DataFrame:
    """Banco Central em wide (uma coluna por indicador, usando 'Media')."""
    bcb = _sql("SELECT * FROM bcb;")
    if bcb.empty:
        return bcb
    bcb["Data"] = pd.to_datetime(bcb["Data"], errors="coerce")
    for col in ["Media", "Mediana", "Minimo", "Maximo"]:
        if col in bcb.columns:
            bcb[col] = (
                bcb[col].astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            bcb[col] = pd.to_numeric(bcb[col], errors="coerce")
    wide = bcb.pivot_table(index="Data", columns="Indicador", values="Media", aggfunc="mean").reset_index()
    wide.columns = ["Data"] + [f"BCB_{c}" for c in wide.columns[1:]]
    return wide

# ---------- HELPERS: DADOS ----------
def _to_float_br_series(s: pd.Series) -> pd.Series:
    """Converte strings PT-BR (R$, vírgula decimal, etc.) em float."""
    s = s.astype(str).str.strip()
    s = (
        s.str.replace("\u00A0", "", regex=False)
         .str.replace("R$", "", regex=False)
         .str.replace("%", "", regex=False)
         .str.replace("–", "-", regex=False)
         .str.replace("—", "-", regex=False)
         .str.replace(" ", "", regex=False)
    )
    has_comma_dec = s.str.contains(r",\d+$", na=False)
    s2 = s.copy()
    s2[has_comma_dec] = s2[has_comma_dec].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s2, errors="coerce")

def _coerce_numeric_br(df: pd.DataFrame) -> pd.DataFrame:
    """Converte colunas object para float quando fizer sentido (heurística)."""
    df = df.copy()
    for c in df.select_dtypes(include=["object"]).columns:
        sample = _to_float_br_series(df[c])
        if sample.notna().mean() >= 0.6:
            df[c] = _to_float_br_series(df[c])
    return df

def _expandir_tempo(df: pd.DataFrame) -> pd.DataFrame:
    if "Data" in df.columns:
        dt = pd.to_datetime(df["Data"], errors="coerce")
        df["Ano"] = dt.dt.year
        df["Mes"] = dt.dt.month
        df["Trimestre"] = dt.dt.quarter
    return df

def _drop_datetime_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Remove QUALQUER coluna datetime do conjunto de features (mantemos no df para gráficos)."""
    dt_cols = [c for c in df.columns if np.issubdtype(df[c].dtype, np.datetime64)]
    return df.drop(columns=dt_cols) if dt_cols else df

# ---------- ML CORE ----------
def _inferir_colunas(df: pd.DataFrame, target: str) -> Tuple[List[str], List[str]]:
    X = df.drop(columns=[target])
    X = _drop_datetime_cols(X)  # << não deixa datetime virar feature
    cat_cols = [c for c in X.columns if X[c].dtype == "object" or str(X[c].dtype).startswith("category")]
    num_cols = [c for c in X.columns if c not in cat_cols]
    return num_cols, cat_cols

def _preprocessador(num_cols: List[str], cat_cols: List[str]) -> ColumnTransformer:
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler(with_mean=True)),  # saída densa
    ])
    try:
        categorical = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])
    except TypeError:
        categorical = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("ohe", OneHotEncoder(handle_unknown="ignore", sparse=False)),
        ])
    return ColumnTransformer(
        transformers=[("num", numeric, num_cols), ("cat", categorical, cat_cols)],
        remainder="drop",
        sparse_threshold=0.0,  # força denso e evita bugs entre versões
    )

def _modelo(nome: str):
    nome = (nome or "rf").lower()
    if nome in ("rf", "randomforest", "random_forest"):
        return RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=-1)
    if nome in ("linreg", "linear", "elasticnet"):
        return ElasticNet(alpha=0.0001, l1_ratio=0.05, random_state=42)
    raise ValueError("Modelo não suportado. Use: rf | linreg")

def _avaliar(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = float(np.sqrt(mse))
    r2 = r2_score(y_true, y_pred)
    with np.errstate(divide="ignore", invalid="ignore"):
        mape = np.mean(np.abs((y_true - y_pred) / np.clip(np.abs(y_true), 1e-8, None)))
    return {"MAE": float(mae), "RMSE": float(rmse), "R2": float(r2), "MAPE": float(mape)}

def _slug(txt: str) -> str:
    return (txt.lower()
            .replace(" ", "_").replace("ã","a").replace("á","a").replace("â","a").replace("à","a")
            .replace("é","e").replace("ê","e").replace("í","i")
            .replace("ó","o").replace("ô","o").replace("õ","o")
            .replace("ú","u").replace("ü","u").replace("ç","c"))

def _paths(tipo: str, cidade: str) -> dict:
    d = os.path.join(MODELS_DIR, _slug(tipo), _slug(cidade))
    os.makedirs(d, exist_ok=True)
    return {
        "dir": d,
        "model": os.path.join(d, "model.pkl"),
        "preproc": os.path.join(d, "preprocessor.pkl"),
        "feature_info": os.path.join(d, "feature_info.json"),
        "metrics": os.path.join(d, "metrics.json"),
        "eval": os.path.join(d, "eval.csv"),
        "meta": os.path.join(d, "meta.json"),
        "snapshot": os.path.join(d, "train_snapshot.csv"),
    }

def _treinar(df: pd.DataFrame, alvo: str, nome_modelo: str, out: dict) -> tuple[dict, pd.DataFrame, Pipeline, pd.DataFrame]:
    df = df.copy()
    if alvo not in df.columns:
        raise ValueError(f"Coluna alvo '{alvo}' não encontrada. Disponíveis: {list(df.columns)}")

    # alvo numérico (PT-BR)
    df[alvo] = _to_float_br_series(df[alvo]) if df[alvo].dtype == "object" else pd.to_numeric(df[alvo], errors="coerce")
    df = df[np.isfinite(df[alvo])]

    # features
    df = _coerce_numeric_br(df)
    df = _expandir_tempo(df)

    n = len(df)
    if n < 3:
        raise ValueError(f"Poucos dados após limpeza (n={n}). Precisa de ≥3 linhas.")

    # split seguro
    test_size = 0.2 if n >= 10 else 0.33
    test_size = min(max(test_size, 1.0 / n + 1e-9), (n - 1) / n - 1e-9)

    num_cols, cat_cols = _inferir_colunas(df, alvo)
    X = df.drop(columns=[alvo])
    X = _drop_datetime_cols(X).replace([np.inf, -np.inf], np.nan)  # <<< datetime fora!
    y = df[alvo].astype(float)

    strat = None
    try:
        if y.nunique(dropna=True) > 2 and n >= 50:
            y_bins = pd.qcut(y, q=min(10, max(2, n // 50)), duplicates="drop", labels=False)
            if y_bins.nunique() > 1:
                strat = y_bins
    except Exception:
        strat = None

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=test_size, random_state=42, stratify=strat)

    pre = _preprocessador(num_cols, cat_cols)
    mdl = _modelo(nome_modelo)
    pipe = Pipeline([("pre", pre), ("model", mdl)])
    pipe.fit(X_tr, y_tr)

    pred = pipe.predict(X_te)
    metrics = _avaliar(y_te.values, pred)

    # salvar artefatos
    joblib.dump(pipe, out["model"])
    joblib.dump(pre, out["preproc"])
    json.dump({"numeric": num_cols, "categorical": cat_cols, "columns": list(X.columns)},
              open(out["feature_info"], "w"), ensure_ascii=False, indent=2)
    json.dump(metrics, open(out["metrics"], "w"), ensure_ascii=False, indent=2)

    eval_df = pd.DataFrame({"Real": y_te.values, "Previsto": pred})
    if "Data" in df.columns:
        try:
            eval_df["Data"] = df.iloc[y_te.index]["Data"].values
        except Exception:
            pass
    eval_df["Residuo"] = eval_df["Previsto"] - eval_df["Real"]
    eval_df.to_csv(out["eval"], index=False, sep=";")

    try:
        df.to_csv(out["snapshot"], index=False, sep=";")
    except Exception:
        pass

    json.dump({"trained_at": datetime.utcnow().isoformat() + "Z", "rows_used": int(len(df)), "model": nome_modelo},
              open(out["meta"], "w"), indent=2)

    return metrics, eval_df, pipe, df

def _carregar_avaliacao(paths: dict) -> tuple[dict | None, pd.DataFrame | None]:
    if os.path.exists(paths["metrics"]) and os.path.exists(paths["eval"]):
        metrics = json.load(open(paths["metrics"], "r", encoding="utf-8"))
        try:
            eval_df = pd.read_csv(paths["eval"], sep=";", parse_dates=["Data"])
        except Exception:
            eval_df = pd.read_csv(paths["eval"], sep=";")
        return metrics, eval_df
    return None, None

def _mostrar_avaliacao(metrics: dict, eval_df: pd.DataFrame, pipe: Pipeline | None):
    col1, col2 = st.columns([1, 1])
    with col1:
        met_barras = pd.DataFrame(
            {"Métrica": ["MAE", "RMSE", "MAPE (%)"], "Valor": [metrics["MAE"], metrics["RMSE"], metrics["MAPE"] * 100]}
        )
        fig_barras = px.bar(met_barras, x="Métrica", y="Valor", text="Valor", title="Erros (quanto menor, melhor)")
        fig_barras.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_barras.update_layout(yaxis_title="")
        st.plotly_chart(fig_barras, use_container_width=True)
    with col2:
        fig_r2 = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=max(0.0, min(1.0, float(metrics["R2"]))),
                gauge={
                    "axis": {"range": [0, 1]},
                    "bar": {"color": "#2ecc71"},
                    "steps": [
                        {"range": [0, 0.33], "color": "#ffe5e5"},
                        {"range": [0.33, 0.66], "color": "#fff4cc"},
                        {"range": [0.66, 1.0], "color": "#e5ffe5"},
                    ],
                },
                title={"text": "R²"},
            )
        )
        st.plotly_chart(fig_r2, use_container_width=True)

    fig_sc = px.scatter(eval_df, x="Real", y="Previsto", title="Real vs Previsto", labels={"Real": "Real", "Previsto": "Previsto"})
    if not eval_df[["Real", "Previsto"]].empty:
        mn = float(np.nanmin([eval_df["Real"].min(), eval_df["Previsto"].min()]))
        mx = float(np.nanmax([eval_df["Real"].max(), eval_df["Previsto"].max()]))
        fig_sc.add_shape(type="line", x0=mn, x1=mx, y0=mn, y1=mx, line=dict(dash="dash"))
    st.plotly_chart(fig_sc, use_container_width=True)

    fig_hist = px.histogram(eval_df["Residuo"], nbins=40, title="Resíduos (Previsto - Real)")
    fig_hist.update_layout(xaxis_title="Resíduo", yaxis_title="Frequência")
    st.plotly_chart(fig_hist, use_container_width=True)

    try:
        if pipe is not None and hasattr(pipe.named_steps["model"], "feature_importances_"):
            names = pipe.named_steps["pre"].get_feature_names_out()
            imp = pipe.named_steps["model"].feature_importances_
            imp_df = pd.DataFrame({"feature": names, "importance": imp}).sort_values("importance", ascending=False).head(20)
            fig_imp = px.bar(imp_df, x="importance", y="feature", orientation="h", title="Top 20 Features")
            fig_imp.update_layout(xaxis_title="Importância", yaxis_title="")
            st.plotly_chart(fig_imp, use_container_width=True)
    except Exception as e:
        st.caption(f"ℹ️ Importância indisponível: {e}")

# ---------- APP ----------
def main():
    st.title("🏠 Dashboard de Preços de Imóveis")

    painel = st.sidebar.selectbox("Escolha o painel", ["Mercado Imobiliário", "Indicadores Econômicos"])

    if painel == "Mercado Imobiliário":
        tipo_map = {"Locação": "locacao", "Venda": "vendas"}
        tipo_label = st.sidebar.selectbox("Tipo de mercado", list(tipo_map.keys()))
        tabela = tipo_map[tipo_label]

        cidades = lista_cidades(tabela)
        if not cidades:
            st.error("Nenhuma cidade encontrada. Rode a ETL primeiro.")
            st.stop()
        cidade = st.sidebar.selectbox("Cidade", cidades)

        df = carregar_cidade(tabela, cidade)
        if df.empty:
            st.warning("Sem dados para esta cidade.")
            st.stop()

        df_num = df.select_dtypes(include=[np.number])
        metricas = [c for c in df_num.columns if c.lower() not in {"ano", "mes", "trimestre"}]
        default_metrica = "Preço médio (R$/m²)Total" if "Preço médio (R$/m²)Total" in df.columns else (metricas[0] if metricas else None)
        metrica = (
            st.sidebar.selectbox("Métrica", [default_metrica] + [m for m in metricas if m != default_metrica])
            if default_metrica else st.sidebar.selectbox("Métrica", metricas)
        )

        usar_bcb = st.sidebar.checkbox("Cruzar com indicadores do Banco Central (BCB)", value=True)
        if usar_bcb:
            bcb_w = carregar_bcb_wide()
            if not bcb_w.empty:
                df = df.merge(bcb_w, on="Data", how="left")

        if metrica and metrica in df.columns:
            fig = px.line(df, x="Data", y=metrica, title=f"{tipo_label} • {cidade} • {metrica}", markers=True)
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("Ver dados brutos"):
            st.dataframe(df)

        with st.expander("🧠 Modelo preditivo"):
            alvo = st.text_input("Coluna alvo (para prever)", value=metrica or default_metrica or df.columns[-1])
            nome_modelo = st.selectbox("Modelo", ["rf", "linreg"], index=0, key=f"mdl_{tabela}_{cidade}")
            paths = _paths(tabela, cidade)

            precisa_treinar = (not os.path.exists(paths["model"]))
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("🔁 Atualizar modelo agora"):
                    precisa_treinar = True
            with c2:
                st.caption("Se não houver modelo, treinamos automaticamente.")

            metrics, eval_df = _carregar_avaliacao(paths)
            pipe = None

            if precisa_treinar or metrics is None or eval_df is None:
                try:
                    with st.spinner("Treinando/atualizando modelo com os dados REAIS desta cidade..."):
                        metrics, eval_df, pipe, df_used = _treinar(df, alvo, nome_modelo, paths)
                    st.success("✅ Modelo treinado/atualizado.")
                    st.caption(f"Linhas usadas no treino: **{len(df_used)}** (snapshot em `{paths['snapshot']}`)")
                    with st.expander("👀 Amostra do dataset usado"):
                        st.dataframe(df_used.head(10))
                except Exception as e:
                    st.error(f"Erro no treinamento: {e}")
                    st.stop()
            else:
                try:
                    pipe = joblib.load(paths["model"])
                except Exception:
                    pipe = None
                st.info("ℹ️ Usando modelo salvo. Clique em **Atualizar modelo agora** se quiser retreinar.")

            _mostrar_avaliacao(metrics, eval_df, pipe)

            with st.expander("📁 Artefatos salvos"):
                st.json(paths)

    elif painel == "Indicadores Econômicos":
        bcb = carregar_bcb_wide()
        if bcb.empty:
            st.warning("Sem dados do BCB na base. Rode a ETL.")
            st.stop()
        cols = [c for c in bcb.columns if c != "Data"]
        serie = st.sidebar.selectbox("Indicador (Media)", cols)
        fig = px.line(bcb, x="Data", y=serie, title=f"BCB • {serie}", markers=True)
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Ver dados brutos"):
            st.dataframe(bcb)

if __name__ == "__main__":
    main()
