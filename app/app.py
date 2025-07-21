import streamlit as st
from datetime import date, timedelta
from supabase_client import SupabaseClient

# Import das telas
from auth.authScreen import authScreen
from auth.redefinePasswordScreen import redefinePasswordScreen
from home.userDashboard import homePage
from home.editPersonalDataPage import editPersonalDataPage
from home.managementDashboard import managementDashboard
import constants

st.set_page_config(
    layout="wide",
    page_title=constants.APP_TITLE,
    page_icon=None,
    initial_sidebar_state="collapsed"
)

# --- Gerenciamento de Estado Global ---
if "supabaseClient" not in st.session_state:
    st.session_state.supabaseClient = SupabaseClient()

# Estado do Usuário
if "currentUser" not in st.session_state:
    st.session_state.currentUser = None
if "clientData" not in st.session_state:
    st.session_state.clientData = None

# Estado dos Dados de Gastos
if "clientSpendings" not in st.session_state:
    st.session_state.clientSpendings = []
if "spendingDataFetched" not in st.session_state:
    st.session_state.spendingDataFetched = False
if "startDate" not in st.session_state:
    st.session_state.startDate = date.today() - timedelta(days=30)
if "endDate" not in st.session_state:
    st.session_state.endDate = date.today()

# Estado dos Gráficos e Visualização
if "user_map" not in st.session_state:
    st.session_state.user_map = {}
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "personal"

# Estado do Fluxo de Autenticação/Senha
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'refresh_token' not in st.session_state:
    st.session_state.refresh_token = None
if 'redefine_password_flux' not in st.session_state:
    st.session_state.redefine_password_flux = False

# Captura de tokens para redefinição de senha
access_token = st.query_params.get("access_token")
refresh_token = st.query_params.get("refresh_token")
if access_token and refresh_token and not st.session_state.redefine_password_flux:
    st.session_state.redefine_password_flux = True
    st.session_state.access_token = access_token
    st.session_state.refresh_token = refresh_token

# --- Roteador Principal da Aplicação ---
def main():
    if st.session_state.redefine_password_flux:
        redefinePasswordScreen()
    elif st.session_state.currentUser:
        with st.sidebar:
            pagina_selecionada = st.radio(
                "",
                ("Dashboard", "Editar Dados Pessoais")
            )
            st.markdown("<br>", unsafe_allow_html=True)
            if st.sidebar.button("Sair"):
                # Limpa tudo ao sair para garantir um estado limpo no próximo login
                keys_to_keep = [] 
                for key in st.session_state.keys():
                    if key not in keys_to_keep:
                        del st.session_state[key]
                st.rerun()
                
        if pagina_selecionada == "Dashboard":
            # Rota especial para o admin
            if st.session_state.currentUser.email == 'agentepessoalcarpia@gmail.com':
                managementDashboard()
            else:
                homePage()
        elif pagina_selecionada == "Editar Dados Pessoais":
            editPersonalDataPage()
    else:
        authScreen()

if __name__ == "__main__":
    main()