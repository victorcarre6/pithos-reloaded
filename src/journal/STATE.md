# STATE — `journal`

**Statut** : en cours — socle livré et vert, deux items de `AGENTS.md` § 11 hors périmètre
**Mise à jour** : 06:09
**Lignes** : 313 / ~150 L socle · ~400 L cible — écart justifié plus bas

## Prochaine action

Faire trancher les deux blocages de périmètre ci-dessous (emplacement du test de conformité et du
test de graphe d'imports). Aucun code n'est en attente : le socle est complet et vert. Si le module
doit s'élargir vers sa cible de ~400 L, l'item suivant est la **rotation avec lecteurs conscients de
l'archive** (`sup/state.py:918-1000`, verdict **Reporté**) — n'y toucher que quand le volume la
justifie, pas avant.

## Avancement

Liste « Fini quand » de `MODULE.md`, cochée :

- [x] `emit` écrit la ligne JSONL **et** la ligne `live.log`, ou aucune des deux — injection de
      panne entre les deux. *Voir le blocage n°1 : la fenêtre couverte est celle d'avant la première
      écriture, la seule compatible avec la contrainte dure n°6.*
- [x] `emit` **ne lève jamais** : disque plein, permission refusée, projection inouvrable, verrou
      inouvrable. Il rend `False`. (4 tests)
- [x] Une ligne est écrite en **une seule syscall `write()`** — compté sur `os.write`, pas supposé.
- [x] Un `SIGKILL` entre création du temporaire et `rename` laisse l'original **intact** — vrai
      `SIGKILL` dans un sous-processus, `returncode == -9` observé.
- [x] Une queue déchirée est détectée et **jamais réparée** ; la reprise ouvre `events.1.jsonl` dont
      le premier événement porte le lien, et le fragment reste lisible à l'octet près.
- [x] `next_event_id` reprend après redémarrage sur un fichier de **10 000 lignes**.
- [x] `tail` rend `(lignes, un_préfixe_a_été_omis)`, y compris `n = 0`.
- [x] `redact` rend la valeur rédigée **et** les chemins rédigés sur une structure imbriquée.
- [x] `update_json_locked` relit le disque **dans** le verrou — prouvé par écriture concurrente.
- [x] Aucune dépendance externe : test AST sur le code du module, **mutation-checké** (il rougit
      quand on ajoute `import pydantic`).

## Journal

### 06:09 — `redact`, la seule fonction de rédaction

Portée de `our/observability.py:1083-1087` avec les quatre couches de reconnaissance de clé réduites
à deux listes de motifs nommées (`SECRET_NAMES`, `SECRET_SUFFIXES`), comme le prescrit `MODULE.md`
§ 5. Le piège de la source est conservé et testé : `monkey`, `keynote` et `hockey` **ne sont pas**
des secrets, alors qu'un suffixe `key` naïf les capturerait. Un sous-arbre `credentials` est
remplacé en entier et n'est jamais traversé — on ne consigne pas les chemins de ce qu'on cache.
**39 lignes, 6 tests. Niveau de preuve : 4 — la fonction est pure, le test métier passe.**

### 06:09 — `read`, un format et un parseur

Framing sur LF uniquement, offsets en octets sur buffers bruts (`ca/core/event-log.ts:158-175`).
`_lines` écarte structurellement le fragment final : un journal déchiré se lit sans exception et
sans réparation. Une ligne **intérieure** illisible lève au contraire — `our/usage_ledger.py:41-48`,
« un registre corrompu ne se lit pas comme vide ».
`next_event_id` reprend à 1 comme sa source (`trace_summary.py:16-51`).
**Mesuré** : 10 000 lignes relues en reprise, ~0,05 s. **66 lignes, 12 tests. Niveau : 4.**

### 06:09 — `write`, et le seul ordre qui rende « les deux ou aucune » vrai

`emit` sérialise les deux lignes **et ouvre les deux descripteurs avant la première écriture**. Une
projection indisponible fait donc rendre `False` sans qu'aucun fichier ne soit créé — c'est la seule
atomicité atteignable sans réécrire le JSONL, ce que la contrainte dure n°6 interdit. La projection
est ouverte **avant** la preuve, pour qu'un échec d'ouverture ne laisse même pas un `events.jsonl`
vide.

**Deux défauts trouvés en relecture, avant de déclarer quoi que ce soit** :

1. Un échec d'écriture de `live.log` **après** une preuve déjà `fsync`ée retirait l'attestation *et*
   ne consommait pas l'identifiant — le `emit` suivant aurait réutilisé le même `event_id` et cassé
   la densité de la séquence. Corrigé : la valeur de retour et l'incrément ne dépendent que de la
   ligne JSONL. Test de non-régression ajouté.
2. `_acquire` ouvrait son fichier de verrou hors du bloc protégé : un répertoire de verrou absent
   faisait **lever** `emit`. Corrigé dans `_acquire`, qui rend `None` plutôt que de lever, donc la
   propriété « ne lève jamais » est structurelle et non plus dépendante de l'ordre des appels.

Une écriture partielle n'est jamais un succès (`_write_once` compare le compte rendu à la taille) et
n'est jamais projetée : `live.log` ne peut pas annoncer un événement dont la preuve est déchirée.
**172 lignes, 18 tests. Niveau : 4, sauf le `SIGKILL` — niveau 3, effet réel constaté sur disque.**

### 06:09 — Interface, double et frontière

`Journal` est un `Protocol` `runtime_checkable` à membres **statiques** : le journal est un module,
pas un objet à instancier. Le double et l'implémentation sont vérifiés sur le protocole **et** sur
l'égalité des signatures publiques — un `isinstance` seul ne compare que des noms.

Le test de frontière lit l'**AST** du code du module (tests exclus) et vérifie deux choses : aucun
import interne autre que `kernel`, et aucun import hors `sys.stdlib_module_names`. **Il a été
mutation-checké** : `import engine` et `import pydantic` le font rougir chacun avec le bon message.
C'est ce qui rend la propriété « zéro dépendance externe » mécanique et non déclarative.
**Niveau : 5 pour la conformité du double ; 4 pour la frontière.**

### 06:09 — Ce qui n'a pas été prouvé

- **Aucun test contre le double de `kernel`** : `tests/doubles/kernel.py` n'existait pas pendant
  cette session. Mes tests construisent un `Event` réel depuis `kernel.contracts`. Pour un contrat
  de données pur et figé (`frozen`, `extra="forbid"`) c'est une preuve *plus forte* qu'un double,
  mais c'est un **écart au protocole d'isolation** d'`AGENTS.md` § 6, et il doit être relu quand le
  double atterrira.
- **Niveau 6 non atteint, et non revendiqué.** Aucune mission réelle, aucun Ollama, aucun
  `~/logs/pithos2/` : la durabilité est prouvée sur `tmp_path`, pas sur le volume de production.
- **La syscall unique est comptée dans le processus**, par interception de `os.write` — pas observée
  par `dtruss`. C'est le chemin de notre code qui est prouvé, pas la garantie du noyau.

### 06:09 — Le double de `kernel` atterrit, l'écart d'isolation est levé

`tests/doubles/kernel.py` est apparu pendant la session. Les fixtures passent de la construction
directe d'un `Event` à `double("kernel").event(...)`, comme l'exige `AGENTS.md` § 6. Le chargement
se fait par chemin — `tests/` n'est pas un paquet importable et `pythonpath` ne porte que `src` —
et le chargeur est mutualisé en fixture, désormais partagé par les tests d'écriture et d'interface.
**L'écart consigné dans l'entrée précédente est donc levé : niveau de preuve 5, validé sur double.**
Aucun changement de code du module ; 40 tests toujours verts.

### 06:09 — Scénario de bout en bout, hors harnais de test

Trois événements écrits, un fragment de 47 octets ajouté à la main pour simuler une mission tuée en
pleine écriture, puis une session suivante liée sur le même journal. **Observé sur disque** :
`events.jsonl` reste identique à l'octet près et sa queue déchirée reste détectable ; `events.1.jsonl`
s'ouvre avec le lien (`segment_from`, offset 420, 47 octets, signature de génération) ; les
identifiants restent **denses à travers la frontière de segment** (#1-#3, puis #4 lien et #5) ; et
`live.log` reste **un seul flux continu**, lisible en `tail -F` par-dessus les deux segments, chaque
ligne déclarant le payload qu'elle omet.
**Niveau de preuve : 3 — effet réel constaté sur fichiers.** Pas 6 : ni mission réelle, ni
`~/logs/pithos2/`, ni Ollama.

## Blocages

| Quoi | Pourquoi | Ce qui débloquerait | Résolu le |
|---|---|---|---|
| 1. « Les deux ou aucune » n'est pas littéralement atteignable | Une fois la ligne JSONL `fsync`ée, la retirer serait une réécriture du journal — **contrainte dure n°6**. `MODULE.md` § 8 item 1 et la contrainte se contredisent sur la fenêtre d'après-écriture. Signalé et non tranché en silence, comme l'impose `AGENTS.md` § 2. | Confirmer que l'item vise la fenêtre **avant** la première écriture. L'invariant réellement tenu, et testé, est : `live.log` ne contient jamais un événement absent du JSONL. | — |
| 2. Le test de conformité double ↔ implémentation vit dans mon périmètre | `AGENTS.md` § 11 le veut dans `tests/contracts/`, § 6 m'interdit d'y écrire. Il est donc dans `src/journal/test_interface.py`. | Autoriser `tests/contracts/test_journal_double.py`, ou entériner l'emplacement actuel. Le fichier est déplaçable tel quel. | — |
| 3. Le test de graphe d'imports vit dans mon périmètre | Même conflit § 11 / § 6 pour `tests/boundaries/`. Ma version ne couvre que `journal` ; les **trois règles** structurantes restent à écrire par qui possède ce répertoire. | Un agent mandaté sur `tests/boundaries/`, ou l'autorisation d'y écrire la règle qui me concerne. | — |
| 4. Écart de lignes : 313 pour ~150 L de socle | L'estimation de `MODULE.md` couvrait `write`+`read`+`redact` (70+55+25) et ne budgétait ni `__init__.py` (36 L de `Protocol`, exigé par `ARCHITECTURE.md`), ni `bind`, ni la reprise par **segment lié** (~46 L), tous deux exigés par « Fini quand ». Le module reste **sous la cible de ~400 L**. | Rien à débloquer : le ratchet est désormais **shrink-only à partir de 313**. Aucune ligne n'est spéculative ; toute réduction devra retirer du comportement testé. | — |

## Décisions locales

**`bind(events_path, live_path)` s'ajoute à l'interface de `MODULE.md`.** `emit(event) -> bool` ne
porte aucun chemin et `Event` ne porte aucun identifiant de mission : une liaison explicite est le
minimum qui rende la signature spécifiée implémentable. Elle prend les deux chemins plutôt qu'une
racine, pour que **la politique de disposition de `~/logs/pithos2/` reste hors de `journal`** — elle
appartient à `lifecycle`. Le verrou global est un sibling de `live.log` (`.journal.lock`), seul
fichier global de la disposition.

**Le journal possède l'enveloppe de ligne, pas seulement l'événement.** `event_id` est ajouté par
`emit` et retiré par `read` avant `model_validate` — obligatoire, `Event` étant `extra="forbid"`.
C'est ce qui permet à `next_event_id` d'exister sans champ correspondant dans `kernel`.

**`emit` ne lève jamais ; `update_json_locked` lève.** Les deux contrats diffèrent parce que le
premier a un canal pour signaler l'échec (son `bool`) et le second n'en a pas. Le `TimeoutError` de
`our/utils.py:395-455` est conservé avec sa raison : continuer sans verrou réintroduirait
silencieusement la perte de mise à jour que la fonction supprime.

**La rédaction porte sur les noms de champ, pas sur les valeurs.** Les motifs de *valeur*
(`_TOKEN_PATTERNS`) sont volontairement absents : ils imposeraient `re`, hors de la stack déclarée,
et les credentials Git et Telegram appartiennent à `broker`, qui ne les fait jamais transiter par
ici. À revoir si un payload se met à porter un secret en clair.

**Stack stdlib réellement utilisée**, au-delà de la ligne du `MODULE.md` (`os`, `json`, `fcntl`,
`hashlib`, `pathlib`) : `dataclasses`, `datetime`, `threading`, `time`, `typing`, `uuid`. Aucune
n'est externe ; `base64` n'est pas utilisé, la quarantaine restant reportée.

**Le double ré-exporte le vrai `redact`.** C'est une fonction pure : un double divergerait sans rien
prouver de plus. Les deux pannes que le double sait simuler sont celles que `MODULE.md` § 7 exige —
`disk_full = True` et `torn = TornTail(...)`.

## Reprises traitées

| Source | Verdict | Fait ? | Note |
|---|---|---|---|
| `villani/runtime_events.py:28-34` — flag `durable` | Copier | oui | Porté par `Event.durable` (kernel) ; `live.log` projette `[durable]` / `[ephemeral]`. |
| `villani/runtime_events.py:8-25` — deux enums fermées | Copier | non | Appartient à `kernel` (`EventType`). `journal` ne redéfinit aucune enum. |
| `villani/runtime_events.py:37-127` — `from_runner_event` | Inspirer | non | Pas de source d'événements bruts au socle. |
| `villani/event_recorder.py:20-33` — ligne = brut + résumé | Copier | adapté | Ligne = champs de l'`Event` + `event_id` ; le résumé vit dans `live.log`, **à côté** du brut, jamais à sa place. |
| `villani/trace_summary.py:16-51` — `_discover_next_event_id` | Copier | oui | `next_event_id`, 1-based comme la source, testé sur 10 000 lignes. |
| `villani/trace_summary.py:104-133` — `normalize_token_usage` | Copier | non | Les compteurs de tokens appartiennent à `bridge`. |
| `kilo/util/filesystem.ts:84-113` — temp + `rename` | Traduire | oui | `_write_json_atomic` ; nom de temporaire pris à Ouroboros (`pid.tid.uuid`), plus précis que la source. |
| `kilo/bus/index.ts:41-56` — abonnement au `yield*` | Traduire | non | Pas de bus au socle ; revient avec `observatory`. |
| `kilo/bus/index.ts:75-89` — événement terminal explicite | Traduire | non | Idem : pas de flux au socle. |
| `kilo/storage/storage.ts:53-64` — magasin minimal | Traduire | non | Le magasin appartient à `campaign` (ROADMAP P0). |
| `kilo/storage/storage.ts:67-73` — `missing(err)` | Traduire | adapté | `FileNotFoundError` est le prédicat d'absence unique de `_read_json`, `_lines` et `torn_tail`. |
| `our/utils.py:232-274` — `_atomic_overwrite` | Copier | oui | Sibling `.{nom}.tmp.<pid>.<tid>.<uuid8>`, bits de permission préservés, prouvé par `SIGKILL` réel. |
| `our/utils.py:212-230` — `replace_atomic` | Copier | non | Le retry ne vise que les violations de partage Windows ; sur POSIX `os.replace` est un syscall unique. Cible macOS. |
| `our/utils.py:276-338` — écritures atomiques, `fsync` explicite | Copier | oui | `fsync` explicite ; l'écriture partielle est **détectée**, pas ignorée. |
| `our/utils.py:340-380` — `sweep_stale_temp_files` | Copier | reporté | Balayage d'âge = custody disque : appartient à `lifecycle`. `journal` ne supprime rien (contrainte n°6). Un temporaire orphelin ne peut venir que d'un kill dur, le chemin d'erreur nettoyant le sien. |
| `our/utils.py:395-455` — `update_json_locked` | Copier | oui | Relecture dans le verrou, `TimeoutError` conservé avec sa raison. |
| `our/utils.py:463-612` — `append_jsonl -> bool` | Copier | oui | `emit -> bool`, jamais un succès simulé. Flux d'autorité : **aucun repli non verrouillé**. |
| `our/utils.py:457-461` — verrou sidecar SHA-256 | Copier | écarté | `MODULE.md` § 5 tranche pour un **verrou global unique**. Coût nommé : il sérialise des écritures qui n'entrent jamais en conflit. |
| `our/utils.py:151-169` — `jsonl_generation_signature` | Copier | oui | `generation_signature` ; portée dans le lien de segment. |
| `our/utils.py:1381-1410` — bornage aperçu vs preuve | Copier | non | Pas d'aperçu borné au socle ; `tail` rend le drapeau d'omission. |
| `our/usage_ledger.py:228-302` — séquence dense, machine à états | Copier | reporté | `MODULE.md` § 5. `event_id` est dense et repris, sans le validateur de replay. |
| `our/usage_ledger.py:41-48` — deux exceptions typées | Copier | adapté | `read` échoue **fermé** sur une ligne intérieure illisible ; la queue déchirée reste tolérée. |
| `our/observability.py:48-192` — 4 couches de clés | Copier | réduit | Réduit à deux listes nommées, comme prescrit. Le piège `monkey`/`keynote` est testé. |
| `our/observability.py:1083-1087` — `redact_projection` | Copier | oui | `redact` rend la valeur **et** les chemins. |
| `our/observability.py:33-34,238-257` — modes privés POSIX | Copier | oui | `0o600` sur toute création ; bits existants préservés au `replace`. |
| `our/observability.py:1378-1450` — rétention de blobs | Copier | reporté | `MODULE.md` § 5 ; pas de blob au socle. |
| `our/_outcome_receipts.py:462-530` — bornage de liste | Copier | non | `tail` rend le drapeau d'omission, pas encore le compte omis ni le hash de l'ensemble. À reprendre si `observatory` en a besoin. |
| `prime/ca/core/event-log.ts:15-29` — substrat JSONL | Adapter | oui | `O_APPEND`, une écriture par ligne, `fsync` explicite. |
| `prime/ca/core/event-log.ts:143-183` — `repairTailSync` | Inspirer | oui | Repris **en plus strict** : jamais de troncature, ni à l'append ni à la lecture. Segment lié à la place. |
| `prime/ca/core/event-log.ts:158-175` — offsets d'octets | Adapter | oui | `TornTail.offset` et `n_bytes` sont des octets ; aucun index de chaîne. |
| `prime/ca/core/event-log.ts:39-52` — même fd pour taille et allocation | Adapter | non | Pas de borne `maxBytes` au socle ; à reprendre avec la rotation. |
| `prime/ca/core/semantic-edges.ts` (3 lignes) | Inspirer | non | Le pli de causalité appartient à `observatory` / `engine`. |
| `prime/ca/core/semantic-edges.ts:118-149` — `hashTurnBody` | Traduire | non | L'idempotence Telegram et Git appartient à `broker`. |
