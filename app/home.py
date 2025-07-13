import streamlit as st
from supabase_client import SupabaseClient
import pandas as pd
from datetime import date, timedelta
import altair as alt

st.set_page_config(
    layout="wide",
    page_title="Dashboard Agente Pessoal - by Carp.IA",
    page_icon=None
)

if "clientSpendings" not in st.session_state:
    st.session_state.clientSpendings = []
if "spendingDataFetched" not in st.session_state:
    st.session_state.spendingDataFetched = False

if "startDate" not in st.session_state:
    st.session_state.startDate = date.today() - timedelta(days=5)
if "endDate" not in st.session_state:
    st.session_state.endDate = date.today()
if "start_date_widget" not in st.session_state:
    st.session_state.start_date_widget = st.session_state.startDate
if "end_date_widget" not in st.session_state:
    st.session_state.end_date_widget = st.session_state.endDate

if "supabaseClient" not in st.session_state:
    st.session_state.supabaseClient = SupabaseClient()
    
def getClientSpendings():
    st.session_state.clientSpendings = st.session_state.supabaseClient.getSpendings(
        phoneNumber='556299035665',
        startDate=st.session_state.startDate,
        endDate=st.session_state.endDate,
    )
    st.session_state.spendingDataFetched = True

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
   

if st.session_state.spendingDataFetched == False:
    with st.spinner('Carregando...'):
        getClientSpendings()
        st.rerun()
else:

    st.title('Dashboard Agente Pessoal - by Carp.IA')
    st.write('')
    st.markdown("""
    Bem vindo ao dashboard do seu agente pessoal, aqui você vê informações sobre os seus gastos registrados pelo whatsapp.
                
    Selecionando uma data de início e data de fim, você consegue visualizar informações sobre os gastos registrados nesse período.
    """)
    st.markdown("<br><br>", unsafe_allow_html=True)
    

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