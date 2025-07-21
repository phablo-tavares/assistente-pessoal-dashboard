import streamlit as st
import pandas as pd
from datetime import date
import altair as alt

# --- Funções de Lógica de Negócio ---

def getCurrentClientData():
    if st.session_state.currentUser:
        authUserId = st.session_state.currentUser.id
        client_data_list = st.session_state.supabaseClient.getClientData(authUserId=authUserId)
        if client_data_list:
            st.session_state.clientData = client_data_list[0]

# FUNÇÃO CENTRAL: Orquestra a busca de dados com base no modo de visualização
def fetch_spending_data():
    with st.spinner("Buscando dados..."):
        phone_numbers_to_fetch = []
        st.session_state.user_map = {} # Limpa o mapa de usuários

        if not st.session_state.clientData:
            getCurrentClientData()
        
        if not st.session_state.clientData:
            st.warning("Não foi possível carregar os dados do cliente.")
            st.session_state.clientSpendings = []
            return

        # Decide quais números de telefone usar
        if st.session_state.view_mode == "joint" and st.session_state.clientData.get('spendings_sharing_key'):
            sharing_key = st.session_state.clientData['spendings_sharing_key']
            users_in_group = st.session_state.supabaseClient.getUsersBySharingKey(sharing_key)
            if users_in_group:
                phone_numbers_to_fetch = [user['phone_number'] for user in users_in_group]
                # Cria o mapa de telefone para nome para usar nos gráficos
                st.session_state.user_map = {user['phone_number']: user['full_name'] for user in users_in_group}
        else: # Modo pessoal ou sem chave
            phone_numbers_to_fetch = [st.session_state.clientData['phone_number']]
            st.session_state.user_map = {st.session_state.clientData['phone_number']: st.session_state.clientData.get('full_name', 'Eu')}

        if phone_numbers_to_fetch:
            clientSpendings = st.session_state.supabaseClient.getSpendings(
                phoneNumbers=phone_numbers_to_fetch,
                startDate=st.session_state.startDate,
                endDate=st.session_state.endDate,
            )
            st.session_state.clientSpendings = clientSpendings
        else:
            st.session_state.clientSpendings = []

# --- Funções de Callback ---

def update_dates():
    st.session_state.startDate = st.session_state.start_date_widget
    st.session_state.endDate = st.session_state.end_date_widget
    fetch_spending_data()

def update_view_mode():
    selection = st.session_state.visualize_spendings_data_together_widget
    st.session_state.view_mode = "joint" if "em conjunto" in selection else "personal"
    fetch_spending_data()

# --- Funções para Preparação dos DataFrames dos Gráficos ---

def getDataFrameBarChart():
    if not st.session_state.clientSpendings:
        return pd.DataFrame()

    df = pd.DataFrame(st.session_state.clientSpendings)
    df['spending_value'] = pd.to_numeric(df['spending_value'])
    df = df[df['spending_value'] >= 0].copy()
    
    df['Membro'] = df['client_phone_number'].map(st.session_state.user_map).fillna("Desconhecido")
    
    spendingsByCategory = df.groupby(['spending_category', 'Membro'])['spending_value'].sum().reset_index()
    spendingsByCategory.rename(
        columns={'spending_category': 'Categoria', 'spending_value': 'Valor Gasto (R$)'},
        inplace=True
    )
    
    colors = ['#FF4B4B','#4B7BFF','#32CD32', '#FFA500','#A34BFF','#00CED1', '#FF69B4', '#FFD700','#A0522D','#708090']
    unique_categories = sorted(spendingsByCategory['Categoria'].unique())
    category_colors = {cat: colors[i % len(colors)] for i, cat in enumerate(unique_categories)}
    if 'outros' in category_colors:
        category_colors['outros'] = '#708090'
    
    spendingsByCategory['colors'] = spendingsByCategory['Categoria'].map(category_colors)

    if 'outros' in spendingsByCategory['Categoria'].values:
        spendingsByCategory['sort_key'] = spendingsByCategory['Categoria'].apply(lambda x: 1 if x == 'outros' else 0)
        spendingsByCategory.sort_values(by=['sort_key', 'Categoria'], inplace=True)
        spendingsByCategory.drop(columns='sort_key', inplace=True)
    else:
        spendingsByCategory.sort_values(by='Categoria', inplace=True)

    return spendingsByCategory

