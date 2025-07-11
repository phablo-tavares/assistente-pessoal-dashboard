import streamlit as st

if "step" not in st.session_state:
    st.session_state.step = 1

if "name" not in st.session_state:
    st.session_state.name = ''

def nextPage(newName):
    st.session_state.step +=1
    st.session_state.name = newName
def previousPage():
    st.session_state.step -=1

if st.session_state.step == 1:
    st.header('Part 1: info')
    name = st.text_input('Name',value = st.session_state.name)
    st.button('next',on_click=nextPage,args=(name,))
elif st.session_state.step == 2:
    st.header('Part 2: review')
    st.write(f"name: {st.session_state.name}")
    st.button('back',on_click=previousPage)