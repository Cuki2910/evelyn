# Evelyn MVP

Evelyn is an AI-assisted, human-in-the-loop text moderation MVP for Vietnamese,
TikTok-first newsroom publishing. It provides a recommendation, not a final publishing
decision.

## MVP status

- [x] Layer 1 frame moderation: `POST /api/v1/moderate/frame`
- [x] Layer 2 full-script moderation: `POST /api/v1/moderate/script`
- [x] `PASS`, `REVIEW`, and `BLOCK` decisions with structured evidence
- [x] Synthetic development-policy context and policy references
- [x] OpenRouter structured-output LLM gateway with privacy routing controls
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

`mock` is the default and is deterministic/offline. To use the real OpenRouter integration,
set `MODERATION_MODE=llm` along with these backend variables:

```text
LLM_PROVIDER=openrouter
LLM_API_KEY=...
LLM_MODEL=openai/gpt-5.4-mini
LLM_BASE_URL=https://openrouter.ai/api/v1
```

The API key is read only from `LLM_API_KEY` in the environment. The gateway uses the
OpenRouter Chat Completions structured JSON-schema interface and sends `zdr=true`,
`data_collection=deny`, and `require_parameters=true` on every request. It retries one
invalid response, then returns an explicit provider-failure `REVIEW` fallback. This is not
presented as a completed content review and never converts missing evidence or invalid model
output into `PASS`.

## Demo flow

1. Enter a title and summary in **Layer 1**, then choose **Analyze frame**.
2. If Layer 1 is not `BLOCK`, enter the full Vietnamese script in **Layer 2** and choose
   **Analyze script**.
3. Review the decision, risk categories, quoted violations, rule references, and an optional
   fact-preserving suggested revision. If the provider is unavailable, the UI labels the
   fail-safe result separately. A human editor makes the final decision.

## Tests

```bash
cd apps/api
pytest
```

The test suite makes no external LLM calls. It covers Layer 1, Layer 2 `PASS`/`REVIEW`/
`BLOCK`, blank scripts, OpenRouter privacy payloads, strict schemas, invalid/inconsistent LLM
output, provider fail-safe behavior, and the empty-evidence safety rule.

## Deferred

- RAG and policy ingestion
- Database and audit persistence
- Multi-model validation
- Authentication and multi-company support
- Uploads, conversation history, and policy administration
