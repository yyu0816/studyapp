import streamlit as st
@st.dialog("Test Dialog")
def show_dialog():
    c = st.color_picker("Pick a color", key="cp")
    st.write("Color:", c)
if st.button("Open"):
    show_dialog()