def getDataFramePieChart():
    if not st.session_state.clientSpendings:
        return pd.DataFrame()

    df = pd.DataFrame(st.session_state.clientSpendings)
    df['spending_value'] = pd.to_numeric(df['spending_value'])
    df = df[df['spending_value'] >= 0].copy()
    
    spendingsByCategory = df.groupby('spending_category')['spending_value'].sum().reset_index()
    spendingsByCategory.rename(columns={'spending_category': 'Categoria', 'spending_value': 'Valor Gasto (R$)'}, inplace=True)

    colors = ['#FF4B4B','#4B7BFF','#32CD32', '#FFA500','#A34BFF','#00CED1', '#FF69B4', '#FFD700','#A0522D','#708090']
    unique_categories = sorted(spendingsByCategory['Categoria'].unique())
    category_colors = {cat: colors[i % len(colors)] for i, cat in enumerate(unique_categories)}
    if 'outros' in category_colors:
        category_colors['outros'] = '#708090'
        
    spendingsByCategory['colors'] = spendingsByCategory['Categoria'].map(category_colors)
    return spendingsByCategory

def getLineChartDataFrame():
    if not st.session_state.clientSpendings:
        return pd.DataFrame()
    
    allCategories = ["moradia", "alimentação", "transporte", "saúde", "educação", "lazer", "vestuário", "dívidas", "outros"]
    
    rawDf = pd.DataFrame(st.session_state.clientSpendings)
    rawDf['spending_value'] = pd.to_numeric(rawDf['spending_value'])
    rawDf['spending_date'] = pd.to_datetime(rawDf['spending_date']).dt.date
    rawDf = rawDf[rawDf['spending_value'] >= 0].copy()

    spendingsDf = rawDf.groupby(['spending_date', 'spending_category'])['spending_value'].sum().reset_index()
    
    periodDates = pd.to_datetime(pd.date_range(start=st.session_state.startDate, end=st.session_state.endDate)).date
    multiIndex = pd.MultiIndex.from_product([periodDates, allCategories], names=['spending_date', 'spending_category'])
    completeDf = pd.DataFrame(index=multiIndex).reset_index()

    finalDf = pd.merge(completeDf, spendingsDf, on=['spending_date', 'spending_category'], how='left').fillna(0)
    finalDf.sort_values(by='spending_date', inplace=True)
    
    finalDf['valor_acumulado'] = finalDf.groupby('spending_category')['spending_value'].cumsum()
    
    finalDf.rename(columns={'spending_date': 'Data', 'spending_category': 'Categoria', 'valor_acumulado': 'Total Acumulado (R$)'}, inplace=True)
    return finalDf

