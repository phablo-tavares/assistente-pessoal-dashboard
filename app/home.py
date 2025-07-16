import streamlit as st
from supabase_client import SupabaseClient
import pandas as pd
from datetime import date, timedelta
import altair as alt
from email_validator import validate_email
import re

st.set_page_config(
    layout="wide",
    page_title="Dashboard Agente Pessoal - by Carp.IA",
    page_icon=None,
    initial_sidebar_state="collapsed"
)

if "clientSpendings" not in st.session_state:
    st.session_state.clientSpendings = []
if "spendingDataFetched" not in st.session_state:
    st.session_state.spendingDataFetched = False

if "startDate" not in st.session_state:
    st.session_state.startDate = date.today() - timedelta(days=30)
if "endDate" not in st.session_state:
    st.session_state.endDate = date.today()
if "start_date_widget" not in st.session_state:
    st.session_state.start_date_widget = st.session_state.startDate
if "end_date_widget" not in st.session_state:
    st.session_state.end_date_widget = st.session_state.endDate

if "supabaseClient" not in st.session_state:
    st.session_state.supabaseClient = SupabaseClient()
if "currentUser" not in st.session_state:
    st.session_state.currentUser = None
if "clientData" not in st.session_state:
    st.session_state.clientData = None

if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'refresh_token' not in st.session_state:
    st.session_state.refresh_token = None
if 'redefine_password_flux' not in st.session_state:
    st.session_state.redefine_password_flux = False



access_token = st.query_params.get("access_token")
refresh_token = st.query_params.get("refresh_token")
if access_token and refresh_token and st.session_state.redefine_password_flux == False:
    st.session_state.redefine_password_flux = True
    st.session_state.access_token = access_token
    st.session_state.refresh_token = refresh_token

def getCurrentClientData():
    authUserId = st.session_state.currentUser.id
    clientData = st.session_state.supabaseClient.getClientData(authUserId=authUserId)[0]
    st.session_state.clientData = clientData

def getClientSpendings():
    clientSpendings = st.session_state.supabaseClient.getSpendings(
        phoneNumber=st.session_state.clientData['phone_number'],
        startDate=st.session_state.startDate,
        endDate=st.session_state.endDate,
    )
    st.session_state.clientSpendings = clientSpendings

def update_dates():
    st.session_state.startDate = st.session_state.start_date_widget
    st.session_state.endDate = st.session_state.end_date_widget
    getClientSpendings()

def getDataFrameBarChart():
    dataFrame = pd.DataFrame(st.session_state.clientSpendings)
    dataFrame['spending_value'] = pd.to_numeric(dataFrame['spending_value'])
    dataFrame['spending_date'] = pd.to_datetime(dataFrame['spending_date'])
    dataFrame = dataFrame[dataFrame['spending_value'] >= 0].copy()
    spendingsByCategory = dataFrame.groupby('spending_category')['spending_value'].sum().reset_index()

    spendingsByCategory.rename(
        columns={
            'spending_category': 'Categoria',
            'spending_value': 'Valor Gasto (R$)'
        },
        inplace=True,
    )

    if 'outros' in spendingsByCategory['Categoria'].values:
        spendingsByCategory['sort_key'] = spendingsByCategory['Categoria'].apply(
            lambda x: 1 if x == 'outros' else 0
        )
        spendingsByCategory.sort_values(by=['sort_key', 'Categoria'], inplace=True)
        spendingsByCategory.drop(columns='sort_key', inplace=True)
    else:
        spendingsByCategory.sort_values(by='Categoria', inplace=True)

    colors = [
        '#FF4B4B','#4B7BFF','#32CD32', '#FFA500','#A34BFF','#00CED1', '#FF69B4', '#FFD700','#A0522D','#708090',
    ]
    cores_ordenadas = [colors[i % len(colors)] for i in range(len(spendingsByCategory))]
    spendingsByCategory['colors'] = cores_ordenadas

    return spendingsByCategory

