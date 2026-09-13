// Structure et navigation adaptées du dashboard Pithos v1 ; contrats propres aux nano-étapes.
import { useEffect, useState } from "react";
import { date, mode, number, useResource, type Detail, type Event, type Freshness, type Mission, type Node, type Window } from "./data";
import { Empty, ErrorNotice, Metric, Pager, Status } from "./ui";

const PAGE = 20;
type Group = { runs: number; with_state: number; admission_errors: number; with_receipt: number; restored: number; unchanged: number; by_cause: Record<string, number> };

export function App() {
  const [revision, setRevision] = useState(0);
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const ready = useResource<{ ready: boolean; logs_root: string; freshness: Freshness }>("/ready", revision);
  const list = useResource<{ missions: Mission[]; window: Window }>(`/missions?limit=${PAGE}&offset=${offset}`, revision);
  const stats = useResource<{ by_mode: Record<string, Group> }>("/stats/attempts", revision);
  const real = stats.data?.by_mode.trial;
  const realCount = stats.data ? real?.with_state ?? 0 : undefined;
  const selectedId = selected ?? list.data?.missions[0]?.mission_id;

  return <>
    <header><div className="header-inner"><div className="brand"><span className="logo">π</span>
      <div><h1>Pithos <span className="muted">Reloaded</span></h1><p className="subtitle">Observatoire local</p></div></div>
      <span role="status" className={`pill ${ready.data?.ready && !ready.error ? "passed" : "unknown"}`}>
        {ready.error ? "API indisponible" : ready.data?.ready ? "Lecture disponible" : "Connexion / suivi indisponible"}</span></div></header>
    <main className="shell">
      <div className="page-heading"><div><p className="eyebrow">Expériences d’autonomie</p><h2>La trajectoire, preuves à l’appui.</h2>
        <p className="muted">État publié, vérifications et traces brutes · lecture seule · actualisation 10 s</p></div>
        <button onClick={() => setRevision((value) => value + 1)}>↻ Actualiser</button></div>
      <ErrorNotice>{ready.error ?? ready.data?.freshness?.watch_error}</ErrorNotice>
      <ErrorNotice>{stats.error}</ErrorNotice>
      <section className="metrics" aria-label="Bilan des essais réels">
        <Metric label="Nano-étapes réelles" value={realCount} hint="Probes et erreurs d’admission exclues" />
        <Metric label="Avec reçu" value={stats.data ? real?.with_receipt ?? 0 : undefined} hint="Validation durable observée" />
        <Metric label="Rollbacks" value={stats.data ? real?.restored ?? 0 : undefined} hint="Restauration rapportée par l’essai" />
        <Metric label="Sans changement final" value={stats.data ? real?.unchanged ?? 0 : undefined} hint="Empreintes avant et après identiques" />
      </section>
      <div className="section-meta"><span>{ready.data?.logs_root}</span><span>Dernière lecture : {date(ready.data?.freshness?.refreshed_at)}</span></div>
      <section className="layout" aria-label="Explorateur d’essais">
        <aside className="card run-panel"><div className="panel-heading"><h3>Essais & probes</h3><span className="muted">Plus récents d’abord</span></div>
          <ErrorNotice>{list.error}</ErrorNotice>
          {!list.data && !list.error && <Empty>Chargement des essais…</Empty>}
          {list.data?.missions.length === 0 && <Empty>Aucun essai dans cette collection.</Empty>}
          <div className="run-list">{list.data?.missions.map((run) => <button key={run.mission_id}
            className={`run ${selectedId === run.mission_id ? "active" : ""}`} aria-pressed={selectedId === run.mission_id}
            onClick={() => setSelected(run.mission_id)}>
            <strong>{run.mission_id}</strong><span className="muted">{date(run.last_ts)}</span>
            <span>{number(run.n_events)} événements {run.anomalies?.length ? "· anomalies" : ""}</span>
          </button>)}</div>
          <Pager window={list.data?.window} offset={offset} size={PAGE} onChange={(value) => { setOffset(value); setSelected(null); }} />
          <div className="mode-counts">{Object.entries(stats.data?.by_mode ?? {}).map(([name, group]) =>
            <p key={name}><span>{mode(name)}{group.admission_errors ? ` · ${group.admission_errors} refus avant exécution` : ""}</span><strong>{group.runs}</strong></p>)}</div>
        </aside>
        {selectedId ? <TrialDetail key={selectedId} mission={selectedId} revision={revision} /> : <Empty>Sélectionner un essai pour examiner ses preuves.</Empty>}
      </section>
    </main>
  </>;
}