# --- Componente Principal da Tela ---
def homePage():
    # Inicializa widgets com valores da sessão para consistência
    if 'start_date_widget' not in st.session_state:
        st.session_state.start_date_widget = st.session_state.startDate
    if 'end_date_widget' not in st.session_state:
        st.session_state.end_date_widget = st.session_state.endDate

    if not st.session_state.spendingDataFetched:
        with st.spinner('Carregando...'):
            getCurrentClientData()
            fetch_spending_data()
            st.session_state.spendingDataFetched = True
            st.rerun()

    st.title('Dashboard Agente Pessoal - by Carp.IA')
    st.write('')
    
    if not st.session_state.clientData:
        st.error("Não foi possível carregar seus dados. Tente sair e entrar novamente.")
        return

    if not st.session_state.clientData.get('active_subscription', False):
        st.error("Assinatura inativa! Para começar a usar o sistema, fale com o administrador para ativar sua assinatura.")
        return

    st.markdown("Bem-vindo ao dashboard do seu agente pessoal. Aqui você pode visualizar os gastos registrados pelo WhatsApp.")
    
    # --- Inputs de Data e Visualização ---
    dates_input_cols = st.columns([1, 1, 2])
    with dates_input_cols[0]:
        st.date_input("Data de Início", key='start_date_widget', value=st.session_state.startDate, on_change=update_dates, max_value=st.session_state.endDate)
    with dates_input_cols[1]:
        st.date_input("Data de Fim", key='end_date_widget', value=st.session_state.endDate, on_change=update_dates, min_value=st.session_state.startDate)
    
    if st.session_state.clientData.get('spendings_sharing_key'):
        with dates_input_cols[2]:
            st.selectbox(
                'Modo de Visualização',
                key='visualize_spendings_data_together_widget',
                options=["Visualizar apenas meus gastos", "Visualizar gastos em conjunto"],
                on_change=update_view_mode
            )
    
    if not st.session_state.clientSpendings:
        link_whatsapp = "https://wa.me/5562992359294"
        texto_com_link = f"""
        <div style="padding: 1rem; border-radius: 0.5rem; background-color:#c2ba9d; margin-top: 1rem;">
            <p style="color: #B45309; margin: 0;">
                Nenhum gasto encontrado para o período ou modo de visualização selecionado! <br>
                Para registrar, entre em contato com o Agente Pessoal: 
                <a href="{link_whatsapp}" target="_blank" style="color: #0284C7; font-weight: bold;">+55 (62) 99235-9294</a>
            </p>
        </div>
        """
        st.markdown(texto_com_link, unsafe_allow_html=True)
    else:
        barChartTab, pieChartTab, lineChartTab = st.tabs(["Gastos por Categoria", "Composição dos Gastos", "Evolução dos Gastos"])

        with barChartTab:
            df_bar = getDataFrameBarChart()
            
            if st.session_state.view_mode == 'personal':
                df_personal = df_bar.groupby(['Categoria', 'colors'], as_index=False)['Valor Gasto (R$)'].sum()
                barChart = alt.Chart(df_personal).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                    x=alt.X('Categoria:N', title='Categoria', sort=None),
                    y=alt.Y('Valor Gasto (R$):Q', title='Valor Gasto (R$)', scale=alt.Scale(zero=True)),
                    color=alt.Color('Categoria:N', scale=alt.Scale(domain=df_personal['Categoria'].tolist(), range=df_personal['colors'].tolist()), legend=None),
                    tooltip=['Categoria', 'Valor Gasto (R$)']
                )
            else: # MODO 'JOINT'
                barChart = alt.Chart(df_bar).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                    x=alt.X('Categoria:N', title='Categoria', sort=None),
                    y=alt.Y('Valor Gasto (R$):Q', title='Valor Gasto (R$)', scale=alt.Scale(zero=True)),
                    color=alt.Color('Membro:N', title='Membro'),
                    tooltip=['Categoria', 'Membro', 'Valor Gasto (R$)']
                )
                
            st.altair_chart(barChart.configure_axis(grid=False).configure_view(strokeWidth=0).properties(height=500), use_container_width=True)

        with pieChartTab:
            df_pie = getDataFramePieChart()
            pie_chart = alt.Chart(df_pie).mark_arc(innerRadius=90, cornerRadius=5).encode(
                theta=alt.Theta("Valor Gasto (R$):Q"),
                color=alt.Color('Categoria:N', scale=alt.Scale(domain=df_pie['Categoria'].tolist(), range=df_pie['colors'].tolist()), legend=alt.Legend(title="Categorias", orient="right")),
                tooltip=['Categoria', 'Valor Gasto (R$)']
            ).configure_view(strokeWidth=0).properties(height=500)
            st.altair_chart(pie_chart, use_container_width=True)

        with lineChartTab:
            df_line = getLineChartDataFrame()
            lineChart = alt.Chart(df_line).mark_line().encode(
                x=alt.X('Data:T', title='Data'),
                y=alt.Y('Total Acumulado (R$):Q', title='Total Acumulado (R$)', scale=alt.Scale(zero=True)),
                color=alt.Color('Categoria:N', title='Categoria'),
                tooltip=['Data', 'Categoria', 'Total Acumulado (R$)']
            ).properties(height=500).configure_axis(grid=False).configure_view(strokeWidth=0).interactive()
            st.altair_chart(lineChart, use_container_width=True)