def getLineChartDataFrame():
    """Prepara o DataFrame para o gráfico de linhas de SOMA ACUMULADA."""
    allCategories = [
        "moradia", "alimentação", "transporte", "saúde", "educação",
        "lazer", "vestuário", "dívidas", "outros"
    ]

    rawDf = pd.DataFrame(st.session_state.clientSpendings)
    if rawDf.empty:
        return pd.DataFrame()

    rawDf['spending_value'] = pd.to_numeric(rawDf['spending_value'])
    rawDf['spending_date'] = pd.to_datetime(rawDf['spending_date']).dt.date
    rawDf = rawDf[rawDf['spending_value'] >= 0].copy()

    spendingsDf = rawDf.groupby(['spending_date', 'spending_category'])['spending_value'].sum().reset_index()

    periodDates = pd.to_datetime(pd.date_range(
        start=st.session_state.startDate,
        end=st.session_state.endDate
    )).date

    multiIndex = pd.MultiIndex.from_product([periodDates, allCategories], names=['spending_date', 'spending_category'])
    completeDf = pd.DataFrame(index=multiIndex).reset_index()

    finalDf = pd.merge(completeDf, spendingsDf, on=['spending_date', 'spending_category'], how='left')
    finalDf['spending_value'].fillna(0, inplace=True)

    finalDf.sort_values(by='spending_date', inplace=True)

    finalDf['valor_acumulado'] = finalDf.groupby('spending_category')['spending_value'].cumsum()
    finalDf.rename(
        columns={
            'spending_date': 'Data',
            'spending_category': 'Categoria',
            'valor_acumulado': 'Total Acumulado (R$)'
        },
        inplace=True
    )

    return finalDf

def isEmailValid(email:str) -> bool:
    try:
        validate_email(email,check_deliverability=True)
        return True
    except:
        return False

def isPasswordValid(password:str) ->bool:
    return len(password) >= 6

def isWhatsappInUse(whatsapp:str):
    try:
        phoneNumberAlreadyInUse = st.session_state.supabaseClient.phoneNumberAlreadyInUse(phoneNumber=whatsapp)
        return phoneNumberAlreadyInUse
    except Exception as e:
        return False

def isWhatsappValid(whatsapp:str):
    return len(whatsapp) >= 7
def isCPFValid(cpf:str):
    return len(cpf) == 11

def doSignUp(email:str, password: str, fullName:str, whatsapp:str,cpf:str):
    if not email or not password or not fullName or not cpf:
        st.warning('Preencha todos os campos')
    else:
        validEmail = isEmailValid(email=email)
        validPassword = isPasswordValid(password=password)
        validWhatsapp = isWhatsappValid(whatsapp=whatsapp)
        validCPF = isCPFValid(cpf=cpf)
        whatsappInUse = isWhatsappInUse(whatsapp=whatsapp)

        if not validEmail:
            st.toast('Email inválido')
        if not validPassword:
            st.toast('Senha deve conter mais de 6 dígitos')
        if not validWhatsapp:
            st.toast('Número de whatsapp deve ter 7 ou mais números')
        if whatsappInUse:
            st.toast('Número de whatsapp já cadastrado')
        if not validCPF:
            st.toast('CPF deve conter 11 números')

        if validEmail and validPassword and validWhatsapp and validCPF and not whatsappInUse:
            try:
                response = st.session_state.supabaseClient.signUp(email, password)
                user = response.user
                if user:
                    st.session_state.supabaseClient.updateClientData(phoneNumber=whatsapp,fullName=fullName,cpf=cpf,authUserId=user.id,active_subscription=False)
                    st.success("Cadastro feito com sucesso. Por favor, clique no link de confirmação enviado no seu email para validar seu cadastro. Após isso é só fazer login!")
            except Exception as e:
                st.error('Erro no cadastro, tente novamente mais tarde')

