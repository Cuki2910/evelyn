# Evelyn

Evelyn is an AI-assisted text moderation system for newsroom social-media publishing workflows.

## Current scope

- Vietnamese text only
- TikTok-first moderation
- Two-stage workflow: frame screening -> full script review
- AI recommendation states: `PASS`, `REVIEW`, `BLOCK`
- Human-in-the-loop final decision
- `BLOCK` at Layer 1 stops the pipeline
- Only `REVIEW` generates a revised script
- Revised scripts must preserve factual meaning
- All applicable policy groups must pass for the final recommendation to be `PASS`

## Architecture

Evelyn starts as a modular monolith in a monorepo:

```text
apps/web      Next.js frontend
apps/api      FastAPI backend
evals         AI evaluation datasets and runners
docs          architecture and policy-system documentation
infra         local/dev infrastructure
scripts       development utilities
```

Core backend modules:

```text
moderation    two-stage moderation orchestration
policy        ingestion, normalization, rules, retrieval, versioning
revision      factual-preserving script revision and validation
llm           single gateway for all external model calls
audit         decision traceability
feedback      editor override/evaluation data
```

## Decision rule

```text
if any applicable policy result is BLOCK:
    final = BLOCK
elif any applicable policy result is REVIEW:
    final = REVIEW
else:
    final = PASS
```

Uncertainty must resolve to `REVIEW`, never `PASS`.

## Security

Production newsroom content, real policy files, API credentials, and other confidential material must never be committed to this repository.

External LLM access must be routed through the backend LLM gateway and configured using environment variables or a secrets manager.

## Development

```bash
cd apps/api

python -m venv .venv

# Activate the virtual environment.
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Test

```bash
cd apps/api
pytest
```

### Example request

```bash
curl -X POST \
  http://localhost:8000/api/v1/moderate/frame \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Điều tra vụ xô xát tại Hà Nội",
    "summary": "Một người bị đâm và được đưa đi cấp cứu."
  }'
```

Current moderation logic is a deterministic development mock and must not be treated as production TikTok policy enforcement.

## Development status

Layer 1 moderation vertical slice implemented. Policy ingestion, production policy evaluation, external models, persistence, and Layer 2 remain out of scope.
