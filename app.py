import os
import time
import json
import joblib
import pandas as pd
import plotly.express as px
import streamlit as st
from fpdf import FPDF
from gtts import gTTS
import tempfile
import pyotp
import qrcode
from PIL import Image
from io import BytesIO

# -------------------- Config da página --------------------
st.set_page_config(
    page_title="PredImóveis",
    layout="wide",
    page_icon="🏠"
)

# -------------------- Caminhos --------------------
HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "csv_unico.csv")
JOBLIB_PATH = os.path.join(HERE, "modelos_sarima.joblib")


# -------------------- Acessibilidade: TTS --------------------
def ler_texto_em_voz_alta(texto: str):
    """Gera áudio (pt-BR) do texto e exibe um player no Streamlit."""
    if not texto or not str(texto).strip():
        st.warning("Nenhum texto disponível para leitura.")
        return
    try:
        tts = gTTS(text=str(texto), lang="pt-br")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tts.save(tmp.name)
            st.audio(tmp.name, format="audio/mp3")
    except Exception as e:
        st.error(f"Erro ao gerar áudio: {e}")


# -------------------- Login (versão Juliana) --------------------
def mostrar_login():
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
    if "basic_auth" not in st.session_state:
        st.session_state["basic_auth"] = False

    with st.container():
        col1, col2, col3 = st.columns([1, 0.4, 1]) 
    with col2:
        st.image("images/predimoveislogo.png", use_container_width=False, width=200)

    st.markdown(
        """
    <style>
        footer { visibility: hidden !important; }

        /* Título e formulário */
        .stHeading, .stForm { margin: 0 auto; text-align: center; }
        .stForm { width: 65%; }
        
        /* Título interno do login */
        h2, h3, h4, p {
            text-align: left !important;
        }

        /* Botão de envio */
        div[data-testid="stFormSubmitButton"] > button {
            background: #28a745 !important;
            color: #fff !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            transition: 0.2s ease-in-out !important;
        }
        div[data-testid="stFormSubmitButton"] > button:hover {
            background: #218838 !important;
        }

        /* Labels */
        .stForm label p {
            font-size: 19px !important;
        }

        /* Mensagens de status */
        .custom-message {
            width: 65%;
            margin: 10px auto;
            padding: 1rem;
            border-radius: 8px;
            text-align: left;
        }
        .success-message {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error-message {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
        """,
        unsafe_allow_html=True
    )

    # Form de login básico (só se não basic_auth)
    if not st.session_state["basic_auth"]:
        with st.form("login_form"):
            st.markdown("### 🔐 Login do painel")
            st.write("Acesse com suas credenciais administrativas.")
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar")

        if entrar:
            if usuario == "admin" and senha == "admin":
                st.session_state["basic_auth"] = True
                st.markdown(
                    '<div class="custom-message success-message">✅ Login básico realizado! Agora configure o MFA.</div>',
                    unsafe_allow_html=True
                )
                time.sleep(2)
                st.rerun()
            else:
                st.markdown(
                    '<div class="custom-message error-message">❌ Usuário ou senha incorretos.</div>',
                    unsafe_allow_html=True
                )

    # MFA (só se basic_auth e não auth)
    if st.session_state["basic_auth"] and not st.session_state["auth"]:
        st.markdown(
            """
            <div style="display:flex; justify-content:center; align-items:center;">
                <h3 style="margin:0;">🔐 Verificação MFA (2º Fator)</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Garante que o segredo exista
        if "user_secret" not in st.session_state:
            st.session_state.user_secret = pyotp.random_base32()

        totp = pyotp.TOTP(st.session_state.user_secret)
        uri = totp.provisioning_uri(
            name="admin@example.com",
            issuer_name="PredImóveis"
        )

        qr = qrcode.make(uri)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        buf.seek(0)

        # Centraliza QR
        col_esq, col_centro, col_dir = st.columns([1, 2, 1])
        with col_centro:
            st.image(
                Image.open(buf),
                caption="📱 Escaneie no app (ex: 2FAS, Google Authenticator)",
                width=180,
            )
            st.markdown("<br>", unsafe_allow_html=True)

        # Form para MFA
        with st.form("mfa_form"):
            otp = st.text_input("Digite o código MFA:", type="password", max_chars=6)
            verificar = st.form_submit_button("Verificar MFA")

            if verificar:
                if totp.verify(otp):
                    st.session_state["auth"] = True
                    st.success("✅ Login MFA verificado com sucesso!")
                    time.sleep(2)
                    st.rerun()
                else:
                    time.sleep(2)
                    st.error("❌ Código inválido. Tente novamente.")


# -------------------- Helpers de colunas --------------------
def detectar_coluna(colunas, candidatos):
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
    candidatos = [
        "data", "dt", "date", "data_mes", "mes", "mes_referencia",
        "periodo", "referencia", "competencia", "Data", "DATA",
        "Periodo", "Data_Mes", "Mes"
    ]
    return detectar_coluna(cols, candidatos)


def detectar_coluna_cidade(cols):
    candidatos = ["cidade", "municipio", "município", "City", "CIDADE", "localidade"]
    return detectar_coluna(cols, candidatos)


def detectar_coluna_tipo(cols):
    candidatos = [
        "tipo_mercado", "Tipo_Mercado", "segmento", "mercado",
        "tipo", "Tipo", "TipoMercado", "TipoMercado_Nome"
    ]
    return detectar_coluna(cols, candidatos)


def detectar_coluna_preco(cols):
    candidatos_fixos = [
        "Preco_m2", "preco_m2",
        "Preço médio (R$/m²) Total", "Preço médio (R$/m²)Total",
        "Preço_médio_m2", "Preço_m2",
        "valor_m2", "valor_medio_m2",
        "preco", "preço",
        "Numero_Indice_Total", "numero_indice_total",
        "Indice_Total", "Indice",
    ]
    col = detectar_coluna(cols, candidatos_fixos)
    if col:
        return col
    for c in cols:
        cl = c.lower()
        if ("preco" in cl or "preço" in cl or "m²" in cl or "m2" in cl or
                "indice" in cl or "índice" in cl):
            return c
    return None


# -------------------- Dados históricos --------------------
@st.cache_data(show_spinner=False)
def carregar_dados_historicos():
    if not os.path.exists(CSV_PATH):
        st.error("❌ O arquivo 'csv_unico.csv' não foi encontrado na pasta do projeto.")
        return pd.DataFrame()

    try:
        df = pd.read_csv(
            CSV_PATH,
            sep=None,
            engine="python",
            encoding="utf-8",
            dtype=str
        )
    except UnicodeDecodeError:
        df = pd.read_csv(
            CSV_PATH,
            sep=None,
            engine="python",
            encoding="latin-1",
            dtype=str
        )

    df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

    col_data = detectar_coluna_data(df.columns)
    col_cidade = detectar_coluna_cidade(df.columns)
    col_tipo = detectar_coluna_tipo(df.columns)
    col_preco = detectar_coluna_preco(df.columns)

    df = df.rename(columns={
        col_data: "data",
        col_cidade: "cidade",
        col_tipo: "tipo_mercado",
        col_preco: "preco_m2"
    })

    # --- Correção de nomes incompletos das cidades ---
    df["cidade"] = df["cidade"].replace({
        "João": "João Pessoa",
        "São": "São Luís"
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


# -------------------- Previsões SARIMA --------------------
@st.cache_resource(show_spinner=False)
def carregar_snapshot_previsoes():
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


# -------------------- Acessibilidade: textos das seções --------------------
def texto_dashboard_acessivel(base, cidade_sel, mercado_sel):
    if base.empty:
        return "Sem dados para o filtro escolhido."
    inicial = base["preco_m2"].iloc[0]
    atual = base["preco_m2"].iloc[-1]
    media = base["preco_m2"].mean()
    minimo = base["preco_m2"].min()
    maximo = base["preco_m2"].max()
    variacao = (atual - inicial) / inicial * 100 if inicial != 0 else 0
    return (
        f"Visão histórica do mercado imobiliário de {cidade_sel}, no segmento {mercado_sel}. "
        f"Preço médio do período: {media:.2f} reais por metro quadrado. "
        f"Valor mínimo observado: {minimo:.2f}. Valor máximo observado: {maximo:.2f}. "
        f"Valor atual: {atual:.2f}. Variação acumulada desde o início: {variacao:.1f} por cento. "
        "O gráfico de linha mostra a evolução mensal do preço."
    )


def texto_previsoes_acessivel(fut, cidade_sel, mercado_sel, ultima_data_hist):
    if fut.empty:
        return "Sem dados de previsão para o filtro escolhido."
    inicio = fut["data"].min()
    fim = fut["data"].max()
    ult = fut.sort_values("data").iloc[-1]["preco_previsto"]
    return (
        f"Previsões de preço para {cidade_sel}, mercado {mercado_sel}. "
        f"Janela de projeção de {inicio:%b %Y} até {fim:%b %Y}. "
        f"Preço previsto no último mês da projeção: {ult:.2f} reais por metro quadrado. "
        f"A linha vertical indica o início da projeção após {ultima_data_hist:%b %Y}."
        if pd.notnull(ultima_data_hist) else
        f"Previsões de preço para {cidade_sel}, mercado {mercado_sel}. "
        f"Janela de projeção de {inicio:%b %Y} até {fim:%b %Y}. "
        f"Preço previsto no último mês: {ult:.2f} reais por metro quadrado."
    )


def texto_relatorio_acessivel(texto_resumo, resumo_kpis):
    partes = [texto_resumo.strip()]
    for k, v in resumo_kpis.items():
        partes.append(f"{k}: {v}")
    partes.append("Você pode baixar o relatório completo em PDF usando o botão disponível.")
    return " ".join(partes)


# -------------------- Aba 1: histórico --------------------
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

    if st.button("🎧 Ouvir explicação desta seção"):
        ler_texto_em_voz_alta(texto_dashboard_acessivel(base, cidade_sel, mercado_sel))

    fig = px.line(
        base,
        x="data",
        y="preco_m2",
        title=f"{cidade_sel} — {mercado_sel} (Histórico R$/m²)",
        markers=True,
        line_shape="spline",
        labels={"data": "Data", "preco_m2": "Preço (R$/m²)"}
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Ver dados brutos"):
        st.dataframe(base.sort_values("data").reset_index(drop=True))


# -------------------- Aba 2: previsões --------------------
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

    if st.button("🎧 Ouvir explicação das previsões"):
        ler_texto_em_voz_alta(texto_previsoes_acessivel(fut, cidade_sel, mercado_sel, ultima_data_hist))

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


# -------------------- PDF --------------------
def gerar_pdf_relatorio(cidade, mercado, df_base, resumo_kpis, texto_resumo):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Relatorio de Acompanhamento - Mercado Imobiliario", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Cidade: {cidade}", ln=True)
    pdf.cell(0, 8, f"Tipo de mercado: {mercado}", ln=True)

    pdf.ln(6)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Resumo executivo:", ln=True)

    pdf.ln(2)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, texto_resumo)

    pdf.ln(4)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Indicadores principais:", ln=True)

    pdf.set_font("Arial", "", 11)
    for nome, valor in resumo_kpis.items():
        pdf.cell(0, 7, f"- {nome}: {valor}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Ultimas observacoes:", ln=True)

    pdf.set_font("Arial", "", 10)
    df_tab = df_base.sort_values("data").tail(12).copy()
    df_tab["data_str"] = df_tab["data"].dt.strftime("%d/%m/%Y")

    for _, row in df_tab.iterrows():
        linha = f"{row['data_str']} - R$/m2: {row['preco_m2']:.2f}"
        pdf.cell(0, 6, linha, ln=True)

    result = pdf.output(dest="S")
    if isinstance(result, str):
        return result.encode("latin-1")
    else:
        return bytes(result)


# -------------------- Aba 3: dashboards + relatório --------------------
def painel_relatorios(df_hist):
    st.header("📑 Análise Exploratória por Cidade + Relatório em PDF")
    st.caption("Dashboards exploratórios e relatório automático em PDF.")

    if df_hist.empty:
        st.warning("⚠ Ainda não há dados históricos suficientes para montar o relatório.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        cidade_sel = st.selectbox("Cidade:", sorted(df_hist["cidade"].unique()), key="rel_cidade")
    with col2:
        mercado_sel = st.selectbox("Tipo de mercado:", sorted(df_hist["tipo_mercado"].unique()), key="rel_mercado")
    with col3:
        periodo = st.selectbox(
            "Período:",
            ["Completo", "Últimos 12 meses", "Últimos 24 meses"],
            index=1,
            key="rel_periodo"
        )

    base = df_hist[
        (df_hist["cidade"] == cidade_sel) &
        (df_hist["tipo_mercado"] == mercado_sel)
    ].copy()

    if base.empty:
        st.warning("Sem dados para esse filtro.")
        return

    base = base.sort_values("data")

    if periodo != "Completo":
        max_data = base["data"].max()
        meses = 12 if periodo == "Últimos 12 meses" else 24
        corte = max_data - pd.DateOffset(months=meses)
        base = base[base["data"] >= corte]

    atual = base["preco_m2"].iloc[-1]
    inicial = base["preco_m2"].iloc[0]
    media = base["preco_m2"].mean()
    minimo = base["preco_m2"].min()
    maximo = base["preco_m2"].max()
    desvio = base["preco_m2"].std()

    variacao_abs = atual - inicial
    variacao_pct = (variacao_abs / inicial * 100) if inicial != 0 else 0

    def formata_valor(v):
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    preco_medio_str = formata_valor(media)
    preco_atual_str = formata_valor(atual)
    variacao_pct_str = f"{variacao_pct:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    desvio_str = f"{desvio:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    valor_inicial_limpo = formata_valor(inicial)
    valor_atual_limpo = preco_medio_str if variacao_pct == 0 else preco_atual_str

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Preço atual (R$/m²)", preco_atual_str)
    col_kpi2.metric("Média no período (R$/m²)", preco_medio_str)
    col_kpi3.metric(
        "Variação acumulada",
        f"{variacao_pct_str}%",
        formata_valor(variacao_abs)
    )

    # faixas de preço
    if base["preco_m2"].nunique() >= 4:
        cat = pd.qcut(base["preco_m2"], q=4, duplicates="drop")
    elif base["preco_m2"].nunique() >= 2:
        cat = pd.cut(base["preco_m2"], bins=3, include_lowest=True)
    else:
        cat = pd.Series(["Valor único"] * len(base), index=base.index)

    base["faixa_preco"] = cat
    base["faixa_preco_str"] = base["faixa_preco"].astype(str)

    vc_faixa = base["faixa_preco_str"].value_counts()
    faixa_dominante_existe = not vc_faixa.empty
    perc_dom = float(vc_faixa.iloc[0] / vc_faixa.sum() * 100) if faixa_dominante_existe else 0.0
    perc_dom_str = f"{perc_dom:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")

    data_ini = base["data"].min().strftime("%d/%m/%Y")
    data_fim = base["data"].max().strftime("%d/%m/%Y")

    if variacao_pct > 5:
        sentido = "uma tendência de valorização do metro quadrado na região"
    elif variacao_pct < -5:
        sentido = "uma tendência de queda nos valores praticados"
    else:
        sentido = "um comportamento relativamente estável dos preços ao longo do período analisado"

    if desvio < 0.5:
        volatilidade = "que os preços variam pouco em torno da média"
    elif desvio < 1.5:
        volatilidade = "que existe alguma variação, mas sem grandes extremos"
    else:
        volatilidade = "que há bastante diferença entre os valores mais baixos e mais altos observados"

    if faixa_dominante_existe:
        trecho_pizza = (
            f"Os gráficos de pizza e de barras por faixa de preço mostram que cerca de {perc_dom_str}% "
            "das observações se concentram em um intervalo específico, indicando que a maior parte dos contratos "
            "fica em torno de um mesmo nível de preço."
        )
    else:
        trecho_pizza = (
            "Os gráficos de pizza e de barras por faixa de preço indicam que as observações estão bem distribuídas "
            "entre as diferentes faixas, sem grande concentração em apenas um nível."
        )

    texto_resumo = (
        f"No período de {data_ini} a {data_fim}, analisamos o comportamento dos preços de imóveis em "
        f"{cidade_sel}, no segmento de {mercado_sel.lower()}. \n\n"
        f"Nesse intervalo, o preço médio foi de aproximadamente R$ {preco_medio_str} por metro quadrado, "
        f"e o valor mais recente observado é de cerca de R$ {preco_atual_str} por metro quadrado. "
        f"Isso representa uma variação acumulada de aproximadamente {variacao_pct_str}% em relação ao início do período, "
        f"o que sugere {sentido}. \n\n"
        "O gráfico de linha mostra como esses preços evoluíram ao longo do tempo, mês a mês. "
        "Os gráficos de barras e o boxplot por ano ajudam a comparar os níveis médios e a dispersão dos preços "
        "entre os diferentes anos analisados. "
        f"{trecho_pizza} "
        f"A tabela de estatísticas descritivas indica um desvio padrão em torno de {desvio_str}, o que sugere {volatilidade}. \n\n"
        "De forma geral, esses resultados ajudam a entender o comportamento do mercado na cidade analisada e podem "
        "apoiar decisões de reajuste de contratos, negociação de valores e planejamento de investimentos futuros."
    )

    if st.button("🎧 Ouvir resumo desta seção"):
        resumo_kpis_tmp = {
            "Preço atual (R$/m²)": f"R$ {preco_atual_str}",
            "Média no período": f"R$ {preco_medio_str}",
            "Variação acumulada": f"{variacao_pct_str}%",
        }
        ler_texto_em_voz_alta(texto_relatorio_acessivel(texto_resumo, resumo_kpis_tmp))

    st.markdown("### 📝 Resumo em texto corrido")
    st.text(texto_resumo)

    # gráficos
    st.markdown("### 📈 Tendência no período selecionado")
    fig_linha = px.line(
        base,
        x="data",
        y="preco_m2",
        markers=True,
        line_shape="spline",
        labels={"data": "Data", "preco_m2": "Preço (R$/m²)"},
        title=f"Evolução do preço — {cidade_sel} / {mercado_sel}"
    )
    st.plotly_chart(fig_linha, use_container_width=True)

    texto_linha = (
        f"No gráfico de linha acima, cada ponto representa o preço médio do metro quadrado em um mês. "
        f"Quando a linha sobe, significa que os preços ficaram mais altos; quando desce, que eles recuaram. "
        f"Nesta cidade, no período analisado, saímos de um valor próximo de R$ {valor_inicial_limpo} e chegamos a cerca de R$ {valor_atual_limpo}, "
        f"o que reforça {sentido}."
    )
    st.caption(f'<p style="font-size: 0.875rem">{texto_linha}</p>', unsafe_allow_html=True)

    base["ano"] = base["data"].dt.year
    por_ano = base.groupby("ano")["preco_m2"].mean().reset_index()
    mediana_ano = base.groupby("ano")["preco_m2"].median().reset_index(name="mediana")
    ano_mais_caro = int(por_ano.loc[por_ano["preco_m2"].idxmax(), "ano"])
    ano_mais_barato = int(por_ano.loc[por_ano["preco_m2"].idxmin(), "ano"])

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_bar_ano = px.bar(
            por_ano,
            x="ano",
            y="preco_m2",
            labels={"ano": "Ano", "preco_m2": "Preço médio (R$/m²)"},
            title="Preço médio por ano"
        )
        st.plotly_chart(fig_bar_ano, use_container_width=True)

    with col_g2:
        fig_box = px.box(
            base,
            x="ano",
            y="preco_m2",
            points="all",
            labels={"ano": "Ano", "preco_m2": "Preço (R$/m²)"},
            title="Distribuição dos preços por ano"
        )
        st.plotly_chart(fig_box, use_container_width=True)

    med_mais_caro = mediana_ano.loc[mediana_ano["ano"] == ano_mais_caro, "mediana"].iloc[0]
    med_mais_barato = mediana_ano.loc[mediana_ano["ano"] == ano_mais_barato, "mediana"].iloc[0]

    texto_ano = (
        f"No gráfico de barras, comparamos o preço médio por ano. Em {ano_mais_caro}, "
        f"o valor médio ficou mais alto, em torno de R$ {formata_valor(med_mais_caro)}, "
        f"enquanto em {ano_mais_barato} os preços foram mais baixos, perto de R$ {formata_valor(med_mais_barato)}. "
        "Isso ajuda a enxergar em quais anos o mercado esteve mais pressionado ou mais confortável em termos de valor."
    )
    texto_box = (
        "Já o boxplot resume a distribuição dos preços em cada ano. "
        "A linha dentro de cada caixa mostra o valor que fica bem no meio da amostra (a mediana). "
        "Caixas mais altas indicam anos mais caros; caixas mais baixas indicam anos mais baratos. "
        "Os pontos que aparecem fora da caixa são meses que fugiram do padrão, funcionando como valores mais extremos."
    )
    st.markdown(f"**Como interpretar esses dois gráficos:** {texto_ano} {texto_box}")

    # pizza + barras por faixa
    st.markdown("### 🔍 Análise exploratória da distribuição de preços")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        fig_pizza = px.pie(
            base,
            names="faixa_preco_str",
            title="Distribuição de observações por faixa de preço (R$/m²)",
            hole=0.35,
        )
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_p2:
        contagem_faixas = base["faixa_preco_str"].value_counts().reset_index()
        contagem_faixas.columns = ["faixa_preco_str", "qtd"]
        fig_barras_faixa = px.bar(
            contagem_faixas,
            x="faixa_preco_str",
            y="qtd",
            labels={
                "faixa_preco_str": "Faixa de preço (R$/m²)",
                "qtd": "Número de observações"
            },
            title="Número de observações por faixa de preço",
        )
        st.plotly_chart(fig_barras_faixa, use_container_width=True)

    texto_faixas = (
        "Na pizza e no gráfico de barras, cada fatia representa um intervalo de preços. "
        "As faixas com barras maiores são aquelas onde aparecem mais contratos. "
        f"No período analisado em {cidade_sel}, observamos que uma dessas faixas concentra cerca de {perc_dom_str}% "
        "de todas as observações, o que indica em qual nível de preço o mercado costuma se organizar."
    )
    st.caption(texto_faixas)

    # estatísticas descritivas
    st.markdown("### 📊 Estatísticas descritivas da cidade selecionada")
    descr = base["preco_m2"].describe().rename(
        index={
            "count": "Qtd observações",
            "mean": "Média",
            "std": "Desvio padrão",
            "min": "Mínimo",
            "25%": "1º quartil",
            "50%": "Mediana",
            "75%": "3º quartil",
            "max": "Máximo",
        }
    )
    st.table(descr.to_frame("R$/m²").style.format("{:.2f}"))

    with st.expander("📋 Ver dados detalhados do período"):
        st.dataframe(
            base[["data", "preco_m2"]]
            .sort_values("data")
            .rename(columns={"data": "Data", "preco_m2": "Preço (R$/m²)"})
            .reset_index(drop=True)
        )

    # PDF
    st.markdown("### 📄 Exportar relatório em PDF")

    resumo_kpis = {
        "Preço atual (R$/m²)": f"R$ {preco_atual_str}",
        "Média no período": f"R$ {preco_medio_str}",
        "Mínimo no período": f"R$ {formata_valor(minimo)}",
        "Máximo no período": f"R$ {formata_valor(maximo)}",
        "Variação acumulada": f"{variacao_pct_str}%",
    }

    pdf_bytes = gerar_pdf_relatorio(
        cidade_sel,
        mercado_sel,
        base,
        resumo_kpis,
        texto_resumo
    )

    st.download_button(
        label="⬇️ Baixar relatório em PDF",
        data=pdf_bytes,
        file_name=f"relatorio_{cidade_sel}_{mercado_sel}.pdf",
        mime="application/pdf"
    )

    if st.button("🎧 Ouvir resumo e indicadores"):
        ler_texto_em_voz_alta(texto_relatorio_acessivel(texto_resumo, resumo_kpis))


# -------------------- Main --------------------
def main():
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
    if "basic_auth" not in st.session_state:
        st.session_state["basic_auth"] = False

    if not st.session_state["auth"]:
        mostrar_login()
        return

    st.title("🏠 PredImóveis")
    st.caption("Dashboard acadêmico de análise e previsão de preços de imóveis.")

    st.sidebar.markdown("### 👤 Sessão")
    if st.sidebar.button("Sair"):
        st.session_state["auth"] = False
        st.session_state["basic_auth"] = False
        st.rerun()

    aba = st.sidebar.radio(
        "Navegar por:",
        [
            "📊 Visualização de Dados",
            "🤖 Previsões Inteligentes",
            "📑 Relatórios e PDF",
        ],
        index=0
    )

    df_hist = carregar_dados_historicos()
    pacote_prev = carregar_snapshot_previsoes()

    if aba.startswith("📊"):
        painel_dashboard(df_hist)
    elif aba.startswith("🤖"):
        painel_previsoes(pacote_prev)
    elif aba.startswith("📑"):
        painel_relatorios(df_hist)

    st.markdown("---")
    st.caption(
        "Protótipo acadêmico. A aplicação utiliza recursos de acessibilidade, como síntese de voz (gTTS), "
        "além de modelos estatísticos (SARIMA) para previsão de preços."
    )


if __name__ == "__main__":
    main()