def doLogin(email:str, password: str):
    if not email or not password:
        st.warning('Preencha todos os campos')
    else:
        validEmail = isEmailValid(email=email)
        validPassword = isPasswordValid(password=password)
        if not validEmail:
            st.toast('Email inválido')
        if not validPassword:
            st.toast('Senha deve conter mais de 6 dígitos')

        if validEmail and validPassword:
            try:
                user = st.session_state.supabaseClient.signIn(email, password)
                if user:
                    st.session_state.currentUser = user
                    st.rerun()
            except Exception as e:
                if e.code == 'invalid_credentials':
                    st.error('Credenciais inválidas! Verifique o email e a senha e tente novamente.')
                else:
                    if e.code == 'email_not_confirmed':
                        st.error('Email não verificado! Por favor cheque sua caixa de email e após a verificação faça o login.')
                    else:
                        st.error('erro no login, tente novamente mais tarde')

def doSendResetPasswordEmail(email:str):
    if not email:
        st.warning('Preencha o email')
    else:
        validEmail = isEmailValid(email=email)
        if not validEmail:
            st.toast('Email inválido')
        if validEmail:
            try:
                st.session_state.supabaseClient.sendResetPasswordEmail(email=email)
                st.success('Enviado email para redefinição de senha. Acesse sua caixa de email e clique no link')
            except Exception as e:
                st.error('Erro enviando e-mail para redefinição de senha. tente novamente mais tarde.')

def doRedefinePassword(password:str):
    try:
        st.session_state.supabaseClient.resetPassword(password=password,access_token=st.session_state.access_token,refresh_token=st.session_state.refresh_token)
        st.session_state.redefine_password_flux = False
        st.success('Senha redefinida com sucesso')
    except Exception as e:
        st.error('Erro redefinindo senha. tente novamente mais tarde.')

def format_numeric_whatsapp():
    if 'whatsapp_number_input' in st.session_state:
        cleaned_whatsapp = re.sub(r'[^0-9]', '', st.session_state.whatsapp_number_input)
        st.session_state.whatsapp_number_input = cleaned_whatsapp

def format_numeric_cpf():
    if 'cpf_input' in st.session_state:
        cleaned_cpf = re.sub(r'[^0-9]', '', st.session_state.cpf_input)
        st.session_state.cpf_input = cleaned_cpf

def authScreen():
    st.title("Agente Pessoal - by Carp.IA")
    option = st.radio(label="", options=["Login", "Cadastro", "Esqueci minha senha"],horizontal=True)

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
        signUpButton = st.button("Cadastro")
        if signUpButton:
            doSignUp(email=email,password=password,fullName=fullName,whatsapp=whatsappNumber,cpf=cpf)

    elif option == "Esqueci minha senha":
        email = st.text_input("Email")
        sendResetEmailButton = st.button("Enviar email de redefinição de senha")
        if sendResetEmailButton:
            doSendResetPasswordEmail(email=email)

def redefinePasswordScreen():
    st.title("Agente Pessoal - by Carp.IA")
    with st.form("form"):
        password = st.text_input("Senha", type="password")
        loginButton = st.form_submit_button("Redefinir senha")
        if loginButton:
            doRedefinePassword(password=password)

