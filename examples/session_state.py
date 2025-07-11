import streamlit as st

#logic
if "counter" not in st.session_state:
    st.session_state.counter = 0

def incremmentCounter():
    st.session_state.counter += 1

def resetCounter():
    st.session_state.counter = 0


#page
st.title(f'counter: {st.session_state.counter}')
incremment_counter_button = st.button('increment counter',on_click=incremmentCounter)
reset_counter_button = st.button('reset counter',on_click=resetCounter)