export function TrialDetail({ mission, revision }: { mission: string; revision: number }) {
  const [tab, setTab] = useState("proof");
  const [artifact, setArtifact] = useState("result.json");
  const prefix = `/missions/${encodeURIComponent(mission)}`;
  const resource = useResource<Detail>(prefix, revision);
  const data = resource.data;
  const result = data?.trial.result;
  let status = result?.status;
  if (!status && result?.error) status = "admission_refused";
  if (!status && result?.usable === true) status = "probe_passed";
  if (!status && result?.usable === false) status = "probe_failed";
  const open = (path: string) => { setArtifact(path); setTab("artifacts"); };

  return <div className="detail-stack">
    <section className="card detail-card"><div className="row"><span className="eyebrow">{mode(result?.mode)}</span><Status value={status} /></div>
      <h3 className="detail-title">{mission}</h3>
      <ErrorNotice>{resource.error}</ErrorNotice>
      {!data && !resource.error && <Empty>Lecture des preuves…</Empty>}
      {data && <>
        <div className="detail-metrics"><div><span className="label">Durée de l’essai</span><strong>{number(result?.elapsed_seconds)} s</strong></div>
          <div><span className="label">Appels modèle</span><strong>{number(data.context.summary.calls)}</strong></div>
          <div><span className="label">Troncatures</span><strong>{number(data.context.summary.truncated)}</strong></div>
          <div><span className="label">Tokens rapportés</span><strong>{number(data.context.summary.reported_tokens)}</strong></div></div>
        <div className="outcome"><strong>{data.trial.reason ?? result?.cause ?? result?.detail ?? result?.capability?.detail ?? "Aucune cause terminale rapportée"}</strong>
          <p>{result?.restored === true ? "Rollback confirmé" : result?.restored === false ? "Fichier non restauré" : "Restauration non documentée"}
            {" · "}{data.trial.receipt_count ? `${data.trial.receipt_count} reçu(s) durable(s)` : "Aucun reçu durable"}</p>
          {data.trial.reason === "tautology" && <p className="muted">Le candidat passe son invariant, mais aucun mutant exécuté ne l’a fait échouer. La tentative reste refusée.</p>}</div>
        <div className="muted components">{Object.entries(result?.components ?? {}).map(([name, value]) => `${name}: ${value}`).join(" · ")}</div>
        {[...data.anomalies, ...data.trial.anomalies].map((text, index) => <ErrorNotice key={index}>{text}</ErrorNotice>)}
      </>}
    </section>
    <nav aria-label="Vues de l’essai" className="panel-navigation">{[
      ["proof", "Arbre & preuves"], ["context", "Contexte & mesures"], ["events", "Chronologie"], ["artifacts", "Artefacts"],
    ].map(([name, label]) => <button key={name} className={tab === name ? "active" : ""} aria-pressed={tab === name} onClick={() => setTab(name)}>{label}</button>)}</nav>
    {data && tab === "proof" && <>
      <Tree mission={mission} revision={revision} />
      <section className="card detail-card"><div className="panel-heading"><h3>Exécutions de vérification</h3><span className="muted">{data.trial.gates.length} artefacts</span></div>
        <p className="muted">Rôles avant/après rapprochés par empreinte. Les autres variantes restent sans opérateur attribué dans les anciennes traces.</p>
        {data.trial.gates.length === 0 && <Empty>Aucune exécution de gate enregistrée.</Empty>}
        {data.trial.gates.map((gate) => <article className="gate" key={gate.path}>
          <div className="row"><h4>{({ before: "Avant modification", after: "Candidat proposé", variant: "Variante" })[gate.role] ?? gate.role}</h4><Status value={gate.metadata.check} /></div>
          <p className="muted">{gate.path} · {number(gate.metadata.duration)} s · {gate.role_provenance}</p>
          {gate.metadata.diagnostic && <pre>{gate.metadata.diagnostic}</pre>}
          <div className="artifact-links"><button onClick={() => open(`${gate.path}/candidate.py`)}>Voir la source</button>
            <button onClick={() => open(`${gate.path}/invariant.py`)}>Invariant</button><button onClick={() => open(`${gate.path}/meta.json`)}>Métadonnées</button></div>
        </article>)}
        {data.trial.reports.length > 0 && <details><summary>Historique des rapports de vérification ({data.trial.reports.length})</summary><pre>{JSON.stringify(data.trial.reports, null, 2)}</pre></details>}
      </section>
    </>}
    {data && tab === "context" && <section className="card detail-card"><h3>Appels et occupation du contexte</h3>
      <p className="muted">Tokens rapportés par le runtime ; estimation du prompt séparée. Capacité « asserted » déclarée au lancement.</p>
      {data.context.calls.length === 0 && <Empty>Aucun appel modèle documenté.</Empty>}
      {data.context.calls.map((call, index) => <article className="gate" key={index}>
        <div className="row"><strong>{call.outcome === "budget_refused" ? "Préflight refusé" : `Appel ${index + 1}`} · {date(call.ts)}</strong><Status value={call.outcome} /></div>
        <dl><div><dt>Prompt mesuré / estimé</dt><dd>{number(call.prompt_tokens)} / {number(call.prompt_estimate)}</dd></div>
          <div><dt>Tokens de sortie</dt><dd>{number(call.completion_tokens)}</dd></div>
          <div><dt>Durée mesurée de l’appel</dt><dd>{number(call.elapsed_seconds)} s</dd></div>
          <div><dt>Fenêtre de contexte</dt><dd>{number(call.context_window)} · {call.context_provenance}</dd></div>
          <div><dt>Marge après réserve de sortie</dt><dd>{number(call.margin_tokens)} tokens</dd></div>
          <div><dt>Occupation / pression</dt><dd>{call.occupancy == null ? "—" : `${(call.occupancy * 100).toFixed(1)} %`} · {call.pressure}</dd></div></dl>
        {call.occupancy != null && <progress aria-label={`Occupation appel ${index + 1}`} max={1} value={call.occupancy} />}
      </article>)}
      <Indicators mission={mission} revision={revision} />
      <ActivityStats mission={mission} revision={revision} />
    </section>}
    {tab === "events" && <Timeline mission={mission} revision={revision} />}
    {data && tab === "artifacts" && <section className="card detail-card"><h3>Artefacts de l’essai</h3>
      <label className="artifact-heading">Fichier <select value={artifact} onChange={(event) => setArtifact(event.target.value)}>
        {Object.entries(data.artifacts).filter(([name, entry]) => entry.exists && !name.endsWith(".jsonl")).map(([name]) => <option key={name}>{name}</option>)}
      </select></label><Artifact mission={mission} path={artifact} revision={revision} /></section>}
  </div>;
}