def homePage():
    if st.session_state.spendingDataFetched == False:
        with st.spinner('Carregando...'):
            getCurrentClientData()
            getClientSpendings()
            st.session_state.spendingDataFetched = True
            st.rerun()
    else:
        st.title('Dashboard Agente Pessoal - by Carp.IA')
        st.write('')
        
        if st.session_state.clientData['active_subscription'] == False:
            st.error("Assinatura inativa! Para começar a usar o sistema fale com o administrador do sistema para ativar a sua assinatura.")

        else:
            st.markdown("""
            Bem vindo ao dashboard do seu agente pessoal, aqui você vê informações sobre os seus gastos registrados pelo whatsapp.

            Selecionando uma data de início e data de fim, você consegue visualizar informações sobre os gastos registrados nesse período.
            """)
            
            if st.session_state.clientSpendings == []:
                link_whatsapp = "https://wa.me/5562992359294"
                texto_com_link = f"""
                <div style="padding: 1rem; border-radius: 0.5rem; background-color:#c2ba9d">
                    <p style="color: #B45309; margin: 0;">
                        Você ainda não registrou nenhum gasto! Entre em contato com o Agente Pessoal e comece a registrar gastos: 
                        <a href="{link_whatsapp}" target="_blank" style="color: #0284C7; font-weight: bold;">+55 (62) 99235-9294</a>
                    </p>
                </div>
                """
                st.markdown(texto_com_link, unsafe_allow_html=True)
                st.markdown("<br><br>", unsafe_allow_html=True)
                
            else:
                # --- Dates Input ---
                datesInput,spacer = st.columns([1,3])
                with datesInput:
                    startDateInput,endDateInput = st.columns(2)
                    with startDateInput:
                        st.date_input(
                            key='start_date_widget',
                            label="Data de Início",
                            on_change=update_dates,
                            max_value=st.session_state.endDate,
                            width=200
                        )
                    with endDateInput:
                        st.date_input(
                            key='end_date_widget',
                            label="Data de Fim",
                            on_change=update_dates,
                            min_value=st.session_state.startDate,
                            width=200
                        )

                barChartTab,pieChartTab,lineChartTab = st.tabs(["Gastos por Categoria", "Composição dos Gastos","Evolução dos Gastos por Categoria"])

                with barChartTab:
                    # --- Bar Chart ---
                    barChart = alt.Chart(getDataFrameBarChart()).mark_bar(
                        cornerRadiusTopLeft=3,
                        cornerRadiusTopRight=3
                    ).encode(
                        x=alt.X('Categoria:N', title='Categoria', sort=None),
                        y=alt.Y('Valor Gasto (R$):Q', title='Valor Gasto (R$)', scale=alt.Scale(zero=True)),
                        color=alt.Color('colors:N', scale=None)
                    ).configure_axis(
                        grid=False
                    ).configure_view(
                        strokeWidth=0
                    ).properties(
                        height=500
                    )
                    st.altair_chart(barChart, use_container_width=True)

                with pieChartTab:
                    df_pie_chart = getDataFrameBarChart()
                    pie_chart = alt.Chart(df_pie_chart).mark_arc(
                        innerRadius=90,
                        cornerRadius=5
                    ).encode(
                        theta=alt.Theta(field="Valor Gasto (R$)", type="quantitative"),
                        color=alt.Color('Categoria:N',
                            scale=alt.Scale(
                                domain=df_pie_chart['Categoria'].tolist(),
                                range=df_pie_chart['colors'].tolist()
                            ),
                            legend=alt.Legend(
                                title="Categorias",
                                orient="right"
                            )
                        ),
                        tooltip=['Categoria', 'Valor Gasto (R$)']

                    ).configure_view(
                        strokeWidth=0
                    ).properties(
                        height=500
                    )
                    st.altair_chart(pie_chart, use_container_width=True)

                with lineChartTab:
                    # --- Line Chart ---
                    lineChart = alt.Chart(getLineChartDataFrame()).mark_line().encode(
                        x=alt.X('Data:T', title='Data'),
                        y=alt.Y('Total Acumulado (R$):Q', title='Total Acumulado (R$)', scale=alt.Scale(zero=True)),
                        color=alt.Color('Categoria:N', title='Categoria'),
                        tooltip=['Data', 'Categoria', 'Total Acumulado (R$)']

                    ).properties(
                        height=500
                    ).configure_axis(
                        grid=False
                    ).configure_view(
                        strokeWidth=0
                    ).interactive()

                    st.altair_chart(lineChart, use_container_width=True)

def formatNumericWhatsappEditPersoalData():
    if 'whatsapp_number_input_edit_personal_data' in st.session_state:
        cleaned_whatsapp = re.sub(r'[^0-9]', '', st.session_state.whatsapp_number_input_edit_personal_data)
        st.session_state.whatsapp_number_input_edit_personal_data = cleaned_whatsapp

def formatNumericCpfEditPersoalData():
    if 'cpf_input_edit_personal_data' in st.session_state:
        cleaned_cpf = re.sub(r'[^0-9]', '', st.session_state.cpf_input_edit_personal_data)
        st.session_state.cpf_input_edit_personal_data = cleaned_cpf

