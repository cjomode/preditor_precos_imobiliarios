# app.py — RF01, RF02, RF03 + RNFs (Prophet, ARIMA, RandomForest e XGBoost)

import os
import sqlite3
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

st.set_page_config(page_title="Preditor Imobiliário", layout="wide")

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "db", "warehouse.db")
MODEL_PATH = os.path.join(HERE, "all_models.joblib")
PREC_COL = 'Preço médio (R$/m²)Total'

# ----------------- DB HELPERS -----------------
def _connect() -> sqlite3.Connection:
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

# ----------------- RF01 -----------------
def painel_captura():
    st.subheader("🧾 Captura de dados (RF01)")
    st.caption("Salva no SQLite — modo único ou em lote por período.")

# ----------------- RF02 -----------------
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

    if "Data" in df.columns:
        data_min, data_max = df["Data"].min(), df["Data"].max()
        d_ini, d_fim = st.sidebar.date_input(
            "Período",
            value=(data_min.to_pydatetime().date(), data_max.to_pydatetime().date())
        )
        if d_ini and d_fim:
            df = df[(df["Data"] >= pd.to_datetime(d_ini)) & (df["Data"] <= pd.to_datetime(d_fim))]

    metrica = PREC_COL if PREC_COL in df.columns else df.select_dtypes(include=[np.number]).columns[0]
    fig = px.line(df, x="Data", y=metrica, title=f"{tipo_label} • {cidade} • {metrica}", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ver dados brutos"):
        st.dataframe(df)

# ----------------- RF03 -----------------
def _avaliar(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = r2_score(y_true, y_pred)
    return {"MAE": float(mae), "RMSE": float(rmse), "R2": float(r2)}

def painel_modelo():
    st.subheader("🧠 Modelo preditivo (RF03)")
    st.caption("Usa automaticamente all_models.joblib para prever séries por cidade.")

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

    alvo = PREC_COL if PREC_COL in df.columns else df.select_dtypes(include=[np.number]).columns[-1]

    if not os.path.exists(MODEL_PATH):
        st.error(f"Nenhum modelo encontrado em {MODEL_PATH}.")
        return

    try:
        modelos = joblib.load(MODEL_PATH)
    except Exception as e:
        st.error(f"Erro ao carregar modelos: {e}")
        return

    chave = f"{tabela}_{cidade.lower()}"
    if chave not in modelos:
        st.error(f"Não há modelo treinado para {chave} no all_models.joblib.")
        return

    entry = modelos[chave]

    if isinstance(entry, dict):
        modelo_opcoes = [k for k in entry.keys() if k in ["prophet_model", "arima_model", "rf_model", "xgb_model"]]
        if not modelo_opcoes:
            st.error("Nenhum dos modelos suportados (Prophet, ARIMA, RF, XGBoost) encontrado.")
            return
        escolha = st.selectbox("Escolha o modelo salvo:", modelo_opcoes)
        modelo = entry[escolha]
    else:
        modelo = entry
        escolha = "rf_model"

    df = df.dropna(subset=[alvo]).copy()

    hist_df = entry.get("historical_df", pd.DataFrame()).copy()
    if not hist_df.empty and "Data" in hist_df.columns:
        df_merged = pd.merge(df, hist_df.drop(columns=[PREC_COL], errors="ignore"),
                             on="Data", how="left")
    else:
        df_merged = df.copy()

    prever_futuro = st.checkbox("🔮 Prever até 2027", value=False)
    last_date = df["Data"].max()
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1),
                                 end="2027-12-01", freq="MS")

    try:
        # --------- Parte 1: Histórico ----------
        if escolha == "prophet_model":
            regressors = [c for c in hist_df.columns if c not in ["y", "ds"]]
            future_df = pd.DataFrame({"ds": df_merged["Data"]})
            for r in regressors:
                future_df[r] = df_merged[r].fillna(method="ffill").fillna(0).values if r in df_merged else 0
            forecast = modelo.predict(future_df)
            df_hist = df.copy()
            df_hist["Previsto"] = forecast["yhat"].values

        elif escolha == "arima_model":
            diff = entry.get("arima_diff", 0)
            last_val = entry.get("arima_last_val", None)
            forecast = modelo.forecast(steps=len(df_merged))
            if diff and last_val is not None:
                forecast = np.r_[last_val, forecast].cumsum()[1:]
            df_hist = df.copy()
            df_hist["Previsto"] = np.array(forecast)

        elif escolha in ["rf_model", "xgb_model"]:
            features = entry.get("rf_features" if escolha=="rf_model" else "xgb_features", [])
            imputer = entry.get("rf_imputer" if escolha=="rf_model" else "xgb_imputer", None)
            scaler = entry.get("rf_scaler" if escolha=="rf_model" else "xgb_scaler", None)
            for f in features:
                if f not in df_merged.columns: df_merged[f] = 0
            X = df_merged[features].fillna(0)
            if imputer: X = imputer.transform(X)
            if scaler: X = scaler.transform(X)
            df_hist = df.copy()
            df_hist["Previsto"] = modelo.predict(X)

        # --------- Parte 2: Futuro (opcional) ----------
        df_future = pd.DataFrame()
        if prever_futuro:
            if escolha == "prophet_model":
                extra_future = modelo.make_future_dataframe(periods=len(future_dates), freq="MS")
                for r in regressors: extra_future[r] = 0
                forecast_future = modelo.predict(extra_future)
                df_future = forecast_future[["ds", "yhat"]].rename(columns={"ds": "Data", "yhat": "Previsto"})
                df_future = df_future[df_future["Data"] > df["Data"].max()]

            elif escolha == "arima_model":
                future_forecast = modelo.forecast(steps=len(future_dates))
                if diff and last_val is not None:
                    future_forecast = np.r_[last_val, future_forecast].cumsum()[1:]
                df_future = pd.DataFrame({"Data": future_dates, "Previsto": future_forecast})

            else:  # RF e XGB
                df_future = pd.DataFrame({"Data": future_dates})
                for f in features: df_future[f] = 0
                X_future = df_future[features]
                if imputer: X_future = imputer.transform(X_future)
                if scaler: X_future = scaler.transform(X_future)
                df_future["Previsto"] = modelo.predict(X_future)

        # Concatena: dados reais + previsões futuras
        df_plot = pd.concat([df, df_future], ignore_index=True)

    except Exception as e:
        st.error(f"Erro ao rodar previsão: {e}")
        return

    # ---------- Métricas só no histórico ----------
    y = df[alvo].astype(float).values
    y_pred_hist = df_hist["Previsto"].values
    if len(y) == len(y_pred_hist):
        metrics = _avaliar(y, y_pred_hist)
        c1, c2, c3 = st.columns(3)
        c1.metric("MAE", f"{metrics['MAE']:.2f}")
        c2.metric("RMSE", f"{metrics['RMSE']:.2f}")
        c3.metric("R²", f"{metrics['R2']:.3f}")
    else:
        st.warning("⚠️ Histórico previsto e real têm tamanhos diferentes — métricas ignoradas.")

    # ---------- Plot ----------
    fig = px.line(df_plot, x="Data",
                  y=[alvo] if df_future.empty else [alvo, "Previsto"],
                  title=f"{escolha} — {cidade}", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Ver tabela de previsões"):
        st.dataframe(df_plot[["Data", alvo, "Previsto"]] if alvo in df_plot else df_plot)

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
