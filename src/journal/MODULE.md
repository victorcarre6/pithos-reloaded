# `journal` — la durabilité

> **Lis [`AGENTS.md`](../../AGENTS.md) avant de commencer.** Ce fichier est ton contrat complet : tu ne
> devrais pas avoir besoin d'ouvrir `docs/`. Ton point d'entrée exact est la rubrique « Prochaine action » de
> [`STATE.md`](STATE.md), à côté de ce fichier.
>
> **Tu ne commites, ne pousses et ne merges jamais.** Tes commits se *proposent* dans [`git.md`](git.md),
> avec les `ga`/`gcmsg` exacts — voir [`AGENTS.md`](../../AGENTS.md) § 7.

**Cible** : ~150 L au socle · ~400 L à terme · ratchet **shrink-only**
**Dépend de** : `kernel` (pour `Event`).
**Niveau de dépendance** : 1 — tous les modules de niveau ≥ 2 écrivent par lui.
**Stack** : **stdlib pur** — `os`, `json`, `fcntl`, `hashlib`, `base64`, `pathlib`.

> **Zéro dépendance externe. C'est le seul module du projet dans ce cas, et c'est une propriété à
> préserver.** Si tu te trouves à vouloir installer quelque chose ici, la conception est en cause.

## 1. Autorité

`journal` possède **le format** des traces durables — donc les deux sens, écriture et lecture.
`observatory` lit **par lui** plutôt que de reparser le JSONL de son côté : **un format, un parseur.**

Ce module est né le 06:09 en sortant de `kernel`, où il portait ~55 reprises — rotation, quarantaine,
séquence dense, validation incrémentale — soit plus que la cible de `kernel` tout entier. Ce n'était pas du
vocabulaire mais un moteur de stockage durable.

## 2. Interface publique

```python
def emit(event: Event) -> bool:
    "Écrit la ligne JSONL complète puis sa projection d'une ligne dans live.log."

def update_json_locked(path: Path, fn: Callable[[dict], dict]) -> None:
    "Read-modify-write sous un seul verrou tenu, relecture du disque DANS le verrou."

def read(path: Path) -> Iterator[Event]: ...
def tail(path: Path, n: int) -> tuple[list[Event], bool]: ...   # (lignes, un_préfixe_a_été_omis)
def next_event_id(path: Path) -> int: ...                       # reprise après redémarrage
def torn_tail(path: Path) -> TornTail | None: ...               # détecte, NE RÉPARE PAS
def redact(value: Any) -> tuple[Any, list[str]]: ...            # (valeur_rédigée, chemins_rédigés)
```

## 3. Interdits

- **N'importe rien au-dessus de `kernel`.** Aucun module de niveau ≥ 2.
- **Ne répare jamais un journal tronqué.** Le fragment est **diagnostiqué**, et la reprise ouvre un
  **nouveau segment lié**. Ne tronque pas, ne réécris pas, ne supprime pas — contrainte dure n°6.
- **Pas de `logging`.** Le contrat est la durabilité append-only ; les handlers de `logging` ajoutent une
  sémantique de buffering à combattre.
- **N'installe aucune dépendance.**

## 4. Les deux règles qui décident de tout ici

**Une écriture, deux sorties.** `emit(event)` écrit la ligne JSONL complète **puis** sa projection d'une
ligne dans `live.log`. Un seul chemin d'écriture, donc **impossible qu'un événement soit dans l'un et pas
dans l'autre** ; et `live.log` est explicitement dérivable, donc jetable et reconstructible. La décision 29
s'applique : la projection déclare qu'elle omet le payload.

**Toute écriture est encapsulée et ne lève jamais.** C'est la règle absolue de Villani, retenue sans
exception. Ce qui garde la décision 13 n'est pas une exception à l'écriture mais **l'absence du reçu
constatée après coup** :

```text
écrire        →  n'échoue jamais
compter vert  →  exige le reçu effectivement écrit   (c'est verifier qui le constate)
```

Un reçu non écrit retire l'attestation, et le nœud passe `blocked` avec la cause `receipt_not_written`. Une
mission survit à un disque plein **sans en sortir un seul faux vert**.

## 5. Contenu

| Fichier | Contenu | ~L socle |
|---|---|---:|
| `write.py` | `emit`, append + `fsync`, verrou global, temp+rename, `update_json_locked` | 70 |
| `read.py` | itération, `tail`, `next_event_id`, détection de queue déchirée | 55 |
| `redact.py` | une fonction, une liste de motifs nommée | 25 |

**Le verrou est global et unique**, ~15 L, plutôt qu'un verrou sidecar par fichier nommé par SHA-256
(~40 L). Cohérent avec « une mission à la fois, sous `RunLock` ». Le coût est nommé : il sérialise des
écritures qui n'entrent jamais en conflit.

