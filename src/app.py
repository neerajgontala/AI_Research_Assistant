import streamlit as st
import requests

st.title("AI Research Assistant")
st.write("Ask question AI research papers.")

question = st.text_input("Ask a question about papers:")

if st.button("Ask"):
    with st.spinner("Thinking..."): #it runs setup (show spinner), executes your code, then runs cleanup (hide spinner) automatically.
        response = requests.post(
            "http://127.0.0.1:8000/ask",
            json={"question": question, "n_results": 3}
        )
        data = response.json()
    
    st.subheader("Answer")
    st.write(data["answer"])
    
    st.subheader("Sources")
    for source in data["sources"]:
        st.write(f"**{source['title']}** - similarity: {source['similarity']}")