def doUpdatePersonalData(fullName:str,whatsappNumber:str,cpf:str):
    validWhatsapp = isWhatsappValid(whatsapp=whatsappNumber)
    validCPF = isCPFValid(cpf=cpf)
    whatsappInUse = isWhatsappInUse(whatsapp=whatsappNumber)

    if not validWhatsapp:
        st.toast('Número de whatsapp deve ter 7 ou mais números')
    if whatsappInUse:
        st.toast('Número de whatsapp já cadastrado')
    if not validCPF:
        st.toast('CPF deve conter 11 números')
        
    if validCPF and validWhatsapp and not whatsappInUse:
        try:
            st.session_state.supabaseClient.updateClientData(
                phoneNumber=whatsappNumber,
                fullName=fullName,
                cpf=cpf,
                authUserId=st.session_state.currentUser.id,
                active_subscription=None,
            )
            getCurrentClientData()
            st.success("Dados pessoais atualizados com sucesso!")
        except Exception as e:
            st.error('Erro ao atualizar dados pessoais, tente novamente mais tarde.')


def editPersonalDataPage():
    fullName = st.text_input(
        "Nome Completo",
        value=st.session_state.clientData['full_name'],
    )
    whatsappNumber = st.text_input(
        "Número Whatsapp (apenas números)",
        key="whatsapp_number_input_edit_personal_data",
        placeholder="5562987532165",
        max_chars=18,
        on_change=formatNumericWhatsappEditPersoalData,
        value=st.session_state.clientData['phone_number'],
    )
    cpf = st.text_input(
        "CPF (apenas números)",
        key="cpf_input_edit_personal_data",
        placeholder="11122233344",
        max_chars=11,
        on_change=formatNumericCpfEditPersoalData,
        value=st.session_state.clientData['cpf'],
    )
    saveButton = st.button("Salvar")
    if saveButton:
        doUpdatePersonalData(fullName=fullName,whatsappNumber=whatsappNumber,cpf=cpf)

def getAllClientsData():
    clientsData = st.session_state.supabaseClient.getAllClientData()
    st.session_state.allClientsData = clientsData


def toggleSubscriptionStatus(clientId:int,newStatus:bool,clientName:str):
    try:
        with st.spinner():
            st.session_state.supabaseClient.updateClientSubscriptionStatus(clientId=clientId,newStatus=newStatus)
    except Exception as e:
        st.toast('Erro mudando status da assinatura. Tente novamente mais tarde.')
        toggle_key = f'toggle_active_subscription{clientId}'
        st.session_state[toggle_key] = not newStatus
        for client in st.session_state.allClientsData:
            if client['id'] == clientId:
                client['active_subscription'] = not newStatus
                break
    
    for client in st.session_state.allClientsData:
        if client['id'] == clientId:
            client['active_subscription'] = newStatus
            break
            

def managementDashboard():
    if "allClientsData" not in st.session_state:
        st.session_state.allClientsData = []

    with st.spinner('Carregando...'):
        getCurrentClientData()
        getAllClientsData()
    st.title("Gerenciamento de usuários")

    for clientData in st.session_state.allClientsData:
        with st.container(border=True):
            name,cpf,phoneNumber,activeSubscription = st.columns(4)
            with name:
                st.write(clientData['full_name'])
            with cpf:
                st.write(clientData['cpf'])
            with phoneNumber:
                st.write(clientData['phone_number'])
            with activeSubscription:
                st.toggle(
                    label='Assinatura Ativa',
                    key=f'toggle_active_subscription{clientData['id']}',
                    value=clientData['active_subscription'],
                    width='stretch',
                    on_change=toggleSubscriptionStatus,
                    kwargs={
                        'clientId':clientData['id'],
                        'newStatus':not clientData['active_subscription'],
                        'clientName':clientData['full_name'],
                    }
                )


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
            st.session_state.spendingDataFetched = False
            st.session_state.supabaseClient.signOut()
    if pagina_selecionada == "Dashboard":
        if st.session_state.currentUser.email == 'agentepessoalcarpia@gmail.com':
            managementDashboard()
        else:
            homePage()
    elif pagina_selecionada == "Editar Dados Pessoais":
        editPersonalDataPage()
else:
    authScreen()