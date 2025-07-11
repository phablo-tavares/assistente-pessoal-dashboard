import streamlit as st
from supabase_client import SupabaseClient
import pandas as pd
import numpy as np

st.set_page_config(
    layout="wide",
    page_title="Dashboard Agente Pessoal - by Carp.IA",
    page_icon=None
)

if "clientSpendings" not in st.session_state:
    st.session_state.clientSpendings = []

if "spendingDataFetched" not in st.session_state:
    st.session_state.spendingDataFetched = False




@st.fragment()
def spendingsPageContent():
    moradiaColumnData = []
    alimentacaoColumnData = []
    transporteColumnData = []
    saudeColumnData = []
    educacaoColumnData = []
    lazerColumnData = []
    vestuarioColumnData = []
    dividasColumnData = []
    outrosColumnData = []

    for clientSpendign in st.session_state.clientSpendings:
        match clientSpendign:
            case 'Moradia':
                moradiaColumnData
                pass

    lineChartData = pd.DataFrame(
        data=[
            moradiaColumnData,
            alimentacaoColumnData,
            transporteColumnData,
            saudeColumnData,
            educacaoColumnData,
            lazerColumnData,
            vestuarioColumnData,
            dividasColumnData,  
            outrosColumnData,
        ],
        columns= [
            "Moradia",
            "Alimentação",
            "Transporte",
            "Saúde",
            "Educação",
            "Lazer",
            "Vestuário",
            "Dívidas",
            "Outros",
        ],
    )

    st.line_chart(data=lineChartData)







if st.session_state.spendingDataFetched == False:
    with st.spinner('Carregando...'):
        st.session_state.supabaseClient = SupabaseClient()
        st.session_state.clientSpendings = st.session_state.supabaseClient.getSpendingsByPhoneNumber('556299035665')
        st.session_state.spendingDataFetched = True
        st.rerun()
else:
    spendingsPageContent()





        
