# 🔬 AI Research Assistant

Chat with a collection of AI research papers using a full RAG (Retrieval-Augmented Generation) pipeline — from fetching papers off arXiv to a live, publicly deployed chat interface.

**Live demo:** [airesearchassistant.streamlit.app](https://airesearchassistant-6pkgybujxy6ayrkbrdgafz.streamlit.app)
**Backend API:** [ai-research-assistant-tzia.onrender.com](https://ai-research-assistant-tzia.onrender.com)

---

## What it does

Ask natural-language questions about a curated set of AI research papers (e.g. *"Which papers use neural networks?"*) and get answers grounded in the actual paper content, along with the source papers and similarity scores that back up the answer.

---

## Architecture

```
arXiv API → fetch_articles.py → data/*.json
                                     │
                                     ▼
                          summarize_articles.py
                          (Anthropic Claude API)
                                     │
                                     ▼
                          search_articles.py
                          (ChromaDB + embeddings)
                                     │
                                     ▼
                              api.py (FastAPI)
                          /ask · /search · /
                                     │
                                     ▼
                         app.py (Streamlit UI)
```

- **Retrieval:** ChromaDB vector store (17 deduplicated papers) with `DefaultEmbeddingFunction` (onnxruntime-based — no torch, chosen to fit within Render's free-tier 512MB RAM limit)
- **Generation:** Anthropic Claude API (`claude-haiku-4-5`)
- **Backend:** FastAPI, deployed on Render (free tier)
- **Frontend:** Streamlit, deployed on Streamlit Community Cloud

---

## Project structure

```
src/
├── fetch_articles.py      # Pulls papers from the arXiv API
├── summarize_articles.py  # Summarizes papers via the Anthropic API (LangChain)
├── search_articles.py     # Builds the RAG pipeline: ChromaDB + embeddings
├── api.py                 # FastAPI backend — /, /ask, /search
├── app.py                 # Streamlit chat frontend
├── requirements.txt
├── data/                  # Fetched paper JSON
└── chroma_db/             # Persisted vector store
```

---

## How it was built

Built incrementally in weekly phases, testing each layer before adding the next:

1. **Fetch** — arXiv paper fetching pipeline
2. **Summarize** — LangChain-based summarization via the Anthropic API
3. **Retrieve** — RAG pipeline with ChromaDB + embeddings
4. **Serve** — FastAPI backend with `/ask` (full RAG) and `/search` (retrieval-only) endpoints, Pydantic models, error handling
5. **Chat** — Streamlit frontend, built up from a plain text input → button → real API call → formatted output → full chat history with `session_state`

---

## Running locally

```bash
# 1. Clone and set up
git clone https://github.com/neerajgontala/AI_Research_Assistant.git
cd AI_Research_Assistant/src
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Add your Anthropic API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# 3. Fetch papers, build the index (first-time setup)
python fetch_articles.py
python search_articles.py

# 4. Run the backend
uvicorn api:app --reload

# 5. In a separate terminal, run the frontend
streamlit run app.py
```

By default, `app.py` points at the live Render deployment. To point it at your local backend instead, set:

```bash
export API_URL=http://localhost:8000
```

---

## Deployment

| Layer    | Platform                  | Notes                                                              |
|----------|----------------------------|----------------------------------------------------------------------|
| Backend  | Render (free tier)         | Root dir `src`, start command `uvicorn api:app --host 0.0.0.0 --port $PORT`. Spins down on inactivity — first request after idle can take ~50s. |
| Frontend | Streamlit Community Cloud  | Main file path `src/app.py`                                          |

---

## Known limitations

- **Free-tier cold starts:** the Render backend sleeps after inactivity; the first query after idle time can take up to ~50 seconds to respond.

## Changelog

- Deduplicated the ChromaDB collection — removed 3 duplicate paper entries (20 → 17 papers loaded), verified with a robot-manipulation query returning distinct results
- Fixed an `os.getenv()` argument-order bug in `app.py` where `API_URL` was passed as the key instead of the default, causing it to resolve to `None`
- Deployed frontend to Streamlit Community Cloud; full pipeline now live end-to-end

---

## Tech stack

`Python` · `FastAPI` · `Streamlit` · `ChromaDB` · `LangChain` · `Anthropic Claude API` · `arXiv API` · `Render` · `Streamlit Community Cloud`