"use client";

import { useState } from "react";
import { brief } from "@/lib/api";
import type { ResearchResult } from "@/lib/types";

export default function Home() {
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ResearchResult | null>(null);

  async function onBrief() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      setResult(await brief(company, role));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const canSubmit = company.trim().length > 1 && !loading;

  return (
    <div className="container">
      <header>
        <h1>research-agent</h1>
        <p>
          Give it a company. It plans, searches the web, reads pages, and returns a
          grounded interview briefing — every fact tied to a source it actually
          visited. You can watch every tool call it made.
        </p>
      </header>

      <label htmlFor="company">Company</label>
      <input
        id="company"
        type="text"
        value={company}
        onChange={(e) => setCompany(e.target.value)}
        placeholder="Anthropic"
      />
      <label htmlFor="role">Role (optional)</label>
      <input
        id="role"
        type="text"
        value={role}
        onChange={(e) => setRole(e.target.value)}
        placeholder="AI Engineer"
      />

      <div className="actions">
        <button onClick={onBrief} disabled={!canSubmit}>
          {loading ? "Researching… (~30–60s)" : "Research"}
        </button>
        <button
          className="ghost"
          onClick={() => {
            setCompany("Anthropic");
            setRole("AI Engineer");
          }}
          disabled={loading}
        >
          Load example
        </button>
      </div>

      {error && <p className="error">⚠ {error}</p>}
      {result && <Result result={result} />}
    </div>
  );
}

function Result({ result }: { result: ResearchResult }) {
  const b = result.briefing;
  return (
    <>
      <section className="panel">
        <h2>{b.company}</h2>
        <p>{b.summary}</p>
        {b.what_they_do.length > 0 && (
          <>
            <h3>What they do</h3>
            <ul>{b.what_they_do.map((x, i) => <li key={i}>{x}</li>)}</ul>
          </>
        )}
        {b.recent_developments.length > 0 && (
          <>
            <h3>Recent developments</h3>
            {b.recent_developments.map((d, i) => (
              <div className="cite" key={i}>
                <div>{d.fact}</div>
                <a className="id" href={d.source_url} target="_blank" rel="noreferrer">
                  {d.source_url}
                </a>
              </div>
            ))}
          </>
        )}
      </section>

      {(b.likely_interview_questions.length > 0 || b.talking_points.length > 0) && (
        <section className="panel">
          {b.likely_interview_questions.length > 0 && (
            <>
              <h3>Likely interview questions</h3>
              <ul>{b.likely_interview_questions.map((q, i) => <li key={i}>{q}</li>)}</ul>
            </>
          )}
          {b.talking_points.length > 0 && (
            <>
              <h3>Talking points</h3>
              <ul>{b.talking_points.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </>
          )}
        </section>
      )}

      {b.notes && (
        <section className="panel" style={{ borderColor: "#4a3f26", background: "#1c1810" }}>
          <h3>Notes / caveats</h3>
          {b.notes}
        </section>
      )}

      <section className="panel">
        <h2>Agent trace — {result.steps_used} tool calls</h2>
        {result.trace.map((s) => (
          <div className="chunk" key={s.n}>
            <div className="meta">
              #{s.n} · {s.tool} · {s.input}
            </div>
            {s.output.slice(0, 200)}
            {s.output.length > 200 ? "…" : ""}
          </div>
        ))}
      </section>
    </>
  );
}
