import streamlit as st

def load_css(file_name):
    """
    Função para carregar um arquivo CSS externo e aplicá-lo à aplicação.
    """
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def doRedefinePassword(password:str):
    if len(password) < 6:
        st.warning("A senha deve conter 6 ou mais dígitos.")
        return
        
    try:
        with st.spinner("Redefinindo senha..."):
            st.session_state.supabaseClient.resetPassword(
                password=password,
                access_token=st.session_state.access_token,
                refresh_token=st.session_state.refresh_token
            )
        st.session_state.redefine_password_flux = False
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.success('Senha redefinida com sucesso! Você já pode fazer o login.')

    except Exception as e:
        st.error('Link de redefinição de senha expirado ou inválido. Por favor, solicite um novo.')

def redefinePasswordScreen():
    with st.container(key='auth-component-container'):
        load_css("app/styles/login_style.css")
        st.title("Agente Pessoal - by Carp.IA")
        st.subheader("Crie sua nova senha")
        password = st.text_input("Nova Senha", type="password")
        redefineButton = st.button("Redefinir Senha")
        if redefineButton:
            doRedefinePassword(password=password)