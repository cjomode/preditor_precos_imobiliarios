# 🏠 Preditor Imobiliário — Dashboard Interativo
# ------------------------------------------------------------
# App com 3 seções:
# 1. Captura e atualização do banco (ETL)
# 2. Visualização de dados reais (Dashboard)
# 3. Previsões inteligentes (Prophet e SARIMA)
# ------------------------------------------------------------

import os
import sqlite3
import joblib
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

# 🎨 Configuração inicial da página
st.set_page_config(page_title="Preditor Imobiliário", layout="wide", page_icon="🏠")

# 🧭 Caminhos
HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "db", "warehouse.db")
JOBLIB_PATH = os.path.join(HERE, "modelos_finais_completos.joblib")
PREC_COL = "Preço médio (R$/m²)Total"

# ------------------------------------------------------------
# ⚙️ Funções auxiliares
# ------------------------------------------------------------
def _connect():
    return sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)

@st.cache_data(show_spinner=False)
def _sql(query, params=None):
    with _connect() as conn:
        return pd.read_sql_query(query, conn, params=params)

@st.cache_data(show_spinner=False)
def listar_cidades(tabela):
    df = _sql(f"SELECT DISTINCT Cidade FROM {tabela} ORDER BY Cidade;")
    return df["Cidade"].tolist()

@st.cache_data(show_spinner=False)
def carregar_cidade(tabela, cidade):
    df = _sql(f"SELECT * FROM {tabela} WHERE Cidade = ? ORDER BY Data;", (cidade,))
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df = df.dropna(subset=["Data"])
    return df

# ------------------------------------------------------------
# 🧾 Captura e Atualização de Dados
# ------------------------------------------------------------
def painel_captura():
    st.header("📥 Atualização de Dados")
    st.write("Conecte-se ao pipeline ETL e atualize automaticamente o banco de dados com os dados mais recentes.")
    
    if st.button("🚀 Executar atualização agora"):
        try:
            result = os.system("python script/etl_build_db.py")
            if result == 0:
                st.success("✅ Atualização concluída com sucesso!")
            else:
                st.error("❌ Ocorreu um erro durante a atualização.")
        except Exception as e:
            st.error(f"Erro ao executar ETL: {e}")
    else:
        st.info("Clique no botão acima para rodar o script de atualização (ETL).")

# ------------------------------------------------------------
# 📊 Visualização de Dados Reais
# ------------------------------------------------------------
def painel_dashboard():
    st.header("📊 Visualização de Dados")
    st.caption("Explore a evolução dos preços reais por cidade, direto do banco SQLite.")

    tipo_map = {"Mercado de Locação": "locacao", "Mercado de Venda": "vendas"}
    tipo_label = st.sidebar.radio("Selecione o mercado:", list(tipo_map.keys()))
    tabela = tipo_map[tipo_label]

    cidades = listar_cidades(tabela)
    if not cidades:
        st.warning("⚠️ Nenhuma cidade encontrada no banco.")
        return

    cidade = st.sidebar.selectbox("Selecione a cidade:", cidades)
    df = carregar_cidade(tabela, cidade)

    if df.empty:
        st.warning("Sem dados disponíveis para esta cidade.")
        return

    metrica = PREC_COL if PREC_COL in df.columns else df.select_dtypes(include=[np.number]).columns[0]

    fig = px.line(
        df,
        x="Data",
        y=metrica,
        title=f"📈 {tipo_label} — {cidade}",
        markers=True,
        line_shape="spline"
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Ver dados brutos"):
        st.dataframe(df)

# ------------------------------------------------------------
# 🧠 Previsões Inteligentes
# ------------------------------------------------------------
def painel_modelo():
    st.header("🤖 Previsões Inteligentes")
    st.caption("Compare previsões feitas pelos modelos Prophet e SARIMA.")

    if not os.path.exists(JOBLIB_PATH):
        st.error("Arquivo de modelos não encontrado. Gere o arquivo `.joblib` primeiro.")
        return

    try:
        resultados = joblib.load(JOBLIB_PATH)
    except Exception as e:
        st.error(f"Erro ao carregar modelos: {e}")
        return

    tipo_opcao = st.selectbox("Tipo de mercado:", list(resultados.keys()))
    modelo_opcao = st.selectbox("Modelo:", list(resultados[tipo_opcao].keys()))
    cidades_disp = list(resultados[tipo_opcao][modelo_opcao].keys())
    cidade = st.selectbox("Cidade:", cidades_disp)

    dados = resultados[tipo_opcao][modelo_opcao][cidade]
    if modelo_opcao in dados:
        dados = dados[modelo_opcao]

    if not dados or "metrics" not in dados:
        st.warning("Sem dados disponíveis para esta cidade/modelo.")
        return

    met = dados["metrics"]
    st.subheader(f"📏 Desempenho do Modelo {modelo_opcao.upper()} — {cidade}")
    c1, c2, c3 = st.columns(3)
    c1.metric("MAE", f"{met['MAE']:.2f}")
    c2.metric("RMSE", f"{met['RMSE']:.2f}")
    c3.metric("R²", f"{met['R2']:.2f}")

    tabela = "locacao" if tipo_opcao == "locacao" else "vendas"
    df_real = carregar_cidade(tabela, cidade)
    if df_real.empty:
        st.warning("Sem dados reais para exibir.")
        return

    df_real = df_real.rename(columns={"Data": "ds"}).set_index("ds")
    y_real = df_real[PREC_COL] if PREC_COL in df_real.columns else df_real.iloc[:, -1]
    y_pred_test = dados.get("y_pred_test", pd.Series(dtype=float))
    y_pred_future = dados.get("y_pred_future", pd.Series(dtype=float))

    df_plot = pd.DataFrame({"Real": y_real})
    if not y_pred_test.empty:
        df_plot = df_plot.merge(y_pred_test.rename("Teste"), left_index=True, right_index=True, how="left")
    if not y_pred_future.empty:
        df_plot = pd.concat([df_plot, y_pred_future.rename("Futuro")], axis=0)

    fig = px.line(df_plot, x=df_plot.index, y=df_plot.columns,
                  title=f"📉 {cidade} — {modelo_opcao.upper()}",
                  markers=True)
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# 🔐 Página de Login Simples
# ------------------------------------------------------------
def login_page():
    st.title("🔒 Login - Preditor Imobiliário")
    st.write("Por favor, insira suas credenciais para acessar o sistema.")
    usuario = st.text_input("Usuário:")
    senha = st.text_input("Senha:", type="password")

    if st.button("Entrar"):
        if usuario == "admin" and senha == "admin":
            st.session_state["autenticado"] = True
            st.success("✅ Login realizado com sucesso!")
            st.experimental_rerun()
        else:
            st.error("❌ Usuário ou senha incorretos.")

# ------------------------------------------------------------
# 🚀 Layout principal
# ------------------------------------------------------------
def main():
    # Verificação de login
    if "autenticado" not in st.session_state or not st.session_state["autenticado"]:
        login_page()
        return

    # Interface principal (mantida original)
    st.title("🏠 Preditor Imobiliário")
    st.caption("Dashboard de Análise e Previsão de Preços de Imóveis")

    menu = st.sidebar.radio(
        "Navegar por:",
        ["📥 Atualização de Dados", "📊 Visualização de Dados", "🤖 Previsões Inteligentes"],
        index=1
    )

    if "Atualização" in menu:
        painel_captura()
    elif "Visualização" in menu:
        painel_dashboard()
    else:
        painel_modelo()

# ------------------------------------------------------------
if __name__ == "__main__":
    main()
