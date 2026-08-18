# Evelyn MVP

Evelyn is an AI-assisted, human-in-the-loop text moderation MVP for Vietnamese,
TikTok-first newsroom publishing. It provides a recommendation, not a final publishing
decision.

## MVP status

- [x] Layer 1 frame moderation: `POST /api/v1/moderate/frame`
- [x] Layer 2 full-script moderation: `POST /api/v1/moderate/script`
- [x] `PASS`, `REVIEW`, and `BLOCK` decisions with structured evidence
- [x] Synthetic development-policy context and policy references
- [x] Structured-output LLM gateway supporting OpenRouter, Groq, and Gemini
- [x] Offline deterministic mock mode for tests and local demos
- [x] Minimal Next.js UI for both moderation layers
- [x] Local demo company policies with create/delete controls

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

Open `http://localhost:3100`. Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`
for the local split frontend/API setup. Without it, the frontend calls same-origin `/api/v1`,
which is the Vercel deployment path.

## Configuration

Copy `.env.example` to your local environment and keep real credentials out of git.

```text
MODERATION_MODE=mock
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

`mock` is the default and is deterministic/offline. To use a real LLM, set
`MODERATION_MODE=llm` and `LLM_PROVIDER` to one of `openrouter`, `groq`, or `gemini`, along
with `LLM_API_KEY`. `LLM_MODEL` and `LLM_BASE_URL` are optional and default per provider:

```text
# OpenRouter (default provider)
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-5.4-mini
LLM_BASE_URL=https://openrouter.ai/api/v1

# Groq
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
LLM_BASE_URL=https://api.groq.com/openai/v1

# Gemini (OpenAI-compatible endpoint)
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.6-flash
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
```

The API key is read only from `LLM_API_KEY` in the environment. All three providers use the
same OpenAI-compatible Chat Completions structured JSON-schema interface. Only OpenRouter
requests additionally send `zdr=true`, `data_collection=deny`, and `require_parameters=true` —
Groq and Gemini do not support that field. The gateway retries one invalid response, then
returns an explicit provider-failure `REVIEW` fallback for any provider. This is not presented
as a completed content review and never converts missing evidence or invalid model output into
`PASS`.

**Gemini privacy note:** the free/unpaid Gemini API tier is for synthetic MVP smoke testing
only. Do not send confidential newsroom material, production policy documents, or
personal/sensitive data through it. Evelyn does not enable or claim Gemini zero-data-retention
(ZDR) — data handling depends entirely on your Gemini account/service tier; check Google's own
terms before using anything beyond synthetic test content.

## Demo flow

1. Enter a title and summary in **Layer 1**, then choose **Analyze frame**.
2. If Layer 1 is not `BLOCK`, enter the full Vietnamese script in **Layer 2** and choose
   **Analyze script**.
3. Review the decision, risk categories, quoted violations, rule references, and an optional
   fact-preserving suggested revision. If the provider is unavailable, the UI labels the
fail-safe result separately. A human editor makes the final decision.

## Company Policy Demo

The **Policy desk** at the top of the UI lets you select one of the two demo companies and
add local `REVIEW` or `BLOCK` keyword rules. Rules are stored in
`apps/api/app/runtime/company_policies.json`, which is ignored by git. In `mock` mode, a
matching company rule is included as policy evidence and can change the moderation decision.
This is a local demo facility, not multi-tenant production policy management. On Vercel
serverless, its filesystem is ephemeral: policy create/delete changes can disappear after a
function restart. Add durable database-backed storage before relying on it online.

## Vercel deployment

`vercel.json` deploys `apps/web` and `apps/api` as Vercel Services on one origin. Import the
repository with **Root Directory** left at the repository root, then add these Vercel Environment
Variables to Preview and Production:

```text
MODERATION_MODE=llm
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.6-flash
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_API_KEY=<Gemini key>
```

Keep `LLM_API_KEY` server-only. Never create `NEXT_PUBLIC_LLM_API_KEY`. After deployment, verify
`/health`, `/api/v1/moderate/frame`, `/api/v1/moderate/script`, then test the browser UI with
synthetic content only.

## Tests

```bash
cd apps/api
pytest
```

The test suite makes no external LLM calls. It covers Layer 1, Layer 2 `PASS`/`REVIEW`/
`BLOCK`, blank scripts, OpenRouter privacy payloads, strict schemas, invalid/inconsistent LLM
output, provider fail-safe behavior, and the empty-evidence safety rule.

## Deferred

- RAG and production policy ingestion
- Database and audit persistence
- Multi-model validation
- Authentication and multi-company support
- Uploads, conversation history, and policy administration
