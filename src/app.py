import streamlit as st
import requests

st.title("AI Research Assistant")
st.write("Ask question AI research papers.")

if "history" not in st.session_state:
    st.session_state.history = []

question = st.text_input("Ask a question about papers:")

if st.button("Ask") and question:
    with st.spinner("Thinking..."): #it runs setup (show spinner), executes your code, then runs cleanup (hide spinner) automatically.
        response = requests.post(
            "http://127.0.0.1:8000/ask",
            json={"question": question, "n_results": 3}
        )
        data = response.json()
    
    st.session_state.history.append(
        {
            "question": question,
            "answer": data["answer"],
            "sources": data["sources"]
        }
    )
    
for excahange in reversed(st.session_state.history):
    st.subheader(f" {excahange['question']}")
    st.write(excahange["answer"])
    with st.expander("Sources"):
        for source in excahange["sources"]:
            st.write(f"**{source['title']}** - similarity: {source['similarity']}")
    st.divider()