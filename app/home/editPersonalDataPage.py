import streamlit as st
import re
from home.userDashboard import getCurrentClientData # Reutiliza a função de busca
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

def getHtmlString(htmlFileName:str):
    htmlFolderPath = os.path.join(current_dir, "..", "static/html")
    with open(f"{htmlFolderPath}/{htmlFileName}", 'r', encoding='utf-8') as f:
        htmlContent = f.read()
        return htmlContent

# --- Funções de Validação e Formatação ---
def formatNumericWhatsappEditPersonalData():
    key = 'whatsapp_number_input_edit_personal_data'
    if key in st.session_state:
        st.session_state[key] = re.sub(r'[^0-9]', '', st.session_state[key])

def formatNumericCpfEditPersonalData():
    key = 'cpf_input_edit_personal_data'
    if key in st.session_state:
        st.session_state[key] = re.sub(r'[^0-9]', '', st.session_state[key])

def isWhatsappValid(whatsapp:str):
    return len(whatsapp) >= 7

def isCPFValid(cpf:str):
    return len(cpf) == 11

def isWhatsappInUseByOtherUser(whatsapp:str):
    if st.session_state.clientData and st.session_state.clientData.get('phone_number') == whatsapp:
        return False # É o número do próprio usuário
    return st.session_state.supabaseClient.phoneNumberAlreadyInUse(phoneNumber=whatsapp)

def isSpendingsSharingKeyValid(key:str):
    if not key: # Chave vazia é válida (para sair de um grupo)
        return True
    return len(key) >= 8 and " " not in key

# --- Função de Ação ---
def doUpdatePersonalData(fullName:str, whatsappNumber:str, cpf:str, spendingsSharingKey:str):
    error = False
    if not isWhatsappValid(whatsapp=whatsappNumber):
        st.toast('Número de whatsapp deve ter 7 ou mais números')
        error = True
    if isWhatsappInUseByOtherUser(whatsapp=whatsappNumber):
        st.toast('Número de whatsapp já cadastrado por outro usuário')
        error = True
    if not isCPFValid(cpf=cpf):
        st.toast('CPF deve conter 11 números')
        error = True
    if not isSpendingsSharingKeyValid(key=spendingsSharingKey):
        st.toast('Chave de compartilhamento deve ter 8+ caracteres e não conter espaços')
        error = True
        
    if not error:
        try:
            with st.spinner("Salvando alterações..."):
                st.session_state.supabaseClient.updateClientData(
                    phoneNumber=whatsappNumber,
                    fullName=fullName,
                    cpf=cpf,
                    authUserId=st.session_state.currentUser.id,
                    active_subscription=None, # Não altera a assinatura aqui
                    spendingsSharingKey=spendingsSharingKey.strip() or None, # Garante que seja None se vazio
                )
            getCurrentClientData() # Atualiza os dados na sessão
            st.success("Dados pessoais atualizados com sucesso!")
        except Exception as e:
            st.error('Erro ao atualizar dados. Tente novamente mais tarde.')

# --- Componente Principal da Tela ---
def editPersonalDataPage():
    css_path = os.path.join(current_dir, "..", "styles", "profile_styles.css")
    load_css(css_path)

    # Garante que os dados do cliente estejam carregados
    if not st.session_state.clientData:
        getCurrentClientData()

    with st.container(key="profile-container"):    
        with st.container(key="edit-personal-data-fields"):
            if not st.session_state.clientData:
                st.error("Não foi possível carregar os dados. Tente novamente mais tarde.")
                return
            
            st.markdown(getHtmlString("personalDataElement.html"),unsafe_allow_html=True)
            
            fullName = st.text_input(
                label="Nome Completo *",
                value=st.session_state.clientData.get('full_name', ''),
                help='Como você gostaria de ser identificado no app',
                icon=":material/person:"
            )
            whatsappNumber = st.text_input(
                label="Número do Whatsapp * (Apenas Números)",
                key="whatsapp_number_input_edit_personal_data",
                value=st.session_state.clientData.get('phone_number', ''),
                help='Usado para integração com o chatbot de gastos',
                max_chars=18,
                on_change=formatNumericWhatsappEditPersonalData,
                icon=":material/phone_enabled:",
                placeholder="5562982354789"
            )
            cpf = st.text_input(
                label="CPF * (apenas números)",
                key="cpf_input_edit_personal_data",
                value=st.session_state.clientData.get('cpf', ''),
                help="Documento de identificação",
                max_chars=11,
                on_change=formatNumericCpfEditPersonalData,
                icon=":material/id_card:",
                placeholder="11122233344",
            )
            spendingsSharingKey = st.text_input(
                label="Chave de Compartilhamento de Gastos",
                value=st.session_state.clientData.get('spendings_sharing_key', '') or '',
                help="Código único para compartilhar gastos no modo Conjunto. Compartilhe esta chave com familiares ou parceiros.",
                icon=":material/ios_share:"
            )
            
            saveButton = st.button("Salvar Alerações")
            if saveButton:
                doUpdatePersonalData(
                    fullName=fullName,
                    whatsappNumber=whatsappNumber,
                    cpf=cpf,
                    spendingsSharingKey=spendingsSharingKey
                )

        with st.container(key="sharing-key-description"):
            st.markdown('<br>',unsafe_allow_html=True)
            st.markdown("<h3 style='font-size:24px; padding-top:0px; margin-top:0px;'>Sobre o Modo Conjunto</h3>",unsafe_allow_html=True)
            st.markdown("<p style='font-size:14px; line-height: 20px;'>• O modo <b>Conjunto</b> permite visualizar gastos compartilhados entre múltiplos usuários</p>",unsafe_allow_html=True)
            st.markdown("<p style='font-size:14px; line-height: 20px;'>• Use a <b>Chave de Compartilhamento</b> para conectar contas familiares</p>",unsafe_allow_html=True)
            st.markdown("<p style='font-size:14px; line-height: 20px;'>• No modo <b>Meus Gastos</b>, apenas seus gastos pessoais são exibidos</p>",unsafe_allow_html=True)
            st.markdown("<p style='font-size:14px; line-height: 20px;'>• As transações são sincronizadas automaticamente via chatbot do WhatsApp</p>",unsafe_allow_html=True)