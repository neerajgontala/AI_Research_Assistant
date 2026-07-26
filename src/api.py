from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

from search_articles import (
    load_papers,
    build_vector_store,
    search_papers,
    answer_question,
    DATA_FOLDER,
)

app = FastAPI()

print("Loading papers and vector store...")
papers = load_papers(DATA_FOLDER)
collection = build_vector_store(papers)
print(f"Ready! {collection.count()} papers loaded.\n")

@app.get("/") # when someone sends a GET request to the URL /, run the funtion below
def root():
    return{
        "status":"online",
        "papers_loaded": collection.count()
        }

class QuestionRequest(BaseModel):
    question: str
    n_results: int = 3 
    
class PaperResult(BaseModel):
    title: str
    authors: str
    link: str
    similarity: float
    
class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: List[PaperResult]
    
@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    relevant_papers = search_papers(
        query=request.question,
        collection=collection,
        n_results=request.n_results,
    )
    answer = answer_question(request.question, relevant_papers)
    return {
        "question"  : request.question,
        "answer"    : answer,
       "sources": [
    {
        "title": p["title"],
        "authors": p["authors"],
        "link": p["link"],
        "similarity": round(1-p["distance"],4)
    }
    for p in relevant_papers
]
    }
    
    
@app.post("/search")
def search_only(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail = "Question cannot be empty")
    
    relevant_papers = search_papers(
        query = request.question,
        collection= collection,
        n_results=request.n_results
    )
    
    return{
        "query": request.question,
        "results": [
            {
                "title": p["title"],
                "authors": p["authors"],
                "link": p["link"],
                "similarity": round(1 - p["distance"], 4),
            }
            for p in relevant_papers
        ],
    }