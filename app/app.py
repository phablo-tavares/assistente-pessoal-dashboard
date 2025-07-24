import streamlit as st
from datetime import date, timedelta
from supabase_client import SupabaseClient

# Import das telas
from auth.authScreen import authScreen
from auth.redefinePasswordScreen import redefinePasswordScreen
from home.userDashboard import userDashboard
from home.editPersonalDataPage import editPersonalDataPage
from home.managementDashboard import managementDashboard
import constants
import os
from streamlit_option_menu import option_menu

st.set_page_config(
    layout="wide",
    page_title=constants.APP_TITLE,
    page_icon=":material/bar_chart:",
    initial_sidebar_state="collapsed",
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
        if st.sidebar.button("Sair"):
            st.session_state.supabaseClient.signOut()
            st.session_state.clear()
            st.rerun()
        with st.container(key='main-container'):
            if st.session_state.currentUser.email == 'agentepessoalcarpia@gmail.com':
                managementDashboard()
            else:
                st.markdown("<div id='app-logo-header'><h3>Agente Pessoal</h3><div>", unsafe_allow_html=True)
                optionMenu = option_menu(
                    menu_title=None,
                    options=[
                        "Visão Geral",
                        "Perfil",
                    ],
                    icons=[
                        "bar-chart-line",
                        "person",
                    ],
                    default_index=0,
                    orientation='horizontal',
                    styles={
                        "container": {"padding": "10!important", "background":"white","border-radius": "22px",},
                        "icon": {"font-size": "18px"}, 
                        "nav-link": {"border-radius": "12px", "font-size": "18px", "text-align": "center", "margin":"0px", "--hover-color": "white","padding": "15px"},
                        "nav-link-selected": {"background": "linear-gradient(135deg, hsl(20 100% 55%) 0%, hsl(25 100% 60%) 100%)"},
                    }
                )
                if optionMenu == "Visão Geral":
                    userDashboard()
                elif optionMenu == "Perfil":
                    editPersonalDataPage()

    else:
        authScreen()

if __name__ == "__main__":
    main()