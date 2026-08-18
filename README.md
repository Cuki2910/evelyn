# Evelyn MVP

Evelyn is an AI-assisted, human-in-the-loop text moderation MVP for Vietnamese,
TikTok-first newsroom publishing. It provides a recommendation, not a final publishing
decision.

## MVP status

- [x] Layer 1 frame moderation: `POST /api/v1/moderate/frame`
- [x] Layer 2 full-script moderation: `POST /api/v1/moderate/script`
- [x] `PASS`, `REVIEW`, and `BLOCK` decisions with structured evidence
- [x] Synthetic development-policy context and policy references
- [x] OpenAI-compatible structured-output LLM gateway
- [x] Offline deterministic mock mode for tests and local demos
- [x] Minimal Next.js UI for both moderation layers

The development policy is synthetic and is **not official TikTok policy**. It exists only
to support local demos of violence, graphic violence, drugs, weapons, sexual content,
self-harm, hate, and crime moderation.

## Run the MVP

Backend:

```bash
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend (in a second terminal):

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`. The frontend defaults to the local API at
`http://localhost:8000/api/v1`.

## Configuration

Copy `.env.example` to your local environment and keep real credentials out of git.

```text
MODERATION_MODE=mock
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

`mock` is the default and is deterministic/offline. To use the real provider integration,
set `MODERATION_MODE=llm` along with these backend variables:

```text
LLM_PROVIDER=openai_compatible
LLM_API_KEY=...
LLM_MODEL=...
LLM_BASE_URL=https://api.openai.com/v1
```

The gateway uses the OpenAI-compatible Chat Completions structured JSON-schema interface.
It retries one invalid response, then returns a safe `REVIEW` fallback. It never converts
missing evidence or invalid model output into `PASS`.

## Demo flow

1. Enter a title and summary in **Layer 1**, then choose **Analyze frame**.
2. If Layer 1 is not `BLOCK`, enter the full Vietnamese script in **Layer 2** and choose
   **Analyze script**.
3. Review the decision, risk categories, quoted violations, rule references, and an optional
   fact-preserving suggested revision. A human editor makes the final decision.

## Tests

```bash
cd apps/api
pytest
```

The test suite makes no external LLM calls. It covers Layer 1, Layer 2 `PASS`/`REVIEW`/
`BLOCK`, blank scripts, invalid structured LLM output, and the empty-evidence safety rule.

## Deferred

- RAG and policy ingestion
- Database and audit persistence
- Multi-model validation
- Authentication and multi-company support
- Uploads, conversation history, and policy administration
