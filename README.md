# Support Ticket Agent

AI agent that triages customer support tickets (Vietnamese + English) and drafts replies grounded in a knowledge base. A human always reviews and sends.

**Status:** Sprint 1 — API skeleton and CSV validation. No LLM key needed yet.

## What it will do
1. Classify each ticket: category, priority, sentiment.
2. Call tools to search the knowledge base and look up order status.
3. Draft a reply with exact KB citations, or escalate to a human.
4. Validate the draft: citations must match the source, order facts must come from tools.

## Stack
Python 3.11, FastAPI, Pydantic v2, pandas, pytest + HTTPX.

## Setup (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.main:app --reload
pytest
```
Swagger UI: http://127.0.0.1:8000/docs

## Project layout
```text
src/
  api/routes/   HTTP endpoints only
  services/     use-case logic
  schemas/      Pydantic contracts + taxonomy
  llm/          model-provider interface, FakeLLM
  agent/        classifier, agent loop, draft validator
  tools/        pure Python tools the agent can call
data/
  raw/          synthetic sample tickets
  kb/           knowledge-base articles
  mock/         fake order system
  eval/         labeled gold set
evals/          evaluation runner
docs/           brief, PRD, data spec, agent design, eval plan, roadmap
```

## Results
_Metrics will be added after Sprint 6 (see `docs/05_evaluation_plan.md`)._
