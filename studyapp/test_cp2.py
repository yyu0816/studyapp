import streamlit as st

@st.dialog("Test Dialog")
def show_dialog():
    st.write("Dialog open")
    c = st.color_picker("Pick a color")
    st.write("Color chosen:", c)

if st.button("Open Dialog"):
    show_dialog()