⚠️ **Un verrou d'écrivain ne protège pas le lecteur** !
→ `observatory` n'en prend aucun. Ce qui protège d'une ligne déchirée reste **une seule syscall `write()` par
ligne** plus **un lecteur qui tolère une queue déchirée**. Les deux exigences sont indépendantes ; le verrou
n'en dispense pas.

**Format** : un champ `v` par ligne — une ligne de code, toute migration future possible — plus une
**signature de génération de fichier** (hash de la première ligne + taille) pour que lecteur et écrivain
sachent qu'ils parlent du même fichier.

**Reporté jusqu'à ce qu'un volume le justifie** : rotation avec lecteurs conscients de l'archive,
quarantaine base64, séquence dense à machine à états, `LedgerResumeState`, rétention de blobs.

## 6. Critères de socle que ce module rend verts

- **Aucune ligne JSONL n'est jamais réécrite ni supprimée**, y compris une fin de fichier tronquée : le
  fragment est diagnostiqué et la reprise ouvre un nouveau segment lié (décision 10 amendée).
- **L'espace disque est vérifié avant écriture** d'un snapshot, d'une trace ou d'un artefact —
  l'insuffisance est un `blocked` mécanique avec cause, jamais une exception d'écriture. *(Le prédicat
  d'espace vient de `lifecycle` ; `journal` l'appelle.)*
- Contribue à : *aucun succès sans preuve d'effet*, en garantissant qu'une écriture de preuve réussie est
  durable.

## 7. Le double

`tests/doubles/journal.py` — un journal **en mémoire** qui accumule les événements dans une liste et expose
la même interface. Deux comportements que le double doit savoir simuler, parce que tout le reste du projet
en dépend :

1. **`emit` qui rend `False`** (disque plein) sans lever — pour que `verifier` puisse être testé sur le
   chemin `receipt_not_written`.
2. **Une queue déchirée** — pour que `observatory` puisse être testé sur un lecteur tolérant.

## 8. Fini quand

- [ ] `emit` écrit la ligne JSONL **et** la ligne `live.log`, ou aucune des deux — test par injection de
      panne entre les deux.
- [ ] `emit` **ne lève jamais**, quelle que soit la panne : disque plein, permission, chemin absent. Il rend
      `False`.
- [ ] Une ligne est écrite en **une seule syscall `write()`** — vérifié, pas supposé.
- [ ] Un `SIGKILL` entre création du temporaire et `rename` laisse le fichier d'origine **intact** — test
      par injection de crash déterministe.
- [ ] Une queue déchirée est **détectée et jamais réparée** ; la reprise ouvre un segment lié, et le
      fragment reste lisible.
- [ ] `next_event_id` reprend correctement après redémarrage, sur un fichier de 10 000 lignes.
- [ ] `tail` rend `(lignes, un_préfixe_a_été_omis)` — le booléen est vrai dès qu'une ligne a été omise.
- [ ] `redact` rend la valeur rédigée **et la liste des chemins rédigés**, sur une structure imbriquée.
- [ ] `update_json_locked` relit le disque **dans** le verrou — test par écriture concurrente.
- [ ] Aucune dépendance externe dans `pyproject.toml` pour ce module.

## 9. Pièges connus

- **Les offsets sont des offsets d'octets sur buffers bruts.** Les indices de chaîne divergent dès le
  premier caractère UTF-8 multi-octets.
- **Framing sur LF uniquement**, et décodage UTF-8 incrémental.
- **La vérification de taille et l'allocation doivent voir le même fd**, sinon une croissance concurrente
  contourne la borne.
- **La réparation d'une queue n'a jamais lieu à la lecture** — *« a viewer may replay a live writer's log »*.
  Chez nous elle n'a lieu nulle part.
- **Publier sur disque avant de modifier la projection mémoire**, jamais l'inverse.
- **Le `SecretRedactingLogFilter` d'Ouroboros est écarté** : la décision 10 exclut `logging`, il n'y a rien
  à filtrer.

---

## Sources — reprises retenues

**34 lignes.** Chaque pointeur se lit dans `resources/`. Le détail complet et le contexte de chaque partie sont dans [`resources/IMPORT_REPORT.md`](../../resources/IMPORT_REPORT.md).
**Lis la source avant de porter.** Une reprise collée sans être relue est un défaut.

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| A4.1 | `runtime_events.py:28-34` | `RuntimeEvent` porte un flag **`durable`** : un événement de statut éphémère ne pollue pas la preuve. | **Copier** |
| A4.1 | `runtime_events.py:8-25` | `RuntimeEventChannel` / `RuntimeEventType` — deux enums fermées : le canal (qui écoute) et le type (quoi). | **Copier** |
| A4.1 | `runtime_events.py:37-127` | `from_runner_event` — table de correspondance unique entre événements bruts et typés, avec repli explicite. | **Inspirer** |
| A4.1 | `event_recorder.py:20-33` | Une ligne JSONL = `ts` + `type` + `phase` + `durable` + `summary` + **payload brut complet**. Le résumé est à côté du brut, jamais à sa place. | **Copier** |
| A4.1 | `trace_summary.py:16-51` | `EventLogger._discover_next_event_id` — les identifiants reprennent après redémarrage en relisant le fichier. | **Copier** |
| A4.1 | `trace_summary.py:104-133` | `normalize_token_usage` — les compteurs peuvent rester `None`. | **Copier** |


