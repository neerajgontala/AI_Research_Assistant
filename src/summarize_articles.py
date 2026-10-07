import os
import json 
import glob  
from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic  
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


load_dotenv()

llm = ChatAnthropic(model="claude-haiku-4-5")

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert AI research assistant. 
     Your job is to read academic paper abstracts and produce clear, concise summaries that a developer can quickly understand.
 
Always respond in this exact JSON format:
{{
  "one_liner": "One sentence summary of what this paper is about",
  "key_contribution": "The main thing this paper introduces or proves",
  "why_it_matters": "Why an AI engineer should care about this",
  "keywords": ["keyword1", "keyword2", "keyword3"]
}}"""),
    
    ("human", """Please summarize this resesarch paper:
     Title: {title}
     Abstract: {abstract}""")
])

chain = prompt | llm | StrOutputParser()


def load_all_articles(data_folder: str) -> list:
    """
    Loads all JSON files from your data/ folder.
    Returns a flat list of all articles across all files.
    """
    all_articles = []
    
    # find all .JSON files in the data folder
    pattern = os.path.join(data_folder,"*.json") #builds a file path for any operating system carefully.
    json_files = [f for f in glob.glob(pattern) 
              if not os.path.basename(f).startswith("summaries_")] #This filters out any file whose name starts with "summaries_" — so your output files never get read back as input.
    # json_files = glob.glob(pattern)
    
    if not json_files:
         print(f"❌ No JSON files found in: {data_folder}")
         print("Run fetch_articles.py first!")
         return[]
    print(f" Found {len(json_files)} JSON file(s) to process:")
    
    for filepath in json_files:
        filename = os.path.basename(filepath)
        
        with open(filepath,"r", encoding="utf-8") as f:
            data = json.load(f)
         
        # to unwrap the articles in fetch_articles.py file    
        if isinstance(data, dict) and "articles" in data:
            articles = data["articles"]
            topic = data.get("topic", "unknown")
            if not articles:
                print(f"   ⚠️  Skipping {filename} — no articles found")
                continue
        elif isinstance(data, list): 
            articles = data # haldles the older format too
            
            topic = "unknown"
        else:
            articles = []
            
        print(f"   ✅ {filename} → {len(articles)} articles (topic: {topic})")
        all_articles.extend(articles) 

    return all_articles


def summarize_article(article: dict) -> dict:
    """
    sends one article to claude and returns a structured summary.
    """
    title = article.get("title", "untitled")
    abstract = article.get("summary", "No abstract available.") # In fetch_articles.py the abstract of the papers is stored under the key "summary" - so thats the key we read here

    print(f"\n Summarizing: {title[:60]}...")
    
    try:
        raw_response = chain.invoke( #fills the title and abstract into the prompt template
            {
            "title": title,
            "abstract": abstract
            }
        )
        
        cleaned_response = raw_response.strip()
        if cleaned_response.startswith("```"):
            # strip a leading ```json / ``` fence and trailing ``` that claude sometimes wraps the JSON in
            cleaned_response = cleaned_response.strip("`")
            cleaned_response = cleaned_response.removeprefix("json").strip()

        summary=json.loads(cleaned_response) # converts string produced by claude in to actuall python dictioinary(JSON) format.

        return {
                "title":      title,
                "authors":    article.get("authors", []),
                "published":  article.get("published", ""),
                "link":       article.get("link", ""),
                "summary":    summary      # Claude's structured summary
            }
    
    except json.JSONDecodeError:
        print(f" ⚠️ Claude didn't return clear JSON for this article. Saving raw response.")
        return{
            "title":     title,
            "authors":   article.get("authors", []),
            "published": article.get("published", ""),
            "link":      article.get("link", ""),
            "raw_response": raw_response
        }
        
    except Exception as e:
        print(f" ❌ Error summarizing article:{e}")
        return {"title": title,"error": str(e)}
    
    
def save_summaries(summaries: list,data_folder: str)->str:
    """
    Saves all summaries to a single JSON file.
    WHY a new file? Keep raw data, separate from processed data.
    That way you can always re-run the summarizer without re-fetching.
    """
    
    from datetime import datetime
    
    os.makedirs(data_folder, exist_ok=True)
    filename = os.path.join(
        data_folder,
        f"summaries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
    
    output={
        "generated_at":     datetime.now().isoformat(),
        "total_articles":   len(summaries),
        "summaries":        summaries   
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        
    print(f"\n 📁 Saved {len(summaries)} summaries -> {filename}")
    return filename




if __name__ =="__main__":
    print("=" * 55)
    print("AI Research Assistant - LLM Summarizer")
    print("=" * 55)
    
    DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    
    # To read all JSON files
    articles = load_all_articles(DATA_FOLDER) 
    
    if not articles: #if no articles are loaded 
        exit() # exit instead of crashing with a confused error
        
    print(f"\n Total articles to summarize: {len(articles)}")
    
    #testing with 3 first to make sure 
    articles_to_process = articles
    print(f"Processing first{len(articles_to_process)} articles (test run)...")
    
    #summarize each article
    summaries = []
    for i, article in enumerate(articles_to_process,1):
        print(f"[{i}/{len(articles_to_process)}]", end="")
        result = summarize_article(article)
        summaries.append(result)
        
    #preview of the summary
    print("\n\n---- Preview of first summary ----")   
    if summaries and "summary" in summaries[0]:
        s = summaries[0]["summary"]
        print(f"Title:              {summaries[0]['title'][:70]}")
        print(f"One liner:          {s.get('one liner', '')}")
        print(f"Key contribution:   {s.get('Key_contribution', '')}")
        print(f"Why it matters:     {s.get('why_it_matters', '')}")
        print(f"Keywords:           {', '.join(s.get('keywords',[]))}")
        
    #save all the summaries
    save_summaries(summaries, DATA_FOLDER)
     
    