import streamlit as st
import time
import pandas as pd
import plotly.express as px
import os
import random

# ---------------------- CONFIG GERAL ----------------------
st.set_page_config(page_title="Preditor Imobiliário", layout="wide")

# ---------------------- ESTADO DA SESSÃO ----------------------
estado_inicial = {
    'login_etapa': 'login',
    'codigo_mfa': '',
    'mostrar_codigo': False,
    'usuario_autenticado': False,
    'verificacao_mfa_sucesso': False
}

for chave, valor in estado_inicial.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor

# ---------------------- FUNÇÕES DE AUTENTICAÇÃO ----------------------
def gerar_codigo_mfa():
    return str(random.randint(100000, 999999))

def exibir_login():
    st.markdown("""
    <div style="text-align:center">
        <h1>🏠 Preditor de Preços Imobiliários Regionais</h1>
    </div>
    """, unsafe_allow_html=True)
    st.subheader("🔐 Acesso Restrito")
    with st.form("login_form"):
        usuario = st.text_input("Usuário", placeholder="Digite seu nome de usuário")
        senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        if st.form_submit_button("➡️ Entrar"):
            if usuario == "admin" and senha == "admin":
                st.session_state.codigo_mfa = gerar_codigo_mfa()
                st.session_state.login_etapa = 'mfa'
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")
    st.stop()

def exibir_mfa():
    st.subheader("🔑 Verificação em Duas Etapas (MFA)")

    if not st.session_state.mostrar_codigo:
        if st.button("📩 Receber Código MFA"):
            st.session_state.mostrar_codigo = True
            st.rerun()
    else:
        st.markdown(f"### ✉️ Seu código é: `{st.session_state.codigo_mfa}`")

    with st.form("mfa_form"):
        codigo_input = st.text_input("Digite o código recebido")

        col1, col2 = st.columns(2)
        with col1:
            verificar = st.form_submit_button("✅ Verificar Código")
        with col2:
            voltar = st.form_submit_button("🔄 Voltar")

        if verificar:
            if not codigo_input.strip():
                st.warning("⚠️ O campo de código está vazio.")
            elif codigo_input == st.session_state.codigo_mfa:
                st.success("✅ Código verificado com sucesso!")
                time.sleep(2)
                st.session_state.usuario_autenticado = True
                st.session_state.login_etapa = 'autenticado'
                st.rerun()
            else:
                st.error("❌ Código incorreto. Tente novamente.")

        if voltar:
            for chave in ['login_etapa', 'codigo_mfa', 'mostrar_codigo']:
                st.session_state[chave] = estado_inicial[chave]
            st.rerun()
        if voltar:
            for chave in ['login_etapa', 'codigo_mfa', 'mostrar_codigo']:
                st.session_state[chave] = estado_inicial[chave]
            st.rerun()


    st.stop()

# ---------------------- DADOS ----------------------
DATA_DIR = "data"

cidades_arquivos = {
    "Locação": {
        "Aracaju": "dados_locacao_aracaju_tratado.csv",
        "Fortaleza": "dados_locacao_fortaleza_tratado.csv",
        "João Pessoa": "dados_locacao_joao_pessoa_tratado.csv",
        "Maceió": "dados_locacao_maceio_tratado.csv",
        "Natal": "dados_locacao_natal_tratado.csv",
        "Recife": "dados_locacao_recife_tratado.csv",
        "Salvador": "dados_locacao_salvador_tratado.csv",
        "São Luís": "dados_locacao_sao_luis_tratado.csv",
        "Teresina": "dados_locacao_teresina_tratado.csv"
    },
    "Venda": {
        "Aracaju": "dados_vendas_aracaju_tratados.csv",
        "Fortaleza": "dados_vendas_fortaleza_tratados.csv",
        "João Pessoa": "dados_vendas_joao_pessoa_tratados.csv",
        "Maceió": "dados_vendas_maceio_tratados.csv",
        "Natal": "dados_vendas_natal_tratados.csv",
        "Recife": "dados_vendas_recife_tratados.csv",
        "Salvador": "dados_vendas_salvador_tratados.csv",
        "São Luís": "dados_vendas_sao_luis_tratados.csv",
        "Teresina": "dados_vendas_teresina_tratados.csv"
    }
}

colunas_corretas = {
    'Preço médio (R$/m²) Total': 'Preço médio (R$/m²)Total',
    'Preço médio (R$/m²)Total ': 'Preço médio (R$/m²)Total',
    ' Preço médio (R$/m²)Total': 'Preço médio (R$/m²)Total'
}

def carregar_dados(caminho):
    df = pd.read_csv(caminho, sep=';')
    df.rename(columns=colunas_corretas, inplace=True)
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df.dropna(subset=['Data'], inplace=True)
    return df

def gerar_grafico_imobiliario(df, cidade, metrica):
    if "variação" in metrica.lower():
        fig = px.bar(df, x='Data', y=metrica, title=f"{metrica} - {cidade}")
    else:
        fig = px.line(df, x='Data', y=metrica, title=f"{metrica} - {cidade}", markers=True)
    return fig

