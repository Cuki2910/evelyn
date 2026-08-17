# Evelyn Technical Architecture v0.1

## Product boundary

Evelyn evaluates Vietnamese textual content only. It does not evaluate video, imagery, or raw audio.

The system provides recommendations to a human media reviewer. It never publishes content autonomously.

## Moderation flow

```text
Layer 1: frame/title/basic information
  -> PASS / REVIEW / BLOCK
  -> BLOCK stops the automated pipeline
  -> PASS or REVIEW can continue to Layer 2

Layer 2: complete publish-ready script
  -> evaluate all applicable policy groups
  -> PASS / REVIEW / BLOCK
  -> REVIEW may generate a factual-preserving revised script
  -> revised script is checked for factual consistency and policy compliance
  -> human reviewer makes the final decision
```

## Policy decision semantics

A final `PASS` requires every applicable policy group to return `PASS`.

```text
any BLOCK  -> BLOCK
else any REVIEW -> REVIEW
else -> PASS
```

Uncertain cases must resolve to `REVIEW`.

## Policy layers

Initial policy groups:

1. Vietnamese legal/government requirements
2. TikTok policy
3. company-specific policy

Policy source documents are retained with immutable versions. Historical analyses retain the versions used at analysis time. Re-checking against newer policy creates a new analysis rather than overwriting history.

## Policy ingestion

```text
raw Vietnamese text
  -> normalization
  -> section extraction
  -> rule candidate extraction
  -> structured policy representation
  -> versioned active policy
```

Company-specific policy is tenant scoped. The data model should carry `tenant_id` from the start even while the MVP serves a single organization.

## LLM boundary

All external model traffic must flow through one backend LLM gateway. Application modules must not call providers directly.

Initial model roles:

- classifier/extractor
- policy reasoner/revision generator
- optional validator added only when evaluation justifies it

## Revision constraints

Only `REVIEW` produces a revised script. Revisions may keep, rewrite, or remove text only when factual substance is preserved.

The system must flag material changes involving facts, entities, numbers, chronology, attribution, causality, or important omissions.

## Auditability

Each analysis should retain enough information to reconstruct the decision:

- tenant
- input hash
- policy names and versions
- matched rule IDs
- source section/span
- model role/model version
- prompt version
- content violation span
- decision and explanation
- revision, if any
- human feedback/override