#### C — Kilo Code · `resources/kilocode-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| C3.1 | `opencode/src/util/filesystem.ts:84-113` | Écriture atomique par temporaire + `rename`, nom temporaire portant **pid + timestamp + suffixe aléatoire** ; `ENOENT` ⇒ `mkdir -p` puis retente. Sérialisation de `tree.json` et `registry.json`. | **Traduire** |
| C3.1 | `opencode/src/bus/index.ts:41-56` | Le commentaire **est** la notion : `subscribe` acquiert l'abonnement **au `yield*`, pas à la première lecture**, la forme paresseuse perdant les publications intermédiaires. Tests « RACE » dédiés. Piège d'un bus + tail de dashboard. | **Traduire** |
| C3.1 | `opencode/src/bus/index.ts:75-89` | Le finaliseur **publie `InstanceDisposed` avant d'éteindre le PubSub**. Un flux se termine toujours par un événement terminal, jamais par du silence. | **Traduire** |
| C3.1 | `opencode/src/storage/storage.ts:53-64` | Stockage minimal `read`/`write`/`update(key, fn)`/`list(prefix)`/`remove`, clé = `string[]` → chemin. **Une clé hiérarchique est un chemin ; le magasin est un arbre de JSON.** | **Traduire** |
| C3.1 | `opencode/src/storage/storage.ts:67-73` | `missing(err)` — normalise « fichier absent » à travers `ENOENT` **et** l'erreur typée. Deux formes d'absence, un seul prédicat. | **Traduire** |


#### D — Ouroboros · `resources/ouroboros-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| D3.1 | `our/utils.py:232-274` | `_atomic_overwrite` — sibling `.{nom}.tmp.<pid>.<tid>.<uuid>` puis `os.replace`. Un SIGKILL entre création et rename laisse le fichier **existant intact**, jamais tronqué. Bits de permission préservés. | **Copier** |
| D3.1 | `our/utils.py:212-230` | `replace_atomic` — retry borné sur `PermissionError` **seulement**. POSIX reste un syscall unique, sans sleep. | **Copier** |
| D3.1 | `our/utils.py:276-338` | `write_bytes_atomic` / `write_text_atomic` / `atomic_write_json`, `fsync` **optionnel et explicite**. Un `os.write` partiel est détecté, pas ignoré. | **Copier** |
| D3.1 | `our/utils.py:340-380` | `sweep_stale_temp_files` — les temporaires orphelins d'un kill dur sont récupérés par balayage d'âge. Sans lui, un crash par mission laisse un fichier mort par écriture. | **Copier** |
| D3.1 | `our/utils.py:395-455` | `update_json_locked` — read-modify-write **sous un seul verrou tenu**, relecture du disque **dans** le verrou. `TimeoutError` sur échec : *« proceeding unlocked would silently reintroduce the race »*. | **Copier** |
| D3.1 | `our/utils.py:463-612` | `append_jsonl` renvoie **`bool`**, jamais un succès simulé. `require_lock=True` pour les flux d'autorité : ceux-là ne se rabattent **pas** sur un append non verrouillé. | **Copier** |
| D3.1 | `our/utils.py:457-461` | `jsonl_append_lock_path` — verrou sidecar nommé par le SHA-256 du chemin résolu, partagé entre writers et rotation. | **Copier** |
| D3.1 | `our/utils.py:151-169` | `jsonl_generation_signature` — identité d'une **génération** de fichier (hash de la première ligne + taille), pour que writer et reader détectent une rotation à l'identique. | **Copier** |
| D3.1 | `our/utils.py:1381-1410` | Deux primitives de bornage aux contrats **distincts** : aperçu avec **plancher anti-gaspillage** (une coupe qui économise moins que son propre marqueur est refusée) vs preuve durable. | **Copier** |
| D3.1 | `our/usage_ledger.py:228-302` | `_validate_records` — **séquence dense** (`seq` strictement incrémental, un trou est une corruption) plus une **machine à états par entité** validée au replay. | **Copier** |
| D3.1 | `our/usage_ledger.py:41-48` | Deux exceptions typées : fail-closed vs histoire structurellement invalide. **Un registre corrompu ne se lit pas « comme vide ».** | **Copier** |
| D3.1 | `our/observability.py:48-192` | Reconnaissance de clé secrète par **quatre couches** : noms exacts, suffixes (`_API_KEY`, `_TOKEN`), suffixes composés, marqueurs de segment, plus motifs de valeur et de paramètre d'URL. | **Copier** |
| D3.1 | `our/observability.py:1083-1087` | `redact_projection` — **une** fonction traversant n'importe quelle structure, renvoyant la valeur rédigée **et la liste des rédactions effectuées**. | **Copier** |
| D3.1 | `our/observability.py:33-34,238-257` | Modes privés POSIX explicites (`0o600`/`0o700`) avec prédicat de support. La trace forensique n'est pas lisible par les autres utilisateurs. | **Copier** |
| D3.1 | `our/observability.py:1378-1450` | La rétention des blobs est une **fonction nommée**, pas un `find -delete` dans un cron. | **Copier** |
| D3.1 | `our/_outcome_receipts.py:462-530` | `disclosed_list_projection` — borner une **liste** obéit à la même règle que borner une chaîne : le slice porte le **compte omis** et un **hash durable de l'ensemble complet**. | **Copier** |


