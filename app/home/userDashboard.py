import streamlit as st
import pandas as pd
from datetime import date
import altair as alt
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

# --- Funções de Lógica de Negócio ---

def calcular_metricas_principais(gastos):
    if not gastos:
        return {
            'total_gastos': 0,
            'maior_gasto_valor': 0,
            'maior_gasto_categoria': 'N/A',
            'categoria_principal_nome': 'N/A',
        }

    # Usa o Pandas para facilitar a manipulação dos dados
    df = pd.DataFrame(gastos)
    df['spending_value'] = pd.to_numeric(df['spending_value'])

    # 1. Calcular o Total de Gastos
    total_gastos = df['spending_value'].sum()

    # 2. Encontrar o Maior Gasto (a maior transação individual)
    # .loc encontra a linha inteira com o maior valor
    maior_gasto_registro = df.loc[df['spending_value'].idxmax()]
    maior_gasto_valor = maior_gasto_registro['spending_value']
    maior_gasto_categoria = maior_gasto_registro['spending_category']

    # 3. Encontrar a Categoria Principal (categoria com a maior soma de gastos)
    gastos_por_categoria = df.groupby('spending_category')['spending_value'].sum()
    categoria_principal_nome = gastos_por_categoria.idxmax()

    categoria_principal_valor = gastos_por_categoria.max()
    if total_gastos > 0:
        categoria_principal_percentual = (categoria_principal_valor / total_gastos) * 100
    else:
        categoria_principal_percentual = 0

    return {
        'total_gastos': total_gastos,
        'maior_gasto_valor': maior_gasto_valor,
        'maior_gasto_categoria': maior_gasto_categoria,
        'categoria_principal_nome': categoria_principal_nome,
        'categoria_principal_percentual': categoria_principal_percentual,
    }

def getCurrentClientData():
    if st.session_state.currentUser:
        authUserId = st.session_state.currentUser.id
        client_data_list = st.session_state.supabaseClient.getClientData(authUserId=authUserId)
        if client_data_list:
            st.session_state.clientData = client_data_list[0]

