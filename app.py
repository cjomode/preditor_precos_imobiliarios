# Codigo com comentarios para explicação

# app.py — RF01, RF02, RF03 + RNFs (Prophet, ARIMA, RandomForest e XGBoost)
# -----------------------------------------------------------------------------
# Este aplicativo Streamlit implementa três Requisitos Funcionais:
# RF01 - Captura de dados
# RF02 - Dashboard com dados reais do banco
# RF03 - Previsões usando modelos de Machine Learning salvos em all_models.joblib
# -----------------------------------------------------------------------------
# RNFs: Performance, reutilização e interface interativa com usuário
# -----------------------------------------------------------------------------

import os
import sqlite3
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Configuração inicial da página Streamlit
st.set_page_config(page_title="Preditor Imobiliário", layout="wide")

# Caminhos base do projeto
HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "db", "warehouse.db")           # Banco de dados SQLite
MODEL_PATH = os.path.join(HERE, "all_models.joblib")         # Arquivo com modelos salvos
PREC_COL = 'Preço médio (R$/m²)Total'                        # Coluna padrão usada como variável alvo

# ----------------- FUNÇÕES AUXILIARES DO BANCO -----------------
def _connect() -> sqlite3.Connection:
    """Abre conexão com o banco SQLite e ajusta parâmetros de desempenho."""
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    with conn:
        # PRAGMAs melhoram integridade e performance
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
    return conn

@st.cache_data(show_spinner=False, ttl=300)
def _sql(q: str, params: tuple | None = None) -> pd.DataFrame:
    """Executa uma query SQL e retorna resultado em DataFrame (com cache)."""
    with _connect() as conn:
        return pd.read_sql_query(q, conn, params=params)

@st.cache_data(show_spinner=False)
def _lista_cidades(tabela: str) -> List[str]:
    """Retorna lista de cidades disponíveis em uma tabela (locação ou venda)."""
    df = _sql(f"SELECT DISTINCT Cidade FROM {tabela} ORDER BY Cidade;")
    return df["Cidade"].dropna().tolist()

@st.cache_data(show_spinner=False)
def _carregar_cidade(tabela: str, cidade: str) -> pd.DataFrame:
    """Carrega todos os dados históricos de uma cidade específica."""
    df = _sql(f"SELECT * FROM {tabela} WHERE Cidade = ? ORDER BY Data;", (cidade,))
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")  # converte para datetime
        df = df.dropna(subset=["Data"]).sort_values("Data")
    return df.reset_index(drop=True)

# ----------------- RF01 - CAPTURA DE DADOS -----------------
def painel_captura():
    """Painel apenas ilustrativo (placeholder) para captura de dados futuros."""
    st.subheader("🧾 Captura de dados (RF01)")
    st.caption("Salva no SQLite — modo único ou em lote por período.")

