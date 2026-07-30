# import streamlit as st
# import requests

# st.title("AI Research Assistant")
# st.write("Ask question AI research papers.")

# if "history" not in st.session_state:
#     st.session_state.history = []

# question = st.text_input("Ask a question about papers:")

# if st.button("Ask") and question:
#     with st.spinner("Thinking..."): #it runs setup (show spinner), executes your code, then runs cleanup (hide spinner) automatically.
#         response = requests.post(
#             "http://127.0.0.1:8000/ask",
#             json={"question": question, "n_results": 3}
#         )
#         data = response.json()
    
#     st.session_state.history.append(
#         {
#             "question": question,
#             "answer": data["answer"],
#             "sources": data["sources"]
#         }
#     )
    
# for excahange in reversed(st.session_state.history):
#     st.subheader(f" {excahange['question']}")
#     st.write(excahange["answer"])
#     with st.expander("Sources"):
#         for source in excahange["sources"]:
#             st.write(f"**{source['title']}** - similarity: {source['similarity']}")
#     st.divider()


# ------------------------------------------------------------------------------------------



# app.py — Reimagined UI
#
# WHAT CHANGED FROM THE ORIGINAL:
# - Real chat bubbles (st.chat_message) instead of stacked st.write() blocks
# - st.chat_input pinned to the bottom, instead of a text_input + button
# - A sidebar showing paper count, example questions, and a "clear chat" control
# - Page config for a browser tab title/icon and wide layout
# - Sources shown as small caption text under each answer, not a big expander

import streamlit as st
import requests
import os

# ── PAGE CONFIG (must be the first Streamlit call) ───────────────────────────
# WHY st.set_page_config()?
# Controls things outside the page body: the browser tab title, the tab icon,
# and whether the content uses the full screen width or a centered column.
# Streamlit requires this to be the VERY FIRST st.* call in the whole script.
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
    layout="wide",
)

API_URL = os.getenv("API_URL","https://ai-research-assistant-tzia.onrender.com")  # WHY a constant? one place to change when you deploy


# ── SESSION STATE SETUP ───────────────────────────────────────────────────────
# WHY still session_state?
# Same reason as before — Streamlit reruns the whole script on every
# interaction, and this is the only thing that survives a rerun.
if "messages" not in st.session_state:
    st.session_state.messages = []
    # WHY "messages" instead of "history"?
    # We're matching the shape st.chat_message expects to render:
    # a list of {"role": ..., "content": ...} dicts — the same pattern
    # every major chat UI (including Claude's own) is built on.


# ── SIDEBAR ────────────────────────────────────────────────────────────────────
# WHY a sidebar at all?
# It moves secondary information (paper count, tips, controls) OUT of the
# main conversation flow, so the chat itself stays uncluttered.
with st.sidebar:
    st.title("🔬 Research Assistant")
    st.caption("Ask questions about your AI paper collection")

    st.divider()

    # WHY call the health check here?
    # Gives the user (and you, while testing) instant visual proof the
    # backend is alive and how many papers are loaded — no /docs needed.
    try:
        health = requests.get(f"{API_URL}/", timeout=3).json()
        st.metric("Papers loaded", health.get("papers_loaded", "—"))
        st.success("Backend online")
    except requests.exceptions.RequestException:
        st.error("Backend offline — start uvicorn first")

    st.divider()

    st.subheader("Try asking:")
    example_questions = [
        "What papers discuss robot manipulation?",
        "Which papers use neural networks?",
        "What are the latest advances in machine learning?",
    ]
    # WHY loop + button instead of hardcoding 3 buttons?
    # Add a 4th example later by just adding one line to the list above —
    # no new widget code needed. Classic "data drives UI" pattern.
    for eq in example_questions:
        if st.button(eq, use_container_width=True):
            # WHY set this instead of calling the API directly here?
            # We store the CLICKED question and let the main loop below
            # handle it uniformly — one code path for "typed" and "clicked"
            # questions instead of two.
            st.session_state.pending_question = eq

    st.divider()

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        # WHY st.rerun()?
        # Forces Streamlit to immediately restart the script from the top,
        # so the cleared chat reflects on screen right away instead of
        # waiting for the next natural interaction.


# ── MAIN CHAT AREA ─────────────────────────────────────────────────────────────
st.title("Chat with your papers")

# WHY loop over messages and render each one?
# st.chat_message doesn't remember past messages by itself — YOU decide what
# to draw, every rerun, from session_state. This loop is "replay the whole
# conversation from memory," which is why session_state had to hold it.
for message in st.session_state.messages:
    # WHY st.chat_message(role)?
    # Renders a styled bubble — avatar + background — matching "user" or
    # "assistant" automatically. This one call replaces st.subheader +
    # st.write + manual styling from the old version.
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            # WHY st.caption instead of an expander this time?
            # A design choice: small, always-visible source lines feel more
            # like a citation footnote and less like hidden extra work for
            # the user to open. Either is valid — this is a style call.
            for s in message["sources"]:
                st.caption(f"📄 {s['title']} · similarity {s['similarity']}")


# ── HANDLE INPUT ────────────────────────────────────────────────────────────────
# WHY st.chat_input instead of st.text_input + st.button?
# It's purpose-built for this exact case: pins itself to the bottom of the
# page, clears itself automatically after submit, and submits on Enter —
# no separate button needed at all.
typed_question = st.chat_input("Ask a question about the papers...")

# WHY check BOTH typed_question and pending_question?
# A question can arrive two ways now: typed at the bottom, or clicked from
# the sidebar's example buttons. We unify them into one variable so the
# rest of the code only has to handle "a question arrived," not "how."
question = typed_question or st.session_state.pop("pending_question", None)
# WHY .pop() with a default of None?
# Reads AND removes "pending_question" in one step — so a sidebar-clicked
# question fires exactly once, not on every rerun afterward.

if question:
    # 1. Show the user's own message immediately
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # 2. Call the API and show the assistant's reply
    with st.chat_message("assistant"):
        with st.spinner("Reading papers..."):
            try:
                response = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question, "n_results": 3},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                st.markdown(data["answer"])
                for s in data["sources"]:
                    st.caption(f"📄 {s['title']} · similarity {s['similarity']}")

                # Save the FULL exchange so the loop above can redraw it
                # on every future rerun (see the "WHY loop" comment above)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data["answer"],
                    "sources": data["sources"],
                })

            except requests.exceptions.RequestException as e:
                st.error(f"Couldn't reach the backend: {e}")