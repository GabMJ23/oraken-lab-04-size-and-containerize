"""Lab 4, Part B: a tiny search service to put in a container.

You do not need to change this file, except for the one-line change in
Part B, step 6 (the VERSION line below).

It reads two settings from environment variables:
  DATABASE_URL  where the database is, e.g. postgresql://user:password@host:5432/name
  PORT          the port to listen on (default 8000)

Endpoints:
  GET /health      200 if the database answers, 503 if it does not
  GET /search?q=   the documents that match the words in q

Start it with:  python -m app.main
"""
import json
import os
import pathlib
import re

import psycopg
import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

VERSION = "1"  # Part B, step 6: change this line, rebuild, and time the rebuild.

DOCUMENTS = json.loads(pathlib.Path(__file__).with_name("documents.json").read_text(encoding="utf-8"))

app = FastAPI(title="Lab 4 search service")


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def check_database(url):
    """Connect to the database and ask it one question. Returns (ok, details)."""
    if not url:
        return False, {"database": "DATABASE_URL is not set"}
    try:
        with psycopg.connect(url, connect_timeout=3) as conn:
            row = conn.execute(
                "SELECT default_version FROM pg_available_extensions WHERE name = 'vector'"
            ).fetchone()
        return True, {"database": "ok", "pgvector": row[0] if row else "not available"}
    except Exception as exc:  # any failure means "not reachable"; never crash the health check
        first_line = str(exc).strip().splitlines()[0] if str(exc).strip() else type(exc).__name__
        return False, {"database": "unreachable", "detail": first_line[:200]}


@app.get("/health")
def health():
    ok, details = check_database(os.environ.get("DATABASE_URL", ""))
    body = {"status": "ok" if ok else "error", "version": VERSION, **details}
    return JSONResponse(body, status_code=200 if ok else 503)


@app.get("/search")
def search(q: str = Query(..., min_length=1, description="words to look for")):
    terms = set(words(q))
    results = []
    for doc in DOCUMENTS:
        score = sum(1 for w in words(doc["title"] + " " + doc["text"]) if w in terms)
        if score:
            results.append({"id": doc["id"], "title": doc["title"], "score": score})
    results.sort(key=lambda r: (-r["score"], r["id"]))
    return {"query": q, "count": len(results), "results": results}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
