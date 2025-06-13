import streamlit as st
import random

# --- Configuração da página
st.set_page_config(page_title="Login - Preditor Imobiliário", layout="centered")

# --- Título principal
st.markdown("""
<div style="text-align:center">
    <h1>🏠 Preditor de Preços Imobiliários Regionais</h1>
</div>
""", unsafe_allow_html=True)

# --- Estado da sessão
if 'login_etapa' not in st.session_state:
    st.session_state.login_etapa = 'login'
if 'codigo_mfa' not in st.session_state:
    st.session_state.codigo_mfa = ''
if 'mostrar_codigo' not in st.session_state:
    st.session_state.mostrar_codigo = False
if 'usuario_autenticado' not in st.session_state:
    st.session_state.usuario_autenticado = False

# --- Função MFA
def gerar_codigo_mfa():
    return str(random.randint(100000, 999999))

# --- Etapa 1: Login
if st.session_state.login_etapa == 'login':
    with st.container():
        st.subheader("🔐 Acesso Restrito")
        st.markdown("Informe suas credenciais para continuar.")

        with st.form("login_form"):
            usuario = st.text_input("Usuário", placeholder="Digite seu nome de usuário")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            enviar_login = st.form_submit_button("➡️ Entrar")

            if enviar_login:
                if usuario == "admin" and senha == "admin":
                    st.session_state.codigo_mfa = gerar_codigo_mfa()
                    st.session_state.login_etapa = 'mfa'
                    st.session_state.mostrar_codigo = False
                else:
                    st.error("❌ Usuário ou senha inválidos.")

# --- Etapa 2: MFA
elif st.session_state.login_etapa == 'mfa':
    st.subheader("🔑 Verificação em Duas Etapas (MFA)")

    if not st.session_state.mostrar_codigo:
        st.info("Clique no botão abaixo para receber seu código MFA.")
        if st.button("📩 Receber Código MFA", use_container_width=True):
            st.session_state.mostrar_codigo = True
    else:
        with st.expander("📬 Código MFA Recebido", expanded=True):
            st.markdown(f"### ✉️ Seu código é: `{st.session_state.codigo_mfa}`")

    st.markdown("---")

    with st.form("mfa_form"):
        codigo_input = st.text_input("🔎 Digite o código recebido")
        col1, col2 = st.columns(2)
        with col1:
            verificar = st.form_submit_button("✅ Verificar Código")
        with col2:
            voltar = st.form_submit_button("🔄 Voltar")

        if verificar:
            if codigo_input == st.session_state.codigo_mfa:
                st.success("Código verificado com sucesso!")
                st.session_state.usuario_autenticado = True
                st.session_state.login_etapa = 'autenticado'
            else:
                st.error("Código incorreto. Tente novamente.")

        if voltar:
            st.session_state.login_etapa = 'login'
            st.session_state.codigo_mfa = ''
            st.session_state.mostrar_codigo = False

# --- Etapa 3: Autenticado
elif st.session_state.usuario_autenticado:
    st.balloons()
    st.markdown("## Bem-vindo, administrador!")

    st.markdown("___")
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.login_etapa = 'login'
        st.session_state.usuario_autenticado = False
        st.session_state.codigo_mfa = ''
        st.session_state.mostrar_codigo = False