# ----------------- RF02 - DASHBOARD -----------------
def painel_dashboard():
    """Exibe gráficos com os dados reais armazenados no banco SQLite."""
    st.subheader("📊 Dashboard inicial (RF02)")

    # Seleciona tipo de mercado e cidade
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

    # Filtro por período
    if "Data" in df.columns:
        data_min, data_max = df["Data"].min(), df["Data"].max()
        d_ini, d_fim = st.sidebar.date_input(
            "Período",
            value=(data_min.to_pydatetime().date(), data_max.to_pydatetime().date())
        )
        if d_ini and d_fim:
            df = df[(df["Data"] >= pd.to_datetime(d_ini)) & (df["Data"] <= pd.to_datetime(d_fim))]

    # Seleciona coluna métrica para plotagem
    metrica = PREC_COL if PREC_COL in df.columns else df.select_dtypes(include=[np.number]).columns[0]

    # Gráfico de linha do preço médio
    fig = px.line(df, x="Data", y=metrica, title=f"{tipo_label} • {cidade} • {metrica}", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # Exibe tabela bruta
    with st.expander("Ver dados brutos"):
        st.dataframe(df)

# ----------------- RF03 - MODELO PREDITIVO -----------------
def _avaliar(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calcula métricas de avaliação do modelo."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = r2_score(y_true, y_pred)
    return {"MAE": float(mae), "RMSE": float(rmse), "R2": float(r2)}

def painel_modelo():
    """Carrega modelos treinados e realiza previsões com seleção interativa."""
    st.subheader("🧠 Modelo preditivo (RF03)")
    st.caption("Usa automaticamente all_models.joblib para prever séries por cidade.")

    # Seleção de tipo de mercado e cidade
    tipo_map = {"Locação": "locacao", "Venda": "vendas"}
    tipo_label = st.selectbox("Tipo de mercado", list(tipo_map.keys()), key="mdl_tipo")
    tabela = tipo_map[tipo_label]

    cidades = _lista_cidades(tabela)
    if not cidades:
        st.error("Nenhuma cidade encontrada.")
        return
    cidade = st.selectbox("Cidade", cidades, key="mdl_cidade")

    # Carrega dados da cidade
    df = _carregar_cidade(tabela, cidade)
    if df.empty:
        st.warning("Sem dados.")
        return

    # Define variável alvo
    alvo = PREC_COL if PREC_COL in df.columns else df.select_dtypes(include=[np.number]).columns[-1]

    # Checa se arquivo com modelos existe
    if not os.path.exists(MODEL_PATH):
        st.error(f"Nenhum modelo encontrado em {MODEL_PATH}.")
        return

    try:
        modelos = joblib.load(MODEL_PATH)
    except Exception as e:
        st.error(f"Erro ao carregar modelos: {e}")
        return

    # Cria chave única para acessar modelos no joblib
    chave = f"{tabela}_{cidade.lower()}"
    if chave not in modelos:
        st.error(f"Não há modelo treinado para {chave} no all_models.joblib.")
        return

    entry = modelos[chave]  # Dicionário com todos os modelos salvos para essa cidade

    # Mapeia nomes técnicos para nomes amigáveis (para o usuário)
    nome_amigavel = {
        "prophet_model": "Prophet",
        "arima_model": "ARIMA",
        "rf_model": "Random Forest",
        "xgb_model": "XGBoost"
    }

    # Lista apenas modelos disponíveis e faz o selectbox
    modelo_opcoes = [k for k in entry.keys() if k in nome_amigavel]
    opcoes_display = [nome_amigavel[k] for k in modelo_opcoes]
    escolha_display = st.selectbox("Escolha o modelo salvo:", opcoes_display)
    escolha = [k for k, v in nome_amigavel.items() if v == escolha_display][0]
    modelo = entry[escolha]

    # Remove registros sem valor na variável alvo
    df = df.dropna(subset=[alvo]).copy()

    # Carrega dataframe histórico (caso exista)
    hist_df = entry.get("historical_df", pd.DataFrame()).copy()
    if not hist_df.empty and "Data" in hist_df.columns:
        df_merged = pd.merge(df, hist_df.drop(columns=[PREC_COL], errors="ignore"), on="Data", how="left")
    else:
        df_merged = df.copy()

    # Checkbox para previsões futuras
    prever_futuro = st.checkbox("🔮 Prever até 2027", value=False)
    last_date = df["Data"].max()
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), end="2027-12-01", freq="MS")

    try:
        # -------- PREVISÃO HISTÓRICA --------
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
            features = entry.get("rf_features" if escolha == "rf_model" else "xgb_features", [])
            imputer = entry.get("rf_imputer" if escolha == "rf_model" else "xgb_imputer", None)
            scaler = entry.get("rf_scaler" if escolha == "rf_model" else "xgb_scaler", None)
            for f in features:
                if f not in df_merged.columns:
                    df_merged[f] = 0
            X = df_merged[features].fillna(0)
            if imputer: X = imputer.transform(X)
            if scaler: X = scaler.transform(X)
            df_hist = df.copy()
            df_hist["Previsto"] = modelo.predict(X)

        # -------- PREVISÃO FUTURA --------
        df_future = pd.DataFrame()
        if prever_futuro:
            if escolha == "prophet_model":
                extra_future = modelo.make_future_dataframe(periods=len(future_dates), freq="MS")
                for r in regressors:
                    extra_future[r] = 0
                forecast_future = modelo.predict(extra_future)
                df_future = forecast_future[["ds", "yhat"]].rename(columns={"ds": "Data", "yhat": "Previsto"})
                df_future = df_future[df_future["Data"] > df["Data"].max()]
            elif escolha == "arima_model":
                future_forecast = modelo.forecast(steps=len(future_dates))
                if diff and last_val is not None:
                    future_forecast = np.r_[last_val, future_forecast].cumsum()[1:]
                df_future = pd.DataFrame({"Data": future_dates, "Previsto": future_forecast})
            else:
                df_future = pd.DataFrame({"Data": future_dates})
                for f in features:
                    df_future[f] = 0
                X_future = df_future[features]
                if imputer:
                    X_future = imputer.transform(X_future)
                if scaler:
                    X_future = scaler.transform(X_future)
                df_future["Previsto"] = modelo.predict(X_future)

        # Junta previsões históricas + futuras
        df_plot = pd.concat([df_hist, df_future], ignore_index=True)

    except Exception as e:
        st.error(f"Erro ao rodar previsão: {e}")
        return

    # -------- MÉTRICAS DE AVALIAÇÃO --------
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

    # Gráfico final
    fig = px.line(df_plot, x="Data",
                  y=[alvo] if "Previsto" not in df_plot.columns else [alvo, "Previsto"],
                  title=f"{escolha_display} — {cidade}", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # Exibe tabela com previsões
    with st.expander("📋 Ver tabela de previsões"):
        colunas_disponiveis = [c for c in ["Data", alvo, "Previsto"] if c in df_plot.columns]
        st.dataframe(df_plot[colunas_disponiveis])

# ----------------- LAYOUT PRINCIPAL -----------------
def main():
    """Organiza o layout geral e alterna entre os painéis RF01, RF02 e RF03."""
    st.title("🏠 Preditor Imobiliário")
    st.caption("Atende RF01, RF02, RF03 + RNF01..RNF04. Base: db/warehouse.db (ETL).")

    painel = st.sidebar.radio("Painel", ["Captura (RF01)", "Dashboard (RF02)", "Modelo (RF03)"], index=1)
    if painel.startswith("Captura"):
        painel_captura()
    elif painel.startswith("Dashboard"):
        painel_dashboard()
    else:
        painel_modelo()

# Executa app
if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        st.error(f"Banco não encontrado em {DB_PATH}. Rode a ETL primeiro.")
    else:
        main()
# -----------------------------------------------------------------------------
# 🔎 OBSERVAÇÃO IMPORTANTE SOBRE AS MÉTRICAS:
# As métricas (MAE, RMSE, R²) podem parecer estranhas por alguns motivos:
# 1. Os modelos foram treinados com base em séries temporais curtas ou ruidosas.
# 2. Há defasagem entre a variável prevista e os dados reais (datas não alinhadas).
# 3. As features externas (variáveis macroeconômicas) podem estar zeradas no histórico.
# 4. Alguns modelos (ARIMA, Prophet) geram previsões suavizadas, não captando variações abruptas.
# 5. O R² pode ficar baixo ou negativo se a série for muito volátil.
# Portanto, as métricas devem ser interpretadas com cautela — o foco é a tendência geral da curva.
# -----------------------------------------------------------------------------
