import streamlit as st
import os
import pandas as pd
import numpy as np

st.write('skdljfhaksdhkfasdasdças')
st.write(['lsakjdfhas',213123,21341234,'sdgsdfgsdfg'])
pressed = st.button("preess me")
st.write(f"pressed: {pressed}")
st.title("title")
st.header("header")
st.subheader("subheader")
st.markdown("## markdown")
st.caption("caption")
st.code("""
for i in range(5000):
    print(i)

""")
st.image(os.path.join(os.getcwd(),"static","Imagem do WhatsApp de 2025-05-12 à(s) 16.32.25_d6a37d2d.jpg"))
st.divider()

#dataframe
dataFrame = pd.DataFrame({
    "name":['pedro','lucas','jose','maria','julia','alice'],
    "age":[18,19,22,15,19,25],
    "ocupation":['sdfgsdfgsdf','sdfgsdfgsdf','sdfgsdfgsdf','sdfgsdfgsdf','sdfgsdfgsdf','sdfgsdfgsdf',],
})
st.dataframe(dataFrame)

#editable dataframe
st.subheader('data editor')
editableDataframe = st.data_editor(dataFrame)

#static table
st.subheader('static table')
st.table(dataFrame)

#metrics
st.metric(label='total rows',value=len(dataFrame))


#CHARTS
gastosCliente = pd.DataFrame(
    data=np.random.rand(20,9),
    columns=[
        'Moradia',
        'Alimentação',
        'Transporte',
        'Saúde',
        'Educação',
        'Lazer',
        'Vestuário',
        'Dívidas',
        'Outros',
    ],
)
st.subheader('area chart')
st.area_chart(gastosCliente)

#bar chart
st.subheader('bar chart')
st.bar_chart(gastosCliente)

#line chart
st.subheader('line chart')
st.line_chart(gastosCliente)