#### E — Prime Agent · `resources/prime-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| E3.1 | `ca/core/event-log.ts:15-29` | **`EventLog` — substrat JSONL append-only crash-safe.** Le commentaire de tête est le contrat entier : append en une seule écriture `O_APPEND`, `fsync` à la demande. | **Adapter** |
| E3.1 | `ca/core/event-log.ts:143-183` | `repairTailSync` — la réparation n'a lieu **qu'à l'append, jamais à la lecture** (*« a viewer may replay a live writer's log »*). Notre règle est encore plus stricte : nouveau segment lié, jamais de troncature. | **Inspirer** |
| E3.1 | `ca/core/event-log.ts:158-175` | Tous les offsets sont des **offsets d'octets sur buffers bruts** — les indices de chaîne divergent dès le premier caractère UTF-8 multi-octets. | **Adapter** |
| E3.1 | `ca/core/event-log.ts:39-52` | La vérification de taille et l'allocation voient **le même fd** : une croissance concurrente ne peut pas contourner la borne. `maxBytes`/`maxRecords` échouent en fermé. | **Adapter** |
| E3.1 | `ca/core/semantic-edges.ts:6-28,82-95` | Journal d'événements bruts **plus un pli pur** qui en dérive les arêtes de causalité. Les événements sont écrits **avant les effets qu'ils décrivent** ; une arête n'est matérialisée que quand sa cible finit. | **Inspirer** |
| E3.1 | `ca/core/semantic-edges.ts:426-470` | `deriveSemanticEdges` — pli pur, avec `pending` rendu quand une requête échoue. Un échec ne perd pas la causalité, il la reporte. | **Inspirer** |
| E3.1 | `ca/core/semantic-edges.ts:118-149` | `hashTurnBody` — *« la réutilisation d'`Idempotency-Key` n'est sûre que pour un retry octet-identique »*. Notre politique d'idempotence Telegram et Git en dépend. | **Traduire** |


---

## Sources — reprises écartées ou reportées

**5 lignes. N'implémente aucune de ces lignes.** Le pointeur reste pour qu'un retournement de décision retrouve la source. Si tu penses qu'une raison est fausse, **écris-le dans `STATE.md`, n'implémente pas.**

#### C — Kilo Code · `resources/kilocode-main/`

| § | Source | Notion | Statut |
|---|---|---|---|
| C3.1 | `opencode/src/storage/storage.ts:81` | `MIGRATIONS` — tableau ordonné avec compteur entier persisté. Nécessaire à `journals/` et au format de `registry.json`. | **Écarté** |


#### D — Ouroboros · `resources/ouroboros-main/`

| § | Source | Notion | Statut |
|---|---|---|---|
| D3.1 | `sup/state.py:918-1000` | Rotation JSONL avec lecteurs conscients de l'archive. Notre `live.log` en aura besoin dès la dixième mission. | **Reporté** |
| D3.1 | `our/usage_ledger.py:200-226` | `_quarantine_tail` — la queue déchirée est encodée en base64 dans un `*.quarantine.jsonl`. **On reprend la quarantaine, pas la troncature** — voir conflit n°8. | **Reporté** |
| D3.1 | `our/usage_ledger.py:355-477` | `LedgerResumeState` — validation **incrémentale** : un lecteur ayant déjà validé un préfixe passe la prochaine `seq` attendue, au lieu de tout relire. | **Reporté** |
| D3.1 | `our/observability.py:1452-1470` | `SecretRedactingLogFilter` — un filtre `logging` qui rédige, pour que le chemin *non* instrumenté ne fuite pas non plus. | **Écarté** |

