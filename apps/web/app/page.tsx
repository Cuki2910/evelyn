"use client";

import { FormEvent, useEffect, useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
const DEMO_COMPANIES = [
  { id: "evelyn-news", name: "Evelyn News" },
  { id: "city-desk", name: "City Desk" },
];

type Decision = "PASS" | "REVIEW" | "BLOCK";
type Company = { id: string; name: string };
type CompanyPolicy = {
  id: string;
  company_id: string;
  title: string;
  keywords: string[];
  decision: Exclude<Decision, "PASS">;
  reason: string;
  rule_id: string;
};
type PolicyCatalog = { companies: Company[]; policies: CompanyPolicy[] };
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

async function requestJson<Response>(path: string, options?: RequestInit): Promise<Response> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "The request could not be completed.");
  }
  return response.json() as Promise<Response>;
}

function DecisionBadge({ decision }: { decision: Decision }) {
  return <span className={`decision decision-${decision.toLowerCase()}`}>{decision}</span>;
}

function ResultPanel({ result }: { result: ModerationResult | null }) {
  if (!result) {
    return <div className="result-placeholder">Moderation result will appear here.</div>;
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
        <span>Recommendation</span>
        <DecisionBadge decision={result.decision} />
      </div>
      <p className="result-reason">{result.reason}</p>
      <dl className="risk-list">
        <div><dt>Risk level</dt><dd>{result.risk_level}</dd></div>
        <div><dt>Categories</dt><dd>{result.risk_categories.length ? result.risk_categories.join(", ") : "None"}</dd></div>
      </dl>
      {result.violations.length > 0 ? (
        <div className="evidence">
          <h3>Flagged text</h3>
          {result.violations.map((violation, index) => (
            <article className="evidence-item" key={`${violation.category}-${index}`}>
              <q>{violation.text}</q>
              <p><strong>{violation.category}</strong> - {violation.reason}</p>
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

type PolicyDeskProps = {
  catalog: PolicyCatalog;
  selectedCompany: string;
  title: string;
  keywords: string;
  decision: Exclude<Decision, "PASS">;
  reason: string;
  loading: boolean;
  error: string;
  onCompanyChange: (value: string) => void;
  onTitleChange: (value: string) => void;
  onKeywordsChange: (value: string) => void;
  onDecisionChange: (value: Exclude<Decision, "PASS">) => void;
  onReasonChange: (value: string) => void;
  onCreate: (event: FormEvent<HTMLFormElement>) => void;
  onDelete: (policyId: string) => void;
};

function PolicyDesk({
  catalog,
  selectedCompany,
  title,
  keywords,
  decision,
  reason,
  loading,
  error,
  onCompanyChange,
  onTitleChange,
  onKeywordsChange,
  onDecisionChange,
  onReasonChange,
  onCreate,
  onDelete,
}: PolicyDeskProps) {
  const companies = catalog.companies.length ? catalog.companies : DEMO_COMPANIES;
  const policies = catalog.policies.filter((policy) => policy.company_id === selectedCompany);

  return (
    <section className="policy-desk" aria-labelledby="policy-desk-title">
      <div className="policy-heading">
        <div>
          <p className="step">00 / COMPANY POLICY</p>
          <h2 id="policy-desk-title">Policy desk</h2>
          <p>Demo-only policies are saved locally and applied to the selected company in mock mode.</p>
        </div>
        <label>
          Active company
          <select value={selectedCompany} onChange={(event) => onCompanyChange(event.target.value)}>
            {companies.map((company) => <option key={company.id} value={company.id}>{company.name}</option>)}
          </select>
        </label>
      </div>
      {error ? <p className="error" role="alert">{error}</p> : null}
      <div className="policy-grid">
        <div className="policy-list">
          <h3>Active rules</h3>
          {policies.length ? policies.map((policy) => (
            <article className="company-policy" key={policy.id}>
              <div><DecisionBadge decision={policy.decision} /><code>{policy.rule_id}</code></div>
              <h4>{policy.title}</h4>
              <p>{policy.reason}</p>
              <small>Keywords: {policy.keywords.join(", ")}</small>
              <button type="button" className="text-button" disabled={loading} onClick={() => onDelete(policy.id)}>Remove</button>
            </article>
          )) : <p className="empty-policy">No custom rules for this company yet.</p>}
        </div>
        <form className="policy-form" onSubmit={onCreate}>
          <h3>Add policy</h3>
          <label>Rule title<input value={title} onChange={(event) => onTitleChange(event.target.value)} required minLength={3} /></label>
          <label>Keywords <span>comma-separated</span><input value={keywords} onChange={(event) => onKeywordsChange(event.target.value)} required /></label>
          <label>Action<select value={decision} onChange={(event) => onDecisionChange(event.target.value as Exclude<Decision, "PASS">)}><option value="REVIEW">REVIEW</option><option value="BLOCK">BLOCK</option></select></label>
          <label>Editor note<textarea value={reason} onChange={(event) => onReasonChange(event.target.value)} rows={3} required minLength={3} /></label>
          <button disabled={loading} type="submit">{loading ? "Saving..." : "Add policy"}</button>
        </form>
      </div>
    </section>
  );
}

async function postModeration(path: string, body: object): Promise<ModerationResult> {
  return requestJson<ModerationResult>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
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
  const [catalog, setCatalog] = useState<PolicyCatalog>({ companies: [], policies: [] });
  const [selectedCompany, setSelectedCompany] = useState("evelyn-news");
  const [policyTitle, setPolicyTitle] = useState("");
  const [policyKeywords, setPolicyKeywords] = useState("");
  const [policyDecision, setPolicyDecision] = useState<Exclude<Decision, "PASS">>("REVIEW");
  const [policyReason, setPolicyReason] = useState("");
  const [policyLoading, setPolicyLoading] = useState(false);
  const [policyError, setPolicyError] = useState("");

  useEffect(() => {
    let active = true;
    void requestJson<PolicyCatalog>("/policies")
      .then((nextCatalog) => { if (active) setCatalog(nextCatalog); })
      .catch(() => { if (active) setPolicyError("Could not load local company policies."); });
    return () => { active = false; };
  }, []);

  async function analyzeFrame(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading("frame");
    setError("");
    try {
      setFrameResult(await postModeration("/moderate/frame", { title, summary, company_id: selectedCompany }));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Moderation request failed.");
    } finally {
      setLoading(null);
    }
  }

  async function analyzeScript(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading("script");
    setError("");
    try {
      setScriptResult(await postModeration("/moderate/script", { title: scriptTitle || undefined, script, company_id: selectedCompany }));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Moderation request failed.");
    } finally {
      setLoading(null);
    }
  }

  async function createPolicy(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPolicyLoading(true);
    setPolicyError("");
    try {
      const policy = await requestJson<CompanyPolicy>("/policies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_id: selectedCompany,
          title: policyTitle,
          keywords: policyKeywords.split(",").map((keyword) => keyword.trim()).filter(Boolean),
          decision: policyDecision,
          reason: policyReason,
        }),
      });
      setCatalog((current) => ({
        companies: current.companies.length ? current.companies : DEMO_COMPANIES,
        policies: [...current.policies, policy],
      }));
      setPolicyTitle("");
      setPolicyKeywords("");
      setPolicyReason("");
    } catch (requestError) {
      setPolicyError(requestError instanceof Error ? requestError.message : "Could not save this policy.");
    } finally {
      setPolicyLoading(false);
    }
  }

  async function deletePolicy(policyId: string) {
    setPolicyLoading(true);
    setPolicyError("");
    try {
      const response = await fetch(`${API_BASE_URL}/policies/${policyId}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Could not remove this policy.");
      setCatalog((current) => ({ ...current, policies: current.policies.filter((policy) => policy.id !== policyId) }));
    } catch (requestError) {
      setPolicyError(requestError instanceof Error ? requestError.message : "Could not remove this policy.");
    } finally {
      setPolicyLoading(false);
    }
  }

  return (
    <main>
      <header className="masthead">
        <p className="eyebrow">VIETNAMESE NEWS SAFETY DESK</p>
        <h1>Evelyn<span>.</span></h1>
        <p>Moderation assistance for TikTok-first newsroom publishing. Recommendations only; editors decide.</p>
      </header>
      <PolicyDesk
        catalog={catalog}
        selectedCompany={selectedCompany}
        title={policyTitle}
        keywords={policyKeywords}
        decision={policyDecision}
        reason={policyReason}
        loading={policyLoading}
        error={policyError}
        onCompanyChange={setSelectedCompany}
        onTitleChange={setPolicyTitle}
        onKeywordsChange={setPolicyKeywords}
        onDecisionChange={setPolicyDecision}
        onReasonChange={setPolicyReason}
        onCreate={createPolicy}
        onDelete={deletePolicy}
      />
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
