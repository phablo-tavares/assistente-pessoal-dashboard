import streamlit as st
import os   

def load_css(filaPath):
    """
    Função para carregar um arquivo CSS externo e aplicá-lo à aplicação.
    """
    try:
        with open(filaPath) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

current_dir = os.path.dirname(__file__)
# --- Funções de Lógica de Negócio ---

def getAllClientsData():
    if "allClientsData" not in st.session_state:
        st.session_state.allClientsData = []
    
    with st.spinner("Carregando dados dos clientes..."):
        clientsData = st.session_state.supabaseClient.getAllClientData()
        st.session_state.allClientsData = clientsData

def toggleSubscriptionStatus(clientId:int, newStatus:bool, clientName:str):
    try:
        # A atualização visual é feita no callback para ser instantânea
        for client in st.session_state.allClientsData:
            if client['id'] == clientId:
                client['active_subscription'] = newStatus
                break
        
        # A chamada ao backend é feita em seguida
        st.session_state.supabaseClient.updateClientSubscriptionStatus(clientId=clientId, newStatus=newStatus)
        
        status_text = "ativada" if newStatus else "desativada"
        st.toast(f"Assinatura de {clientName} foi {status_text}.")
        
    except Exception as e:
        st.toast(f'Erro ao alterar a assinatura de {clientName}. Tente novamente.')
        # Reverte a mudança visual em caso de erro
        for client in st.session_state.allClientsData:
            if client['id'] == clientId:
                client['active_subscription'] = not newStatus
                break
        st.rerun()

# --- Componente Principal da Tela ---
def managementDashboard():
    css_path = os.path.join(current_dir, "..", "styles", "management_dashboard.css")
    load_css(css_path)
    st.title("Gerenciamento de Usuários")
    
    if "allClientsData" not in st.session_state or not st.session_state.allClientsData:
        getAllClientsData()

    # Layout do Cabeçalho da Tabela
    header_cols = st.columns([2, 2, 2, 1])
    header_cols[0].markdown("**Nome**")
    header_cols[1].markdown("**CPF**")
    header_cols[2].markdown("**Telefone**")
    header_cols[3].markdown("**Status Assinatura**")
    st.divider()

    if not st.session_state.allClientsData:
        st.info("Nenhum cliente encontrado.")
    else:
        for client in st.session_state.allClientsData:
            row_cols = st.columns([2, 2, 2, 1])
            with row_cols[0]:
                st.write(client.get('full_name', '-'))
            with row_cols[1]:
                st.write(client.get('cpf', '-'))
            with row_cols[2]:
                st.write(client.get('phone_number', '-'))
            with row_cols[3]:
                st.toggle(
                    label='',
                    key=f"toggle_{client['id']}",
                    value=client.get('active_subscription', False),
                    on_change=toggleSubscriptionStatus,
                    args=(client['id'], not client.get('active_subscription', False), client.get('full_name')),
                    label_visibility="collapsed"
                )