"use client";

import { FormEvent, useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

type Decision = "PASS" | "REVIEW" | "BLOCK";
type Violation = { text: string; category: string; reason: string; suggested_action?: string };
type PolicyReference = { rule_id: string; category?: string; reason: string };
type ModerationResult = {
  decision: Decision;
  risk_level: string;
  risk_categories: string[];
  violations: Violation[];
  policy_references?: PolicyReference[];
  policy_results?: PolicyReference[];
  reason: string;
  revised_script?: string | null;
  requires_human_review?: boolean;
  analysis_status: "COMPLETE" | "PROVIDER_ERROR";
  provider_error: string | null;
};

function DecisionBadge({ decision }: { decision: Decision }) {
  return <span className={`decision decision-${decision.toLowerCase()}`}>{decision}</span>;
}

function ResultPanel({ result }: { result: ModerationResult | null }) {
  if (!result) {
    return <div className="result-placeholder">Kết quả moderation sẽ xuất hiện ở đây.</div>;
  }

  const policies = result.policy_references || result.policy_results || [];
  const providerFailed = result.analysis_status === "PROVIDER_ERROR";
  return (
    <section className="result-panel" aria-live="polite">
      {providerFailed ? (
        <div className="provider-warning" role="alert">
          <strong>Moderation provider unavailable.</strong>
          <p>{result.provider_error}</p>
          <small>This fail-safe REVIEW is not a completed content assessment.</small>
        </div>
      ) : null}
      <div className="result-heading">
        <span>Khuyến nghị</span>
        <DecisionBadge decision={result.decision} />
      </div>
      <p className="result-reason">{result.reason}</p>
      <dl className="risk-list">
        <div><dt>Risk level</dt><dd>{result.risk_level}</dd></div>
        <div><dt>Categories</dt><dd>{result.risk_categories.length ? result.risk_categories.join(", ") : "Không có"}</dd></div>
      </dl>
      {result.violations.length > 0 ? (
        <div className="evidence">
          <h3>Đoạn bị flag</h3>
          {result.violations.map((violation, index) => (
            <article className="evidence-item" key={`${violation.category}-${index}`}>
              <q>{violation.text}</q>
              <p><strong>{violation.category}</strong> — {violation.reason}</p>
              {violation.suggested_action ? <small>Suggested action: {violation.suggested_action}</small> : null}
            </article>
          ))}
        </div>
      ) : null}
      {policies.length > 0 ? (
        <div className="evidence">
          <h3>Policy rules</h3>
          {policies.map((policy, index) => (
            <p className="policy" key={`${policy.rule_id}-${index}`}><code>{policy.rule_id}</code> {policy.reason}</p>
          ))}
        </div>
      ) : null}
      {result.revised_script ? (
        <div className="revision">
          <h3>Suggested revision</h3>
          <p>{result.revised_script}</p>
        </div>
      ) : null}
      {result.requires_human_review ? <p className="human-note">Human editor makes the final publishing decision.</p> : null}
    </section>
  );
}

async function postModeration(path: string, body: object): Promise<ModerationResult> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Không thể xử lý yêu cầu moderation.");
  }
  return response.json();
}

export default function Home() {
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [scriptTitle, setScriptTitle] = useState("");
  const [script, setScript] = useState("");
  const [frameResult, setFrameResult] = useState<ModerationResult | null>(null);
  const [scriptResult, setScriptResult] = useState<ModerationResult | null>(null);
  const [loading, setLoading] = useState<"frame" | "script" | null>(null);
  const [error, setError] = useState("");

  async function analyzeFrame(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading("frame");
    setError("");
    try {
      setFrameResult(await postModeration("/moderate/frame", { title, summary }));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Đã có lỗi xảy ra.");
    } finally {
      setLoading(null);
    }
  }

  async function analyzeScript(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading("script");
    setError("");
    try {
      setScriptResult(await postModeration("/moderate/script", { title: scriptTitle || undefined, script }));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Đã có lỗi xảy ra.");
    } finally {
      setLoading(null);
    }
  }

  return (
    <main>
      <header className="masthead">
        <p className="eyebrow">VIETNAMESE NEWS SAFETY DESK</p>
        <h1>Evelyn<span>.</span></h1>
        <p>Moderation assistance for TikTok-first newsroom publishing. Recommendations only; editors decide.</p>
      </header>
      {error ? <p className="error" role="alert">{error}</p> : null}
      <div className="workbench">
        <section className="moderation-card">
          <div className="card-intro"><p className="step">01 / LAYER 1</p><h2>News frame</h2></div>
          <form onSubmit={analyzeFrame}>
            <label>Title<input value={title} onChange={(event) => setTitle(event.target.value)} required /></label>
            <label>Summary<textarea value={summary} onChange={(event) => setSummary(event.target.value)} rows={4} /></label>
            <button disabled={loading !== null} type="submit">{loading === "frame" ? "Analyzing..." : "Analyze frame"}</button>
          </form>
          <ResultPanel result={frameResult} />
        </section>
        <section className="moderation-card">
          <div className="card-intro"><p className="step">02 / LAYER 2</p><h2>Full script</h2></div>
          <form onSubmit={analyzeScript}>
            <label>Title <span>(optional)</span><input value={scriptTitle} onChange={(event) => setScriptTitle(event.target.value)} /></label>
            <label>Script<textarea value={script} onChange={(event) => setScript(event.target.value)} rows={9} required /></label>
            <button disabled={loading !== null} type="submit">{loading === "script" ? "Analyzing..." : "Analyze script"}</button>
          </form>
          <ResultPanel result={scriptResult} />
        </section>
      </div>
    </main>
  );
}