def gerar_grafico_bcb(df, indicador):
    df_filtrado = df[df['Indicador'] == indicador].copy()
    df_filtrado['Data'] = pd.to_datetime(df_filtrado['Data'], errors='coerce')
    for col in ['Media', 'Mediana', 'DesvioPadrao', 'Minimo', 'Maximo']:
        df_filtrado[col] = df_filtrado[col].str.replace(',', '.').astype(float)
    fig = px.line(df_filtrado, x='Data', y=['Media', 'Mediana', 'Minimo', 'Maximo'],
                  title=f"Indicador: {indicador}",
                  labels={"value": "Valor", "variable": "Métrica"})
    return fig, df_filtrado

def painel_projecoes():
    st.subheader("📈 Projeção de Preço Médio até 2027")
    data = {
        "Cidade": ["São Luís", "Recife", "Natal", "Fortaleza", "Salvador", "João Pessoa", "Maceió", "Teresina", "Aracaju"],
        "Preço 2025": [10500, 10300, 10558, 10762, 9980, 8950, 7600, 6200, 5860],
        "Preço 2027": [12400, 12200, 12158, 12462, 11900, 10650, 8800, 7300, 6700],
        "Crescimento (%)": [10.0, 9.7, 9.5, 9.0, 9.3, 8.8, 7.0, 6.5, 5.5],
        "Acima do IPCA (8%)": [True, True, True, True, True, True, False, False, False],
        "Acima do IGP-M (10%)": [False]*9
    }
    df = pd.DataFrame(data)
    df["Destaque"] = df["Cidade"]
    df.loc[df["Acima do IGP-M (10%)"], "Destaque"] += " ★★★"
    df.loc[(df["Acima do IPCA (8%)"]) & (~df["Acima do IGP-M (10%)"]), "Destaque"] += " ★★"
    df.loc[(~df["Acima do IPCA (8%)"]), "Destaque"] += " ★"
    df = df.sort_values(by="Preço 2027", ascending=False)
    fig = px.bar(df, x="Destaque", y="Preço 2027", color="Crescimento (%)", text="Preço 2027",
                 color_continuous_scale="Blues",
                 title="🏠 Projeção de Preço Médio Venda (R$/m²) - 2027")
    fig.update_traces(texttemplate='R$%{text:,.0f}', textposition='outside')
    fig.update_layout(showlegend=False, height=500, width=900,
                      font=dict(family="Arial", size=12),
                      xaxis_title="Cidades (★ = Acima do IPCA | ★★★ = Acima do IGP-M)",
                      yaxis_title="Preço Médio Venda (R$/m²) - 2027")
    st.plotly_chart(fig)

    st.subheader("📄 Dados Usados")
    st.dataframe(df.set_index("Cidade")[["Preço 2025", "Preço 2027", "Crescimento (%)"]])

# ---------------------- MAIN ----------------------

def main():
    if st.session_state.login_etapa == 'login':
        exibir_login()
    elif st.session_state.login_etapa == 'mfa':
        exibir_mfa()

    if not st.session_state.usuario_autenticado:
        st.warning("⚠️ Acesso restrito. Faça login para visualizar o dashboard.")
        st.stop()

    st.title("🏠 Dashboard de Preços de Imóveis")
    painel = st.sidebar.selectbox("Escolha o painel", ["Mercado Imobiliário", "Indicadores Econômicos", "Projeções de Crescimento"])

    if painel == "Mercado Imobiliário":
        sub_tipo = st.sidebar.selectbox("Tipo de mercado", list(cidades_arquivos.keys()))
        cidade = st.sidebar.selectbox("Cidade", list(cidades_arquivos[sub_tipo].keys()))
        caminho = os.path.join(DATA_DIR, cidades_arquivos[sub_tipo][cidade])
        try:
            df = carregar_dados(caminho)
            metricas = [col for col in df.columns if any(m in col.lower() for m in ['preço', 'var.', 'número'])]
            metrica = st.sidebar.selectbox("Métrica", metricas)
            fig = gerar_grafico_imobiliario(df, cidade, metrica)
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("Ver dados brutos"):
                st.dataframe(df)
        except Exception as e:
            st.error(f"Erro: {e}")

    elif painel == "Indicadores Econômicos":
        caminho = os.path.join(DATA_DIR, "dados_banco_central.csv")
        try:
            df = carregar_dados(caminho)
            indicador = st.sidebar.selectbox("Indicador", df['Indicador'].unique())
            fig, df_filt = gerar_grafico_bcb(df, indicador)
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("Ver dados brutos"):
                st.dataframe(df_filt)
        except Exception as e:
            st.error(f"Erro: {e}")

    elif painel == "Projeções de Crescimento":
        painel_projecoes()

if __name__ == "__main__":
    main()
