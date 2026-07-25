import streamlit as st

st.title("AI Research Assistant")
st.write("Ask question AI research papers.")

question = st.text_input("Ask a question about papers:")

if st.button("Ask"):
    st.write("you typed:", question)