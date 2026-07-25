import streamlit as st
import requests

st.title("AI Research Assistant")
st.write("Ask question AI research papers.")

question = st.text_input("Ask a question about papers:")

if st.button("Ask"):
    response = requests.post(
        "http://127.0.0.1:8000/ask",
        json={"question": question, "n_results": 3}
    )
    data = response.json()
    st.write(data)