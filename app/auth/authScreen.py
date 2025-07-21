import streamlit as st
from email_validator import validate_email
import re

def load_css(file_name):
    """
    Função para carregar um arquivo CSS externo e aplicá-lo à aplicação.
    """
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo CSS '{file_name}' não encontrado. Verifique o caminho.")


# --- Funções de Validação ---
def isEmailValid(email:str) -> bool:
    try:
        validate_email(email,check_deliverability=False) # check_deliverability=False para agilidade
        return True
    except:
        return False

def isPasswordValid(password:str) ->bool:
    return len(password) >= 6

def isWhatsappInUseByOtherUser(whatsapp:str):
    if st.session_state.clientData:
        phoneNumberBelongsToCurrentUser = st.session_state.clientData['phone_number'] == whatsapp
        if phoneNumberBelongsToCurrentUser:
            return False
    
    try:
        phoneNumberAlreadyInUse = st.session_state.supabaseClient.phoneNumberAlreadyInUse(phoneNumber=whatsapp)
        return phoneNumberAlreadyInUse
    except Exception as e:
        st.error("Erro ao verificar o número de WhatsApp. Tente novamente.")
        return True # Previne o cadastro em caso de erro

def isWhatsappValid(whatsapp:str):
    return len(whatsapp) >= 7

def isCPFValid(cpf:str):
    return len(cpf) == 11

# --- Funções de Ação ---
def doSignUp(email:str, password: str, fullName:str, whatsapp:str,cpf:str):
    if not email or not password or not fullName or not cpf or not whatsapp:
        st.warning('Preencha todos os campos')
        return

    validEmail = isEmailValid(email=email)
    validPassword = isPasswordValid(password=password)
    validWhatsapp = isWhatsappValid(whatsapp=whatsapp)
    validCPF = isCPFValid(cpf=cpf)
    whatsappInUse = isWhatsappInUseByOtherUser(whatsapp=whatsapp)

    # Validações com feedback para o usuário
    error = False
    if not validEmail:
        st.toast('Email inválido')
        error = True
    if not validPassword:
        st.toast('Senha deve conter 6 ou mais dígitos')
        error = True
    if not validWhatsapp:
        st.toast('Número de whatsapp deve ter 7 ou mais números')
        error = True
    if whatsappInUse:
        st.toast('Número de whatsapp já cadastrado')
        error = True
    if not validCPF:
        st.toast('CPF deve conter 11 números')
        error = True
    
    if error:
        return

    try:
        with st.spinner("Realizando cadastro..."):
            response = st.session_state.supabaseClient.signUp(email, password)
            user = response.user
            if user:
                st.session_state.supabaseClient.updateClientData(
                    phoneNumber=whatsapp,
                    fullName=fullName,
                    cpf=cpf,
                    authUserId=user.id,
                    active_subscription=False,
                    spendingsSharingKey=None
                )
                st.success("Cadastro feito com sucesso. Por favor, clique no link de confirmação enviado para seu email e após a validação, faça o login!")
    except Exception as e:
        st.error('Erro no cadastro. Verifique se o e-mail já está em uso ou tente novamente mais tarde.')


def doLogin(email:str, password: str):
    if not email or not password:
        st.warning('Preencha todos os campos')
        return
        
    validEmail = isEmailValid(email=email)
    if not validEmail:
        st.toast('Email inválido')
        return

    try:
        with st.spinner("Entrando..."):
            user = st.session_state.supabaseClient.signIn(email, password)
            if user:
                st.session_state.currentUser = user
                st.rerun()
    except Exception as e:
        error_message = str(e)
        if 'Invalid login credentials' in error_message:
            st.error('Credenciais inválidas! Verifique o email e a senha e tente novamente.')
        elif 'Email not confirmed' in error_message:
             st.error('Email não verificado! Por favor, cheque sua caixa de email e após a verificação faça o login.')
        else:
            st.error('Erro no login, tente novamente mais tarde.')

def doSendResetPasswordEmail(email:str):
    if not email:
        st.warning('Preencha o email')
        return
        
    validEmail = isEmailValid(email=email)
    if not validEmail:
        st.toast('Email inválido')
        return
        
    try:
        with st.spinner("Enviando email..."):
            st.session_state.supabaseClient.sendResetPasswordEmail(email=email)
        st.success('Email para redefinição de senha enviado. Acesse sua caixa de entrada e clique no link.')
    except Exception as e:
        st.error('Erro ao enviar e-mail. Tente novamente mais tarde.')

# --- Funções de Formatação de Input ---
def format_numeric_whatsapp():
    if 'whatsapp_number_input' in st.session_state:
        cleaned_whatsapp = re.sub(r'[^0-9]', '', st.session_state.whatsapp_number_input)
        st.session_state.whatsapp_number_input = cleaned_whatsapp

def format_numeric_cpf():
    if 'cpf_input' in st.session_state:
        cleaned_cpf = re.sub(r'[^0-9]', '', st.session_state.cpf_input)
        st.session_state.cpf_input = cleaned_cpf

# --- Componente Principal da Tela ---
def authScreen():
    load_css("app/style.css") 
    st.title("Agente Pessoal - by Carp.IA")
    option = st.radio(label="", options=["Login", "Cadastro", "Esqueci minha senha"], horizontal=True, label_visibility="collapsed")

    if option == "Login":
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        loginButton = st.button("Login")
        if loginButton:
            doLogin(email=email,password=password)

    elif option == "Cadastro":
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        fullName = st.text_input("Nome Completo")
        whatsappNumber = st.text_input(
            "Número Whatsapp (apenas números)",
            key="whatsapp_number_input",
            placeholder="5562987532165",
            max_chars=18,
            on_change=format_numeric_whatsapp,
        )
        cpf = st.text_input(
            "CPF (apenas números)",
            key="cpf_input",
            placeholder="11122233344",
            max_chars=11,
            on_change=format_numeric_cpf,
        )
        signUpButton = st.button("Cadastrar")
        if signUpButton:
            doSignUp(email=email,password=password,fullName=fullName,whatsapp=whatsappNumber,cpf=cpf)

    elif option == "Esqueci minha senha":
        email = st.text_input("Email")
        sendResetEmailButton = st.button("Enviar email de redefinição")
        if sendResetEmailButton:
            doSendResetPasswordEmail(email=email)