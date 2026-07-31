import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import json
import os
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv() #loads your .env file

llm = ChatAnthropic(model="claude-haiku-4-5")


def fetch_arxiv_articles(topic, max_results=10):
    # Build the URL — like typing a search into a website
    params = urllib.parse.urlencode({
        "search_query": f"all:{topic}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    url = f"https://export.arxiv.org/api/query?{params}"
    print(f"Fetching articles about: {topic}...")

    # Send the request (like clicking "Search")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "arxiv-fetcher/1.0"}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                xml_data = response.read()
            break
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            if attempt == 2:
                raise RuntimeError(
                    "Failed to fetch articles from arXiv after 3 attempts. "
                    f"Last error: {exc}"
                ) from exc
            time.sleep(2 ** attempt)

    # arXiv sends back XML — we need to read through it
    root = ET.fromstring(xml_data)
    ns = "http://www.w3.org/2005/Atom"
    articles = []

    for entry in root.findall(f"{{{ns}}}entry"):
        authors = [
            a.find(f"{{{ns}}}name").text
            for a in entry.findall(f"{{{ns}}}author")
            if a.find(f"{{{ns}}}name") is not None
        ]
        article = {
            "title":     entry.findtext(f"{{{ns}}}title", "").strip(),
            "summary":   entry.findtext(f"{{{ns}}}summary", "").strip(),
            "authors":   authors,
            "published": entry.findtext(f"{{{ns}}}published", "").strip(),
            "link":      next(
                (l.attrib["href"] for l in entry.findall(f"{{{ns}}}link")
                 if l.attrib.get("type") == "text/html"), ""
            ),
        }
        articles.append(article)

    return articles

def save_to_json(articles, topic):
    # Create a data/ folder if it doesn't exist
    os.makedirs("data", exist_ok=True)

    # Build the filename using today's date + time
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"data/{topic.replace(' ', '_')}_{timestamp}.json"

    # Wrap the articles in a neat package with metadata
    output = {
        "topic": topic,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total": len(articles),
        "articles": articles,
    }

    with open(filename, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved {len(articles)} articles to: {filename}")
    return filename

if __name__ == "__main__":
    # --- Run it ---
    topic = "big data"     
    try:
        articles = fetch_arxiv_articles(topic, max_results=5)
        save_to_json(articles, topic)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
