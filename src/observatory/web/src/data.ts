// Adapté de pithos/harness/dashboard/web/src/data.ts : polling annulable, sans requêtes concurrentes.
import { useEffect, useState } from "react";

export type Window = { total: number; above: number; below: number };
export type Mission = { mission_id: string; n_events: number; last_ts?: string; anomalies: string[] };
export type Freshness = { refreshed_at?: string; watch_error?: string; missions?: number };
export type Gate = {
  path: string; role: string; role_provenance: string;
  metadata: { check: string; execution?: string; diagnostic?: string; counterexample?: string; duration: number; source_sha256?: string };
};
export type Call = {
  ts: string; outcome: string; prompt_tokens: number | null; completion_tokens: number | null;
  prompt_estimate: number | null; context_window: number | null; context_provenance: string;
  margin_tokens: number | null; occupancy: number | null; pressure: string; truncated: boolean;
  elapsed_seconds?: number | null;
};
export type Detail = Mission & {
  freshness: Freshness;
  trial: {
    result: { mode?: string; status?: string; cause?: string; elapsed_seconds?: number; restored?: boolean;
      before_sha256?: string; after_sha256?: string; components?: Record<string, string>;
      error?: string; detail?: string; usable?: boolean; capability?: { detail?: string } } | null;
    reason: string | null; receipt_count: number; gates: Gate[]; reports: unknown[]; anomalies: string[];
  };
  context: { calls: Call[]; summary: { calls: number; truncated: number; reported_tokens?: number; outcomes?: Record<string, number> } };
  artifacts: Record<string, { exists: boolean; size: number | null }>;
};
export type Node = { node_id: string; parent_id: string | null; depth: number; label: string; target: string;
  status: string; own_ms: number | null; subtree_ms: number | null; anomalies: string[] };
export type Event = { ts: string; type: string; payload: Record<string, unknown> };

export function useResource<T>(path: string, revision: number, interval = 10_000) {
  const [result, setResult] = useState<{ path: string; data?: T; error?: string }>({ path });
  useEffect(() => {
    const controller = new AbortController();
    let timer: number;
    const refresh = async () => {
      try {
        const response = await fetch(`/api${path}`, {
          signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15_000)]),
        });
        if (!response.ok) throw new Error(`Lecture impossible (HTTP ${response.status}).`);
        const data = await response.json() as T;
        if (!controller.signal.aborted) setResult({ path, data });
      } catch (reason) {
        if (controller.signal.aborted) return;
        const error = reason instanceof Error ? reason.message : String(reason);
        setResult((current) => ({ path, data: current.path === path ? current.data : undefined, error }));
      } finally {
        if (!controller.signal.aborted && interval > 0) timer = window.setTimeout(() => void refresh(), interval);
      }
    };
    void refresh();
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [path, revision, interval]);

  return result.path === path ? result : { path };
}

export function number(value: number | null | undefined) {
  return value == null ? "—" : value.toLocaleString("fr-FR");
}
export function date(value: string | undefined) {
  if (!value) return "—";
  const timestamp = new Date(value);
  return Number.isNaN(timestamp.getTime()) ? value : timestamp.toLocaleString("fr-FR");
}
export function mode(value: string | undefined) {
  return ({ trial: "Essai réel", selftest: "Selftest · doubles", probe: "Probe de capacité" })[value ?? ""] ?? "Mode inconnu";
}
