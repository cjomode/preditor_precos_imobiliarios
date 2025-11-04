import os
import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# 🎨 Configuração da página
# ============================================================
st.set_page_config(
    page_title="Preditor Imobiliário",
    layout="wide",
    page_icon="🏠"
)

# ============================================================
# 🧭 Caminhos locais
# ============================================================
HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "csv_unico.csv")
JOBLIB_PATH = os.path.join(HERE, "modelos_sarima.joblib")


# ============================================================
# 🔐 Tela de Login
# ============================================================
def mostrar_login():
    # garante que a chave exista
    if "auth" not in st.session_state:
        st.session_state["auth"] = False

    st.markdown("## 🏠 Preditor Imobiliário")
    st.markdown("### 🔐 Acesso restrito")

    # layout centralizado
    col_esq, col_centro, col_dir = st.columns([1, 2, 1])
    with col_centro:
        st.markdown(
            """
            <div style="
                padding: 2rem;
                border-radius: 0.8rem;
                background-color: #111827;
                border: 1px solid #374151;
                box-shadow: 0 10px 30px rgba(0,0,0,0.45);
            ">
                <h3 style="margin-bottom: 0.5rem;">Login do painel</h3>
                <p style="font-size: 0.9rem; color: #9CA3AF; margin-top: 0;">
                    Acesse com suas credenciais administrativas.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # form logo abaixo do card de texto
        with st.form("login_form"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar")

        if entrar:
            if usuario == "admin" and senha == "admin":
                st.session_state["auth"] = True
                st.success("Login realizado com sucesso! ✨")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")


# ============================================================
# 🔎 Funções auxiliares de detecção de coluna
# ============================================================
def detectar_coluna(colunas, candidatos):
    """
    Tenta achar uma coluna que:
    - seja exatamente igual a um dos candidatos (ignorando maiúsc/minúsc)
    - OU contenha o texto candidato dentro.
    Retorna o nome REAL da coluna encontrada, ou None.
    """
    lower_map = {c.lower(): c for c in colunas}

    for cand in candidatos:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]

    for cand in candidatos:
        alvo = cand.lower()
        for real in colunas:
            if alvo in real.lower():
                return real

    return None


def detectar_coluna_data(cols):
    candidatos_data = [
        "data", "dt", "date", "data_mes", "mes", "mes_referencia",
        "periodo", "referencia", "competencia", "Data", "DATA", "Periodo",
        "Data_Mes", "Mes"
    ]
    return detectar_coluna(cols, candidatos_data)


def detectar_coluna_cidade(cols):
    candidatos_cidade = [
        "cidade", "municipio", "município", "City", "CIDADE", "localidade"
    ]
    return detectar_coluna(cols, candidatos_cidade)


def detectar_coluna_tipo(cols):
    candidatos_tipo = [
        "tipo_mercado", "Tipo_Mercado", "segmento", "mercado",
        "tipo", "Tipo", "TipoMercado", "TipoMercado_Nome"
    ]
    return detectar_coluna(cols, candidatos_tipo)


def detectar_coluna_preco(cols):
    """
    Tenta achar a coluna de preço/m².
    """
    candidatos_preco_fixos = [
        "Preco_m2",
        "preco_m2",
        "Preço médio (R$/m²) Total",
        "Preço médio (R$/m²)Total",
        "Preço_médio_m2",
        "Preço_m2",
        "valor_m2",
        "valor_medio_m2",
        "preco",
        "preço",
        "Numero_Indice_Total",
        "numero_indice_total",
        "Indice_Total",
        "Indice",
    ]
    col = detectar_coluna(cols, candidatos_preco_fixos)
    if col:
        return col

    for c in cols:
        cl = c.lower()
        if ("preco" in cl or "preço" in cl or "m²" in cl or "m2" in cl or
                "indice" in cl or "índice" in cl):
            return c

    return None


# ============================================================
# 📥 Carregar dados históricos
# ============================================================
@st.cache_data(show_spinner=False)
def carregar_dados_historicos():
    """
    Lê csv_unico.csv e devolve colunas padronizadas:
    ['data', 'cidade', 'tipo_mercado', 'preco_m2']
    """
    if not os.path.exists(CSV_PATH):
        st.error("❌ O arquivo 'csv_unico.csv' não foi encontrado na pasta do projeto.")
        return pd.DataFrame()

    try:
        df = pd.read_csv(
            CSV_PATH,
            sep=None,
            engine="python",
            encoding="utf-8",
        )
    except UnicodeDecodeError:
        df = pd.read_csv(
            CSV_PATH,
            sep=None,
            engine="python",
            encoding="latin-1",
        )

    df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

    col_data = detectar_coluna_data(df.columns)
    col_cidade = detectar_coluna_cidade(df.columns)
    col_tipo = detectar_coluna_tipo(df.columns)
    col_preco = detectar_coluna_preco(df.columns)

    faltando = []
    if col_data is None:
        faltando.append("data (ex: Data / Periodo / Mes / Referencia)")
    if col_cidade is None:
        faltando.append("cidade (ex: Cidade / Municipio)")
    if col_tipo is None:
        faltando.append("tipo_mercado (ex: Tipo_Mercado / Mercado)")
    if col_preco is None:
        faltando.append("preco_m2 (preço médio m² / índice de preço)")

    if faltando:
        st.error("⚠ Não consegui mapear todas as colunas essenciais do CSV.")
        st.write("O que ficou faltando identificar:", faltando)
        st.write("Colunas que existem no CSV:", list(df.columns))
        return pd.DataFrame()

    df = df.rename(columns={
        col_data: "data",
        col_cidade: "cidade",
        col_tipo: "tipo_mercado",
        col_preco: "preco_m2"
    })

    df["data"] = pd.to_datetime(df["data"], errors="coerce", dayfirst=False)

    if df["preco_m2"].dtype == object:
        df["preco_m2"] = (
            df["preco_m2"]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
    df["preco_m2"] = pd.to_numeric(df["preco_m2"], errors="coerce")

    df = df.dropna(subset=["data", "cidade", "tipo_mercado", "preco_m2"])
    df = df.sort_values(["cidade", "tipo_mercado", "data"]).reset_index(drop=True)

    return df[["data", "cidade", "tipo_mercado", "preco_m2"]]


# ============================================================
# 🤖 Carregar previsões SARIMA
# ============================================================
@st.cache_resource(show_spinner=False)
def carregar_snapshot_previsoes():
    """
    Espera um joblib com:
      pacote["previsoes_futuras"]: df [data, cidade, tipo_mercado, preco_previsto]
      pacote["historico_real"]: df [data, cidade, tipo_mercado, preco_real] (opcional)
      pacote["info"]: dict com "ultima_data_historica"
    """
    if not os.path.exists(JOBLIB_PATH):
        return None

    try:
        pacote = joblib.load(JOBLIB_PATH)
    except Exception as e:
        st.error(f"❌ Erro lendo o arquivo modelos_sarima.joblib: {e}")
        return None

    if "previsoes_futuras" in pacote and isinstance(pacote["previsoes_futuras"], pd.DataFrame):
        pacote["previsoes_futuras"]["data"] = pd.to_datetime(
            pacote["previsoes_futuras"]["data"], errors="coerce"
        )

    if "historico_real" in pacote and isinstance(pacote.get("historico_real"), pd.DataFrame):
        pacote["historico_real"]["data"] = pd.to_datetime(
            pacote["historico_real"]["data"], errors="coerce"
        )

    return pacote


# ============================================================
# 📊 Aba 1 - Visualização Histórica
# ============================================================
def painel_dashboard(df_hist):
    st.header("📊 Visão Histórica do Mercado Imobiliário")
    st.caption("Evolução do preço médio (R$/m²) ao longo do tempo, por cidade e tipo de mercado.")

    if df_hist.empty:
        st.warning("⚠ Ainda não consegui montar a base histórica. Veja avisos acima 👆.")
        return

    cidades = sorted(df_hist["cidade"].unique())
    mercados = sorted(df_hist["tipo_mercado"].unique())

    col1, col2 = st.columns(2)
    with col1:
        cidade_sel = st.selectbox("Cidade:", cidades)
    with col2:
        mercado_sel = st.selectbox("Tipo de Mercado:", mercados)

    base = df_hist[
        (df_hist["cidade"] == cidade_sel) &
        (df_hist["tipo_mercado"] == mercado_sel)
    ].copy()

    if base.empty:
        st.warning("Sem dados para esse filtro.")
        return

    fig = px.line(
        base,
        x="data",
        y="preco_m2",
        title=f"{cidade_sel} — {mercado_sel} (Histórico R$/m²)",
        markers=True,
        line_shape="spline",
        labels={
            "data": "Data",
            "preco_m2": "Preço (R$/m²)"
        }
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Ver dados brutos"):
        st.dataframe(base.sort_values("data").reset_index(drop=True))


# ============================================================
# 🤖 Aba 2 - Previsões Inteligentes
# ============================================================
def painel_previsoes(pacote):
    st.header("🤖 Previsões de Preço Futuro")
    st.caption("Projeções SARIMA até 2028, baseadas em dados históricos consolidados.")

    if pacote is None or "previsoes_futuras" not in pacote:
        st.error("⚠ Nenhuma previsão disponível. Verifique se o arquivo modelos_sarima.joblib está correto.")
        return

    previsoes = pacote["previsoes_futuras"].copy()
    historico = pacote.get("historico_real", None)
    info = pacote.get("info", {})
    ultima_data_hist = pd.to_datetime(info.get("ultima_data_historica", None), errors="coerce")

    cidades = sorted(previsoes["cidade"].unique())
    mercados = sorted(previsoes["tipo_mercado"].unique())

    col1, col2 = st.columns(2)
    with col1:
        cidade_sel = st.selectbox("Cidade (previsão):", cidades)
    with col2:
        mercado_sel = st.selectbox("Tipo de Mercado (previsão):", mercados)

    fut = previsoes[
        (previsoes["cidade"] == cidade_sel) &
        (previsoes["tipo_mercado"] == mercado_sel)
    ].copy()

    fut = fut.sort_values("data")

    linhas = []

    if isinstance(historico, pd.DataFrame):
        hist = historico[
            (historico["cidade"] == cidade_sel) &
            (historico["tipo_mercado"] == mercado_sel)
        ].copy()

        if not hist.empty:
            hist = hist.rename(columns={"preco_real": "valor"})
            hist["Serie"] = "Histórico Real"
            linhas.append(hist[["data", "valor", "Serie"]])

    fut_plot = fut.rename(columns={"preco_previsto": "valor"})
    fut_plot["Serie"] = "Previsão SARIMA"
    linhas.append(fut_plot[["data", "valor", "Serie"]])

    df_plot = pd.concat(linhas, ignore_index=True)

    fig = px.line(
        df_plot,
        x="data",
        y="valor",
        color="Serie",
        markers=True,
        labels={"data": "Data", "valor": "Preço (R$/m²)"},
        title=f"{cidade_sel} — {mercado_sel} (Histórico + Projeção)"
    )

    if pd.notnull(ultima_data_hist):
        fig.add_shape(
            type="line",
            x0=ultima_data_hist,
            x1=ultima_data_hist,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="gray", dash="dot", width=2)
        )
        fig.add_annotation(
            x=ultima_data_hist,
            y=1,
            yref="paper",
            text="Início da projeção",
            showarrow=False,
            xanchor="left",
            yanchor="top"
        )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Próximos 6 meses estimados")
    preview = fut[["data", "preco_previsto"]].tail(6).rename(columns={
        "data": "Data",
        "preco_previsto": "Preço Previsto (R$/m²)"
    })
    st.dataframe(preview.reset_index(drop=True))


# ============================================================
# 🚀 Layout principal
# ============================================================
def main():
    # controle de sessão
    if "auth" not in st.session_state:
        st.session_state["auth"] = False

    # se não estiver autenticado, mostra login e para aqui
    if not st.session_state["auth"]:
        mostrar_login()
        return

    # ---- a partir daqui só vê quem logou ----
    st.title("🏠 Preditor Imobiliário")
    st.caption("Dashboard acadêmico de análise e previsão de preços de imóveis.")

    # botão de logout na sidebar
    st.sidebar.markdown("### 👤 Sessão")
    if st.sidebar.button("Sair"):
        st.session_state["auth"] = False
        st.rerun()

    aba = st.sidebar.radio(
        "Navegar por:",
        ["📊 Visualização de Dados", "🤖 Previsões Inteligentes"],
        index=0
    )

    df_hist = carregar_dados_historicos()
    pacote_prev = carregar_snapshot_previsoes()

    if aba.startswith("📊"):
        painel_dashboard(df_hist)
    else:
        painel_previsoes(pacote_prev)

    st.markdown("---")
    st.caption("Protótipo acadêmico. Dados confidenciais.")


# ============================================================
# 🏁 main
# ============================================================
if __name__ == "__main__":
    main()
