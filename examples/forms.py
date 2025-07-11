import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta

st.title('User data form')

form_data = {
    "name":None,
    "height":None,
    "gender":None,
    "birthDate":None,
}
date18YearsAgo = datetime.now(ZoneInfo("America/Sao_Paulo")) - relativedelta(years=18)
date150YearsAgo = datetime.now(ZoneInfo("America/Sao_Paulo")) - relativedelta(years=150)

with st.form(key='user_form_data'):
    form_data['name']= st.text_input('Enter your name')
    form_data['height'] = st.number_input('Enter your height')
    form_data['gender'] = st.selectbox(
        "Gender",
        ['male','female','others'],
    )
    form_data['birthDate'] = st.date_input(
        label='Enter your bith date',
        min_value=date150YearsAgo,
        max_value=date18YearsAgo,
    )

    submit_button = st.form_submit_button('Submit')
    if submit_button:
        if not all(form_data.values()):
            st.warning("please fill all fields")
        else:
            st.balloons()