function Tree({ mission, revision }: { mission: string; revision: number }) {
  const [offset, setOffset] = useState(0);
  const tree = useResource<{ nodes: Node[]; anomalies: string[]; window: Window }>(`/missions/${encodeURIComponent(mission)}/tree?limit=200&offset=${offset}`, revision);
  return <section className="card detail-card"><h3>Arbre publié</h3><p className="muted">Les intentions du journal ne remplacent pas l’état publié. Durées inconnues : —.</p>
    <ErrorNotice>{tree.error}</ErrorNotice>
    {tree.data?.nodes.length === 0 && <Empty>Aucun nœud publié pour cet essai.</Empty>}
    {tree.data?.nodes.map((node) => <div key={node.node_id} className="tree-node" style={{ marginLeft: Math.min(node.depth, 10) * 14 }}>
      <div className="row"><strong>{node.node_id}</strong><Status value={node.status} /></div><p>{node.label}</p><p className="muted">{node.target}</p>
      <p className="muted">Parent : {node.parent_id ?? "racine"} · propre {number(node.own_ms)} ms · sous-arbre {number(node.subtree_ms)} ms</p>
      {node.depth > 10 && <p className="muted">Profondeur {node.depth} · indentation plafonnée à 10</p>}
      {node.anomalies.map((text) => <ErrorNotice key={text}>{text}</ErrorNotice>)}
    </div>)}
    {tree.data?.anomalies.map((text, index) => <ErrorNotice key={index}>{text}</ErrorNotice>)}
    <Pager window={tree.data?.window} offset={offset} size={200} onChange={setOffset} />
  </section>;
}

