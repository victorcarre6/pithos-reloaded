# STATE — `bridge`

**Statut** : en cours — socle livré et vert, un item de `AGENTS.md` § 11 hors périmètre
**Mise à jour** : 06:09
**Lignes** : 345 / ~250 L — écart justifié plus bas

## Prochaine action

Faire trancher le blocage n°1 (emplacement du test de graphe d'imports). Aucun code n'est en
attente : le socle est complet et vert sur route locale scriptée. Le chemin critique suivant est
le **spike n°2 reformulé** — brancher `probe()` puis `call()` sur l'Ollama réel et **mesurer le taux
de rejet de la revalidation locale par code d'erreur**. Tout est en place pour le faire : lancer
`probe()` avec `PITHOS_OLLAMA_URL` sur la route réelle et lire les événements `_record` du journal.
**Prérequis côté `engine`** : consigner le verdict de `revalidate`, que `bridge` ne peut pas émettre
sans rendre une fonction pure impure — voir la dernière entrée du journal.

## Avancement

Liste « Fini quand » de `MODULE.md`, cochée :

- [x] `normalize_schema` résout `$defs`/`$ref` et borne les integers sur un `Criterion` réel ; le
      schéma résultant est validé avant envoi (référence non résolue et objet sans propriétés
      refusés). 9 tests.
- [x] Une réponse acceptée par le transport mais non conforme au schéma exact envoyé est rejetée
      localement, avec le bon code fermé.
- [x] `NaN` et `Infinity` sont refusés par `parse_constant` — et portent leur **propre** code fermé,
      `constant_refused`, au lieu de se confondre avec `invalid_json`.
- [x] `finish_reason=length` est distingué de `stop` : `content` est **vide** sur toute issue autre
      que `completed`, donc rien d'exploitable n'en sort même quand le corps parse.
- [x] Le thinking est séparé du contenu, dans les deux formes rencontrées : champ
      `reasoning_content` et bloc `<think>` en tête de contenu.
- [x] Les retries implicites sont désactivés — une 503 produit **exactement une** requête, comptée
      sur une vraie route locale. *Portée exacte au § Journal.*
- [x] Le budget réserve la sortie : un contrat qui ne rentre pas dans la fenêtre ne produit
      **aucune** requête (`route.requests == []`).
- [x] `probe()` refuse de démarrer si `n_ctx_train` est illisible — `unprobeable` est fail-closed et
      n'émet aucun appel.
- [x] Annuler l'attente ne tue pas l'opération : le serveur achève son effet après l'abandon du
      client, et c'est observé. *Moitié non prouvée au § Journal.*
- [~] `tests/boundaries/` — le test existe et rougit sur `import engine`, mais vit dans mon
      périmètre faute d'accès au répertoire. Voir blocage n°1.

## Journal

### 06:09 — `schema`, l'outillage que le spike n°2 attendait

Pydantic v2 émet un `$ref` **par enum** : le schéma réel de `Criterion` porte deux `$defs`
(`Relation`, `Domain`) et trois propriétés dont deux ne sont que des références. Sans inlining, une
grammaire de décodage contraint n'a rien à appliquer. Porté de `kilo/opencode/src/tool/json-schema.ts`
avec trois corrections propres à Pydantic :

- **`properties` ne se filtre pas.** Ses clés sont des noms de champ, pas des mots-clés de schéma.
  Un filtrage naïf par `SUPPORTED_KEYWORDS` supprimerait les propriétés du modèle. Trouvé en écrivant
  le test de sous-ensemble, pas en relecture.
- **Un `$ref` non résolu lève**, il n'est pas retiré. Comme `$ref` n'est pas dans le sous-ensemble
  supporté, le filtrage l'aurait silencieusement transformé en schéma vide — c'est-à-dire en
  **contrainte absente**, le pire résultat possible pour ce module. Un modèle récursif est donc
  refusé avant envoi, et c'est testé.
- **Les bornes déclarées ne sont jamais écrasées** : `setdefault`, pas d'affectation.

`title` disparaît au passage — autant de contexte non consommé à chaque appel sur une fenêtre de 16k.
**58 lignes, 9 tests. Niveau de preuve : 4.**

### 06:09 — `revalidate`, et le fait que `jsonschema` n'est pas déclaré

La source d'Ouroboros valide avec `jsonschema`. **`jsonschema` est installé dans le venv mais absent
de `requirements.txt`** — l'utiliser rendrait le module irreproductible et tombe sous le critère de
rejet d'`AGENTS.md` § 6. Le contrat l'avait déjà anticipé : nos cinq codes remplacent les deux codes
`jsonschema` de la source (`invalid_schema`, `schema_validation_failed`) par `schema_violation`
(Pydantic) et `constant_refused`. La revalidation est donc **pydantique**, dans la stack déclarée.

Reste la question que la source pose et que Pydantic seul ne ferme pas : *valide-t-on bien contre le
schéma exactement envoyé ?* Réponse retenue, sans dépendance : `revalidate` **compare le schéma reçu
à `normalize_schema(model)`** et rend `unknown_tool` s'ils diffèrent. Le schéma envoyé et le modèle
validé sont alors prouvés être le même artefact, et la validation Pydantic vaut validation contre le
schéma envoyé. Chaque verdict porte en plus le `schema_sha256` qui le lie à ce schéma exact.
**62 lignes, 11 tests. Niveau : 4.**

### 06:09 — `client`, sur une vraie route locale

Testé contre un **vrai serveur HTTP stdlib** sur port éphémère, pas un transport simulé : les
requêtes réellement reçues sont inspectées, et le corps effectivement envoyé est vérifié
(`response_format.strict`, schéma exact, `temperature 0.3 / top_p 0.95 / top_k 20`, `stream: false`).

**Décisions de fermeture prises ici** : `content` n'est renseigné que sur `completed`. Une
génération tronquée dont le JSON parse quand même ne peut donc pas être revalidée par un appelant
distrait — l'invariant est porté par la donnée, pas par la discipline de l'appelant. Un
`finish_reason` inconnu (`content_filter`, par exemple) est `unknown_stop`, jamais rabattu sur
`stop` comme le fait la source de Villani.

`normalize_base_url` **refuse toute route hors loopback** (`unsloth/_inference.py:634`), ce qui rend
la contrainte dure n°5 mécanique sur ce chemin : la variable d'environnement qui déplace la route
pour un banc ne peut pas la faire sortir de la machine.

**Portée exacte de « pas de retry implicite »** : le test prouve qu'une 503 produit une seule
requête. `HTTPTransport(retries=0)` désactive en plus les retries de *connexion*, mais **ce
réglage-là n'est pas observé séparément** — httpx ne rejoue de toute façon jamais une réponse HTTP.
**138 lignes, 13 tests. Niveau : 3 — effet réel constaté sur socket.**

### 06:09 — `probe`, fail-closed, et la sonde qui refuse de deviner

Trois contrôles dans l'ordre où ils peuvent échouer. La source d'Ouroboros donne le bon
`health_check` (`n_ctx` lu sur `/v1/models`) **et, deux fonctions plus bas, l'anti-exemple exact** :
`get_context_length` retombe sur `4096` en cas d'exception. C'est précisément ce que
`capability_evidence` corrige et ce que notre contrat interdit — une panne de route ne se lit jamais
comme une valeur par défaut. `unprobeable` n'émet donc **aucun appel** et rend `usable = False`.

Les trois provenances sont implémentées, `asserted` compris : sans `n_ctx_train` lisible, un aveu
explicite d'opérateur (`PITHOS_CONTEXT_WINDOW`) est accepté **et nommé comme tel**, jamais présenté
comme confirmé. Sans lecture ni aveu, la campagne ne démarre pas.
**70 lignes, 8 tests. Niveau : 4 sur route scriptée ; niveau 6 non atteint — aucun Ollama réel.**

### 06:09 — Ce qui n'a pas été prouvé

- **Aucun appel réel à Ollama.** Tout est vert contre une route locale scriptée qui *imite* le
  dialecte OpenAI. **Que la route Ollama applique réellement `response_format` reste la question
  ouverte du spike n°2**, et c'est exactement pourquoi la revalidation locale est obligatoire.
- **« La fermeture du client attend la fin réelle de l'effet » n'est prouvée qu'à moitié.** Ce qui
  est observé : le client abandonne sur sa borne, et le serveur **achève son effet** malgré tout —
  donc une borne murale atteinte ne prouve pas l'arrêt du travail distant. Ce qui n'est pas
  implémenté : une *vérification de fin* côté client, qu'un `/v1/chat/completions` sans identifiant
  de requête ne permet pas d'offrir.
- **L'estimation de tokens est `chars/4`**, fragile pour l'Unicode et le code. Elle est nommée
  `prompt_estimate` et tenue **séparée** de `usage` mesuré, exactement pour ne pas être confondue
  avec lui. Le spike n°4 doit mesurer le ratio réel.
- **Le prompt système n'a été éprouvé contre aucun mode d'échec réel de Ling.** Il est court par
  décision, pas par mesure.

### 06:09 — Bout en bout, et le maillon qui manque au spike n°2

Scénario complet hors harnais de test, journal réellement lié : `probe()` rend
`confirmed / 16384 / usable`, un appel conforme revalide `Ok`, et **un appel que la route accepte
avec `finish_reason: stop` mais dont le contenu viole le schéma est rejeté localement en
`schema_violation`** — la propriété pour laquelle ce module existe, observée de bout en bout. La
trace porte issue, raison terminale, estimation, usage mesuré et empreinte de schéma.
**Niveau de preuve : 3 — effet réel constaté sur socket et sur fichiers.**

**Gap trouvé là, et pas avant** : la trace enregistre l'issue du *transport*, jamais le verdict de
la revalidation. Le spike n°2 demande « le taux de rejet de la revalidation locale, **par code
d'erreur** » : il n'est donc **pas encore calculable depuis le journal seul**. Faire émettre
`revalidate` le rendrait impur et lui donnerait une dépendance d'I/O qu'il n'a pas — c'est
`engine`, qui compose `call` puis `revalidate`, qui doit consigner le verdict. La clé de jointure
existe déjà : `Ok`/`Err` et l'événement de `_record` portent le **même `schema_sha256`**.

## Blocages

| Quoi | Pourquoi | Ce qui débloquerait | Résolu le |
|---|---|---|---|
| 1. Le test de graphe d'imports vit dans mon périmètre | `AGENTS.md` § 11 le veut dans `tests/boundaries/`, § 6 m'interdit d'y écrire. Il est donc dans `src/bridge/test_interface.py` — même conflit que pour `journal`. | Autoriser `tests/boundaries/`, ou entériner l'emplacement. Mon test couvre la **deuxième règle** (`bridge` sans `engine`) et rougit bien quand on la viole. | — |
| 2. Écart de lignes : 345 pour ~250 L | L'estimation du `MODULE.md` couvre les quatre fichiers (40+70+60+40 = 210) et ne budgète ni `__init__.py` (27 L de `Protocol`, exigé par `ARCHITECTURE.md`), ni les trois types que la signature publique impose — `Deadline`, `RawResponse`, `Outcome` (~45 L) — que `kernel` ne possède pas et qu'aucun module inférieur ne peut porter. | Rien à débloquer. Ratchet **shrink-only à partir de 345**. Toute réduction devra retirer du comportement testé. | — |
| 3. `jsonschema` n'est pas déclaré | La source de la revalidation l'utilise ; la stack du `MODULE.md` ne le contient pas et `requirements.txt` est hors de mon périmètre. | Rien : contourné sans dépendance (§ Journal). Si un besoin futur de valider un schéma **non dérivé d'un modèle Pydantic** apparaît, il faudra déclarer `jsonschema` — décision hors de mon périmètre. | contourné le 06:09 |

## Décisions locales

**La route est une donnée d'environnement, pas un paramètre d'appel.** `call(schema, system, user,
deadline)` ne porte pas d'URL : `base_url()` lit `PITHOS_OLLAMA_URL` à chaque appel, avec
`http://127.0.0.1:11434` par défaut, et **refuse tout hôte hors loopback**. C'est ce qui permet de
tester contre une vraie route locale sans ajouter un paramètre de test à la signature publique.

**`unknown_tool` sert de garde d'identité schéma ↔ modèle.** En mode `direct` il n'y a pas de
catalogue d'outils ; le code fermé prend donc le sens le plus proche et le seul utile ici : le
schéma présenté n'est pas celui du modèle contre lequel on revalide.

**`Deadline` porte les deux bornes** — murale et place de sortie réservée. Elles sont vérifiées au
même endroit parce qu'elles refusent l'appel pour la même raison : le contrat obligatoire ne tient
pas. `engine` la construit et décide des retries ; `bridge` ne décide de rien.

**Le double est un module, pas une classe.** Le `MODULE.md` § 7 parle d'« une file de réponses
fournie au constructeur ». Un objet ne peut pas satisfaire le même `Protocol` à membres statiques
que l'implémentation, ce qu'`AGENTS.md` § 11 exige. La file se charge donc par `script(...)` et se
vide par `reset()`, comme le double de `journal`. Quatre fabriques couvrent les six cas demandés :
`conformant`, `malformed` (qui porte à la fois `invalid_json`, `schema_violation` et « accepté par
le transport, rejeté localement »), `truncated`, `transport_error`.

**Le prompt système est une donnée, sa politique est ici.** `prompt/ling.md` ne contient que le
prompt — aucun commentaire de gouvernance, qui serait envoyé au modèle. La règle du `MODULE.md`
tient donc dans ce paragraphe et dans un test :
**tout ajout au prompt doit citer la mission où le mode d'échec a été observé**, et un test échoue
au-delà de 25 lignes non vides pour que le pavé de 129 lignes ne revienne pas par habitude.

**Aucune rédaction avant journalisation.** `journal.redact` n'est pas appelé sur le payload : le
`MODULE.md` § 9 écarte explicitement tout mécanisme de credential parce qu'**Ollama local n'a aucune
authentification**. Il n'y a rien à rédiger sur ce chemin. À revoir si une route authentifiée
apparaît un jour.

## Reprises traitées

| Source | Verdict | Fait ? | Note |
|---|---|---|---|
| `villani/openai_client.py:212-234` — client 23 L, timeout 300 s | Copier | oui | `TIMEOUT_SEC = 300`, borné par `min(deadline, 300)`. Streaming absent par décision. |
| `villani/openai_client.py:9-13` — `/v1` idempotent | Copier | oui | `normalize_base_url`, plus le refus hors loopback. |
| `villani/openai_client.py:75-86` — insertion de `response_format` | Adapter | oui | `build_payload`, mode strict. C'est la cible du spike n°2. |
| `villani/openai_client.py:89-98` — `length` distingué de `stop` | Copier | adapté | Repris **en plus strict** : la source rabat `content_filter` sur `stop`, nous le rendons `unknown_stop`. |
| `villani/context_budget.py` (3 lignes) — unités atomiques, `_preserve_exact`, résumé | Copier | non | Le compactage d'historique appartient à `engine/context`. |
| `villani/state_runtime.py:396-437` — valider avant le réseau | Inspirer | oui | Schéma validé dans `normalize_schema` et budget vérifié **avant** tout POST. |
| `pi/constrained-sampling.ts:208` — `require`, pas `prefer` | Adapter | oui | `strict: True`, aucun repli. |
| `pi/constrained-sampling.ts:117` — sous-ensemble réellement envoyé | Adapter | oui | `SUPPORTED_KEYWORDS` déclaré ; le schéma exact de `Criterion` est testé. |
| `pi/validation.ts:59` — **contre-exemple**, pas de coercition | Adapter | oui | Testé : `"symbols": "f"` est un `schema_violation`, jamais une liste réparée. |
| `pi/json-parse.ts:104` — jamais de JSON partiel ou réparé | Adapter | oui | Aucune extraction, aucun repli `{}`. |
| `pi/openai-completions.ts:357` — enregistrer le payload effectif | Adapter | oui | `_record` : endpoint, modèle, `schema_sha256`, plafond, sampling, issue, usage. |
| `pi/openai-completions.ts:1550` — conserver `raw_stop_reason` | Adapter | oui | Champ dédié ; une raison inconnue reste un échec explicite. |
| `pi/openai-completions.ts:601` — séparer thinking et contenu | Adapter | oui | Deux formes gérées, deux tests. |
| `pi/openai-completions.ts:364` — désactiver les retries implicites | Adapter | oui | `HTTPTransport(retries=0)` ; une 503 = une requête, comptée. |
| `pi/openai-completions.ts:692` — exiger une terminaison explicite | Adapter | oui | Sans streaming, la terminaison **est** le `finish_reason`, et il est exigé. |
| `pi/openai-completions.ts:1507` — usage sans double comptage | Adapter | oui | `usage` rendu brut, jamais fusionné avec `prompt_estimate`. |
| `pi/error-body.ts:38` — diagnostic borné, corps complet dans l'artefact | Adapter | oui | `detail` borné à 200 caractères ; extrait de corps borné à 500 dans la trace. |
| `pi/abort-signals.ts:6` · `pi/abort.ts:17` — annuler ≠ tuer | Adapter | partiel | Prouvé que l'effet survit à l'abandon ; la *vérification de fin* n'existe pas. Voir § Journal. |
| `pi/simple-options.ts:15` — réserver la sortie avant l'appel | Adapter | oui | `budget_refused`, aucune requête émise. |
| `pi/simple-options.ts:75` — borner le thinking | Adapter | non | Aucun paramètre de thinking envoyé ; les noms Pi ne prouvent pas leur support par Ollama. |
| `pi/estimate.ts:114` — estimation ≠ usage mesuré | Adapter | oui | `prompt_estimate` séparé de `usage`, et nommé comme une estimation. |
| `pi/overflow.ts:134` · `kilo/overflow.ts:11-20` · `our/context_budget.py:38-93` — classer le dépassement | Adapter/Copier | non | La **réduction déterministe** après overflow est une politique métier : `engine`. |
| `pi/sanitize-unicode.ts:21` — ne pas corriger silencieusement | Adapter | oui | Aucune sanitisation : une sortie invalide est rejetée, jamais réécrite. |
| `pi` (2 fixtures de test) | Adapter | oui | `length` avec JSON syntaxiquement complet est testé, et ne produit rien d'exploitable. |
| `kilo/json-schema.ts:8-19,28-88,83-85,121-158` — `normalize()` | Traduire | oui | Le cœur de `schema.py`, avec les trois corrections notées au § Journal. |
| `kilo/transform.ts:588-631` — sampling `ling` | Traduire | oui | `SAMPLING`, versionné comme donnée. |
| `kilo/transform.ts:21` — point d'entrée unique du sortant | Traduire | oui | `build_payload` est le seul constructeur de payload. |
| `kilo/session/prompt/ling.txt` (129 L) | Traduire | réduit | `prompt/ling.md`, 11 lignes non vides. Le contrat impose de démarrer court ; un test garde la borne. |
| `kilo/tool.ts:25-33,100-142` — validation d'entrée séparée de l'exécution | Adapter | oui | `revalidate` ne construit rien avant d'avoir validé ; aucune exécution ici. |
| `kilo/codemode/tool-schema.ts:35-107` | Inspirer | non | La génération de schéma depuis des types est déjà couverte par Pydantic. |
| `our/request_wire_custom_validation.py:107-170` — revalider contre le schéma exact | Copier | adapté | Sans `jsonschema` : identité schéma ↔ modèle prouvée, puis validation Pydantic. Voir § Journal. |
| `our/request_wire_custom_validation.py:15-22` — cinq codes fermés | Copier | adapté | Les cinq du `MODULE.md`, dont `constant_refused` qui n'existe pas dans la source. |
| `our/request_wire_custom_validation.py:85-87` — `parse_constant` | Copier | oui | Une ligne, une classe de littéral illégal fermée. Trois littéraux testés. |
| `our/request_wire_custom_validation.py:89-105` — contenir l'échec de schéma | Copier | sans objet | Le `catch` large ne protégeait que du travail `jsonschema`, absent ici. |
| `our/request_wire_custom_validation.py:24-42` — reçu parser-issued | Inspirer | adapté | `Ok`/`Err` portent le `schema_sha256`. Le jeton de fabrique n'est pas repris : `dataclass` gelée, un appelant n'a rien à gagner à en forger une. |
| `our/llm.py:2241-2250` — `response_format` est une intention | Inspirer | oui | C'est la raison d'être de la revalidation locale, obligatoire quoi qu'il arrive. |
| `our/local_model.py:579-617` — `n_ctx_train` lu sur `/v1/models` | Copier | oui | Avec le repli `context_window` de la source. **Le repli `4096` de `get_context_length` est refusé** — voir § Journal. |
| `our/capability_evidence.py:52-158` — provenance sourcée | Adapter | oui | Trois valeurs implémentées ; `unprobeable` fail-closed. |
| `our/capability_evidence.py:159-203` — `require_fresh` explicite | Copier | non | Sans cache de capacité, la fraîcheur n'a pas d'objet : `probe()` mesure à chaque appel. |
| `prime/refinement.ts:570-589` — tronqué vs malformé | Adapter | oui | Deux chemins distincts : `Outcome.truncated` (protocole) et `ErrorCode.invalid_json` (contenu). |
| `prime` — `extractJsonObject`, trois voies de repli | Adapter | **refusé** | Le `MODULE.md` § 3 l'interdit explicitement : récupérer une sortie mal formée, c'est laisser passer un littéral par une autre porte. Le pointeur reste ; l'interdit prime. |
| `prime` — normaliser sans jeter les champs invalides | Traduire | oui | `detail` nomme le chemin exact du champ fautif au lieu de le supprimer. |
| `prime` — budget de sortie dérivé du modèle | Traduire | adapté | Dérivé de la **fenêtre lue** par la sonde, plus honnête qu'une constante. |
| `prime` — forcer le mode non-raisonnant | Traduire | non | Aucun paramètre Ollama connu pour l'imposer sur Ling ; le thinking est **séparé** au retour, ce qui tient la même propriété sans supposer un réglage. |
| `prime` — `stopReason === "length"` erreur nommée | Traduire | oui | `Outcome.truncated`. |
| `prime/agent-loop.ts:106-143` — statut discriminé | Inspirer | oui | `RawResponse.outcome`, cinq issues fermées, jamais un `None` surchargé. |
| `prime/agent-loop.ts:47-79` — `raceWithAbort` | Inspirer | non | Sans streaming ni annulation concurrente, la course n'a pas d'objet : le timeout httpx suffit. |
| **F — Unsloth (16 lignes)** | Adapter | 2 sur 16 | **Faites** : séparer texte visible et thinking (`_inference.py:259`), refuser une URL hors loopback (`:634,650`). Les quatorze autres décrivent **le serveur MCP produit** et le mode `agentic` — elles appartiennent au dépôt de campagne et à `engine`, pas à la frontière modèle. |
| **G — OpenHands (20 lignes)** | Adapter | 1 sur 20 | **Faite** : normalisation d'URL et canonicalisation d'hôte avant comparaison. Les autres portent sur la configuration d'un agent-server, ses tags, ses versions et ses listes d'outils — `campaign`, `engine` et `observatory`. Les headers d'authentification sont **écartés** : Ollama local n'en a pas. |
| **H — SWE-agent (13 lignes)** | Adapter | 1 sur 13 | **Faite** : prompt versionné et paramétrable (`prompt/ling.md`). Le reste est configuration de retry, historique et fenêtres d'observation — explicitement **métier**, donc `engine` (`MODULE.md` § 3). |
| **I — Langfuse (5 lignes)** | Adapter | 1 sur 5 | **Faite** : tokenisation locale à incertitude explicite, séparée de l'usage fourni. Interpolation de prompt, références versionnées et déballage MCP appartiennent à `campaign` et au produit. |
