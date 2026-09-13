// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { App, Artifact, TrialDetail } from "./App";
import { useResource } from "./data";

let container: HTMLDivElement;
let root: Root;
beforeEach(() => {
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  vi.useFakeTimers();
  container = document.createElement("div");
  document.body.append(container);
  root = createRoot(container);
});
afterEach(async () => {
  await act(async () => root.unmount());
  container.remove();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});
function Probe({ path }: { path: string }) {
  const resource = useResource<{ status: string }>(path, 0);
  return <div>{resource.data?.status ?? "loading"}{resource.error}</div>;
}
const omission = { total: 1, above: 0, below: 0 };
function detail(id = "trial-one") {
  return {
    mission_id: id, anomalies: [], artifacts: {}, n_events: 2,
    trial: {
      result: { mode: "trial", status: "blocked", restored: true }, reason: "tautology",
      receipt_count: 0, gates: [], reports: [], anomalies: [],
    },
    context: { calls: [], summary: { calls: 2, truncated: 0 } },
  };
}
test("refreshes after ten seconds without overlapping requests", async () => {
  const fetcher = vi.fn().mockResolvedValue(Response.json({ status: "running" }));
  vi.stubGlobal("fetch", fetcher);
  await act(async () => root.render(<Probe path="/one" />));
  fetcher.mockResolvedValue(Response.json({ status: "blocked" }));
  await act(async () => vi.advanceTimersByTimeAsync(10_000));
  expect(container.textContent).toBe("blocked");
  expect(fetcher).toHaveBeenCalledTimes(2);
});
test("late response cannot replace another selected run", async () => {
  let resolve!: (value: Response) => void;
  const previous = new Promise<Response>((done) => { resolve = done; });
  const fetcher = vi.fn().mockReturnValueOnce(previous).mockResolvedValueOnce(Response.json({ status: "new" }));
  vi.stubGlobal("fetch", fetcher);
  await act(async () => root.render(<Probe path="/old" />));
  await act(async () => root.render(<Probe path="/new" />));
  await act(async () => resolve(Response.json({ status: "old" })));
  expect(container.textContent).toBe("new");
  expect(fetcher.mock.calls[0][1].signal.aborted).toBe(true);
});
test("failed navigation never relabels the previous page", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(Response.json({ status: "previous" }))
    .mockResolvedValueOnce(new Response(null, { status: 503 })));
  await act(async () => root.render(<Probe path="/1" />));
  await act(async () => root.render(<Probe path="/2" />));
  expect(container.textContent).not.toContain("previous");
  expect(container.textContent).toContain("HTTP 503");
});
test("readiness remains visible when metrics fail without inventing zeros", async () => {
  vi.stubGlobal("fetch", vi.fn(async (path: string) => {
    if (path === "/api/ready") return Response.json({ ready: true, freshness: {} });
    if (path === "/api/stats/attempts") return new Response(null, { status: 503 });
    return Response.json({ missions: [], window: { total: 0, above: 0, below: 0 } });
  }));
  await act(async () => root.render(<App />));
  expect(container.querySelector('[role="status"]')?.textContent).toContain("Lecture disponible");
  expect(container.querySelector(".metric")?.textContent).toBe("—");
  expect(container.querySelector('[role="alert"]')?.textContent).toContain("HTTP 503");
});
test("artifact pages use line offsets and reset when the artifact changes", async () => {
  const fetcher = vi.fn(async (path: string) => Response.json({
    path: "candidate.py", text: path.includes("offset=200") ? "second" : "first",
    window: path.includes("offset=200") ? { total: 201, above: 200, below: 0 } : { total: 201, above: 0, below: 1 },
  }));
  vi.stubGlobal("fetch", fetcher);
  await act(async () => root.render(<Artifact mission="one" path="invariant-a/candidate.py" revision={0} />));
  await act(async () => container.querySelector<HTMLButtonElement>('[aria-label="Page suivante"]')?.click());
  expect(container.querySelector("pre")?.textContent).toBe("second");
  await act(async () => root.render(<Artifact mission="one" path="tree.json" revision={0} />));
  expect(fetcher).toHaveBeenLastCalledWith("/api/missions/one/artifact?path=tree.json&limit=200&offset=0", expect.anything());
});
test("catalogue pagination selects the new run and disables the final page", async () => {
  vi.stubGlobal("fetch", vi.fn(async (path: string) => {
    if (path.startsWith("/api/missions?")) {
      const last = path.includes("offset=20");
      return Response.json({ missions: [{ mission_id: last ? "last-run" : "first-run", n_events: 2 }],
        window: { total: 21, above: last ? 20 : 0, below: last ? 0 : 20 } });
    }
    if (path.includes("/tree?")) return Response.json({ nodes: [], anomalies: [], window: omission });
    if (path.endsWith("/ready")) return Response.json({ ready: true, freshness: {} });
    if (path.endsWith("/attempts")) return Response.json({ by_mode: {} });
    return Response.json(detail(path.split("/").at(-1)));
  }));
  await act(async () => root.render(<App />));
  const next = container.querySelector<HTMLButtonElement>('.run-panel [aria-label="Page suivante"]');
  await act(async () => next?.click());
  expect(container.querySelector(".detail-title")?.textContent).toBe("last-run");
  expect(next?.disabled).toBe(true);
});
test("rejected gate evidence stays visible and payload markup is escaped", async () => {
  const body = detail();
  const gate = { path: "invariant-a", role: "variant", role_provenance: "unassigned",
    metadata: { check: "passed", diagnostic: '<script>alert("x")</script>', duration: 0.2 } };
  vi.stubGlobal("fetch", vi.fn(async (path: string) => {
    if (path.includes("/tree?")) return Response.json({ nodes: [], anomalies: [], window: omission });
    return Response.json({ ...body, trial: { ...body.trial, gates: [gate] } });
  }));
  await act(async () => root.render(<TrialDetail mission="trial-one" revision={0} />));
  expect(container.textContent).toContain("tautology");
  expect(container.textContent).toContain("Rollback confirmé");
  expect(container.textContent).toContain("Aucun reçu durable");
  expect(container.textContent).toContain('<script>alert("x")</script>');
  expect(container.querySelector("script")).toBeNull();
});

test("context exposes asserted capacity and missing measurements alongside tool counts", async () => {
  const body = detail();
  vi.stubGlobal("fetch", vi.fn(async (path: string) => {
    if (path.includes("/tree?")) return Response.json({ nodes: [], anomalies: [], window: omission });
    if (path.includes("/stats/tools")) return Response.json({ tools: [{ operation: "splice", calls: 1, bytes: 32 }], splice_inflation: { ratio: null } });
    if (path.includes("/stats/daily")) return Response.json({ days: [] });
    if (path.includes("/indicators")) return Response.json({ version: "v2" });
    return Response.json({ ...body, context: { ...body.context, calls: [{
      ts: "2026-09-13T07:00:00Z", outcome: "completed", context_window: 16384,
      context_provenance: "asserted", prompt_tokens: null, occupancy: null, pressure: "unknown",
    }] } });
  }));
  await act(async () => root.render(<TrialDetail mission="trial-one" revision={0} />));
  const tab = [...container.querySelectorAll<HTMLButtonElement>("nav button")].find((button) => button.textContent === "Contexte & mesures");
  await act(async () => tab?.click());
  expect(container.textContent).toContain("asserted");
  expect(container.textContent).toContain("unknown");
  expect(container.textContent).toContain("32 octets");
  expect(container.querySelector("progress")).toBeNull();
});