function Indicators({ mission, revision }: { mission: string; revision: number }) {
  const resource = useResource<Record<string, { question: string; value: number | null }>>(`/indicators?mission=${encodeURIComponent(mission)}`, revision);
  const rows = Object.entries(resource.data ?? {}).filter(([, value]) => typeof value === "object");
  return <><h3>Questions expérimentales</h3><ErrorNotice>{resource.error}</ErrorNotice><dl>{rows.map(([key, row]) =>
    <div key={key}><dt>{row.question}</dt><dd>{number(row.value)}</dd></div>)}</dl></>;
}

function ActivityStats({ mission, revision }: { mission: string; revision: number }) {
  const scope = `?mission=${encodeURIComponent(mission)}`;
  const tools = useResource<{ tools: { operation: string; calls: number; bytes: number }[];
    splice_inflation: { ratio: number | null } }>(`/stats/tools${scope}`, revision);
  const daily = useResource<{ days: { day: string; verified: number; rejected: number; model_calls: number }[] }>(`/stats/daily${scope}`, revision);
  return <>
    <h3>Activité des outils</h3><ErrorNotice>{tools.error}</ErrorNotice>
    {tools.data?.tools.length === 0 && <Empty>Aucune opération d’outil enregistrée.</Empty>}
    <dl>{tools.data?.tools.map((row) => <div key={row.operation}><dt>{row.operation}</dt><dd>{row.calls} appel(s) · {number(row.bytes)} octets</dd></div>)}</dl>
    <p className="muted">Inflation de splice (source émise / changement utile) : {number(tools.data?.splice_inflation.ratio)}</p>
    <h3>Bilan par jour UTC</h3><ErrorNotice>{daily.error}</ErrorNotice>
    <dl>{daily.data?.days.map((day) => <div key={day.day}><dt>{day.day}</dt>
      <dd>{day.model_calls} appel(s) modèle · {day.verified} validation(s) · {day.rejected} refus</dd></div>)}</dl>
  </>;
}

function Timeline({ mission, revision }: { mission: string; revision: number }) {
  const [offset, setOffset] = useState(0);
  const resource = useResource<{ events: Event[]; window: Window; anomalies: string[] }>(`/missions/${encodeURIComponent(mission)}/events?limit=100&offset=${offset}`, revision);
  return <section className="card detail-card"><h3>Chronologie brute</h3><p className="muted">events.jsonl · intentions, appels et preuves dans l’ordre du journal.</p>
    <ErrorNotice>{resource.error}</ErrorNotice>
    {resource.data?.anomalies.map((text, index) => <ErrorNotice key={index}>{text}</ErrorNotice>)}
    {resource.data?.events.map((event, index) => <details className="event" key={index}>
      <summary><strong>{String(event.payload.operation ?? event.type)}</strong>{event.payload.phase === "intent" ? " · intention" : ""}<time>{date(event.ts)}</time></summary>
      <pre>{JSON.stringify(event.payload, null, 2)}</pre></details>)}
    <Pager window={resource.data?.window} offset={offset} size={100} onChange={setOffset} />
  </section>;
}

export function Artifact({ mission, path, revision }: { mission: string; path: string; revision: number }) {
  const [page, setPage] = useState({ path, offset: 0 });
  const offset = page.path === path ? page.offset : 0;
  useEffect(() => setPage({ path, offset: 0 }), [path]);
  const resource = useResource<{ text: string; window: Window }>(`/missions/${encodeURIComponent(mission)}/artifact?path=${encodeURIComponent(path)}&limit=200&offset=${offset}`, revision);
  return <><p className="muted artifact-path">{path} · aperçu limité à 2 Mo</p><ErrorNotice>{resource.error}</ErrorNotice>
    {resource.data && <pre className="artifact">{resource.data.text}</pre>}
    <Pager window={resource.data?.window} offset={offset} size={200} onChange={(value) => setPage({ path, offset: value })} /></>;
}
