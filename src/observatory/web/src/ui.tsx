import type { ReactNode } from "react";
import { number, type Window } from "./data";

export function ErrorNotice({ children }: { children?: string }) {
  return children ? <p className="error-notice" role="alert">{children}</p> : null;
}
export function Status({ value }: { value?: string | null }) {
  const labels: Record<string, string> = { running: "En cours", pending: "En attente", blocked: "Bloqué",
    passed: "Passé", failed: "Échoué", completed: "Terminé", rejected: "Refusé",
    admission_refused: "Admission refusée", probe_passed: "Sonde conforme", probe_failed: "Sonde refusée" };
  return <span className={`pill ${value ?? "unknown"}`}>{labels[value ?? ""] ?? value ?? "Inconnu"}</span>;
}
export function Metric({ label, value, hint }: { label: string; value?: number | null; hint: string }) {
  return <div className="card metric-card"><span className="label">{label}</span>
    <div className="metric">{number(value)}</div><p className="muted">{hint}</p></div>;
}
export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>;
}
export function Pager({ window: span, offset, size, onChange }: {
  window?: Window; offset: number; size: number; onChange: (offset: number) => void;
}) {
  return <div className="pager">
    <button aria-label="Page précédente" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - size))}>←</button>
    <span className="muted">{span ? `${span.total} au total · ${span.above} avant · ${span.below} après` : "Page en attente"}</span>
    <button aria-label="Page suivante" disabled={!span?.below} onClick={() => onChange(offset + size)}>→</button>
  </div>;
}
