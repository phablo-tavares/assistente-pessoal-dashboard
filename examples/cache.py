import streamlit as st
import time

@st.cache_data(ttl=60)
def fech_data():
    time.sleep(5)
    return {'data':'sampledata'}

data = fech_data()
if data:
    st.write(data)
else:
    st.write('fetching data')