# FUNÇÃO CENTRAL: Orquestra a busca de dados com base no modo de visualização
def fetch_spending_data():
   
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
def userDashboard():
    css_path = os.path.join(current_dir, "..", "styles", "dashboard_styles.css")
    load_css(css_path)
    graph_option = "Gastos por Categoria"

    # Inicializa widgets com valores da sessão para consistência
    if 'start_date_widget' not in st.session_state:
        st.session_state.start_date_widget = st.session_state.startDate
    if 'end_date_widget' not in st.session_state:
        st.session_state.end_date_widget = st.session_state.endDate

    if not st.session_state.spendingDataFetched:
        with st.spinner("Buscando dados..."):
            getCurrentClientData()
            fetch_spending_data()
            st.session_state.spendingDataFetched = True
            st.rerun()
    
    if not st.session_state.clientData:
        st.error("Não foi possível carregar seus dados. Tente sair e entrar novamente.")
        return

    if not st.session_state.clientData.get('active_subscription', False):
        st.error("Assinatura inativa! Para começar a usar o sistema, fale com o administrador para ativar sua assinatura.")
        return


    metricas = calcular_metricas_principais(st.session_state.clientSpendings)
    total_gastos = metricas['total_gastos']
    maior_gasto = metricas['maior_gasto_valor']
    categoria_do_maior_gasto = metricas['maior_gasto_categoria']
    categoria_principal_nome = metricas['categoria_principal_nome']
    categoria_principal_percentual = metricas['categoria_principal_percentual']
    
    with st.container(key="dashboard-container"):
        totalSpendings,biggestSpending,mainCategorySpending = st.columns(3)
        with totalSpendings:
            with st.container(key="totalSpendings"):
                st.write("Total de Gastos")
                st.markdown(
                    f'''
                        <div style="display: flex;">
                            <div style="flex-grow: 1;">
                                <h2>R$ {total_gastos:,.2f}</h2>
                            </div>
                            <div>
                                <svg xmlns="http://www.w3.org/2000/svg" height="32px" viewBox="0 -960 960 960" width="32px" fill="#e3e3e3">
                                    <path d="m140-220-60-60 300-300 160 160 284-320 56 56-340 384-160-160-240 240Z" />
                                </svg>
                            </div>
                        </div>
                    ''',
                    unsafe_allow_html=True,
                )
                st.write("No período")

        with biggestSpending:
            with st.container(key="biggestSpending"):
                st.write("Maior Gasto")
                st.markdown(
                    f'''
                        <div style="display: flex;">
                            <div style="flex-grow: 1;">
                                <h2>R$ {maior_gasto:,.2f}</h2>
                            </div>
                            <div>
                                <svg xmlns="http://www.w3.org/2000/svg" height="32px" viewBox="0 -960 960 960" width="32px" fill="#e3e3e3">
                                    <path d="M440-160v-487L216-423l-56-57 320-320 320 320-56 57-224-224v487h-80Z" />
                                </svg>
                            </div>
                        </div>
                    ''',
                    unsafe_allow_html=True,
                )
                st.write(categoria_do_maior_gasto)

        with mainCategorySpending:
            with st.container(key="mainCategorySpending"):
                st.write("Categoria Principal")
                st.markdown(
                    f'''
                        <div style="display: flex;">
                            <div style="flex-grow: 1;">
                                <h2>{categoria_principal_nome}</h2>
                            </div>
                            <p style="font-size:24px">#1</p>
                        </div>
                    ''',
                    unsafe_allow_html=True
                )
                st.write(f'{categoria_principal_percentual:.0f}% do total')
        st.markdown('<br>',unsafe_allow_html=True)

        with st.container(key='filters'):
            # --- Inputs de Data e Visualização ---
            st.markdown(getHtmlString("filtersAndConfigsElement.html"),unsafe_allow_html=True)
            dates_input_cols = st.columns([1, 1, 1, 1])
            with dates_input_cols[0]:
                st.date_input(
                    "Data de Início",
                    key='start_date_widget', 
                    on_change=update_dates, 
                    max_value=st.session_state.endDate
                )
            with dates_input_cols[1]:
                st.date_input(
                    "Data de Fim", 
                    key='end_date_widget', 
                    on_change=update_dates, 
                    min_value=st.session_state.startDate
                )

            with dates_input_cols[2]:
                graph_option = st.selectbox(
                    'Visualização do Gráfico',
                    key='graph_selector_widget',
                    options=["Gastos por Categoria", "Composição dos Gastos","Evolução dos Gastos"],
                )
            
            if st.session_state.clientData.get('spendings_sharing_key'):
                with dates_input_cols[3]:
                    st.selectbox(
                        'Modo de Visualização',
                        key='visualize_spendings_data_together_widget',
                        options=["Visualizar apenas meus gastos", "Visualizar gastos em conjunto"],
                        on_change=update_view_mode
                    )
        
        st.markdown("<br>", unsafe_allow_html=True)
            
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
            with st.container():
                st.markdown(texto_com_link, unsafe_allow_html=True)
        else:   
            with st.container(key="spendings-graphs"):
                graphDescriptionHtml = f'''
                    <div>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="
                                width: 12px;
                                height: 12px;
                                background: linear-gradient(135deg, hsl(20 100% 55%) 0%, hsl(25 100% 60%) 100%);
                                border-radius: 50%;
                            ">
                            </div>
                            <div style="flex-grow: 1;">
                                <h3 style="font-size: 18px;">
                                    {graph_option}
                                </h3>
                            </div>
                        </div>
                        <p>Análise detalhada dos seus gastos no período selecionado</p>
                    </div>
                    <br>
                '''
                if graph_option == "Gastos por Categoria":
                    st.markdown(graphDescriptionHtml, unsafe_allow_html=True)
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
                        
                    st.altair_chart(barChart.configure_axis(grid=False).configure(background='white').configure_view(strokeWidth=0).properties(height=500), use_container_width=True)

                elif graph_option == "Composição dos Gastos":
                    st.markdown(graphDescriptionHtml, unsafe_allow_html=True)
                    df_pie = getDataFramePieChart()
                    pie_chart = alt.Chart(df_pie).mark_arc(innerRadius=90, cornerRadius=5).encode(
                        theta=alt.Theta("Valor Gasto (R$):Q"),
                        color=alt.Color('Categoria:N', scale=alt.Scale(domain=df_pie['Categoria'].tolist(), range=df_pie['colors'].tolist()), legend=alt.Legend(title="Categorias", orient="right")),
                        tooltip=['Categoria', 'Valor Gasto (R$)']
                    ).configure_view(strokeWidth=0).configure(background='white').properties(height=500)
                    st.altair_chart(pie_chart, use_container_width=True)

                elif graph_option == "Evolução dos Gastos":
                    st.markdown(graphDescriptionHtml, unsafe_allow_html=True)
                    df_line = getLineChartDataFrame()
                    lineChart = alt.Chart(df_line).mark_line().encode(
                        x=alt.X('Data:T', title='Data'),
                        y=alt.Y('Total Acumulado (R$):Q', title='Total Acumulado (R$)', scale=alt.Scale(zero=True)),
                        color=alt.Color('Categoria:N', title='Categoria'),
                        tooltip=['Data', 'Categoria', 'Total Acumulado (R$)']
                    ).properties(height=500).configure_axis(grid=False).configure(background='white').configure_view(strokeWidth=0).interactive()
                    st.altair_chart(lineChart, use_container_width=True)