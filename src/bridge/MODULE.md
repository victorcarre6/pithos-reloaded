# `bridge` — la frontière modèle

> **Lis [`AGENTS.md`](../../AGENTS.md) avant de commencer.** Ce fichier est ton contrat complet : tu ne
> devrais pas avoir besoin d'ouvrir `docs/`. Ton point d'entrée exact est la rubrique « Prochaine action » de
> [`STATE.md`](STATE.md), à côté de ce fichier.
>
> **Tu ne commites, ne pousses et ne merges jamais.** Tes commits se *proposent* dans [`git.md`](git.md),
> avec les `ga`/`gcmsg` exacts — voir [`AGENTS.md`](../../AGENTS.md) § 7.

**Cible** : ~250 L · ratchet **shrink-only**
**Dépend de** : `kernel`, `journal`.
**Niveau de dépendance** : 2.
**Stack** : `httpx` · Pydantic v2. **Ni LangChain, ni `instructor`, ni `outlines`** — la contrainte de
décodage est appliquée côté serveur.

## 1. Autorité

**250 lignes qui méritent leur nom : c'est le point d'application de la contrainte dure n°1.** On doit
pouvoir pointer ce module et dire *« tout ce que le modèle peut émettre est défini ici »*.

## 2. Interface publique

```python
def normalize_schema(model: type[BaseModel]) -> dict:
    "Résout $defs/$ref, borne les integers, restreint au sous-ensemble de mots-clés supporté."

def call(schema: dict, system: str, user: str, deadline: Deadline) -> RawResponse:
    "Un POST bloquant. Une requête, une réponse complète. Pas de streaming."

def revalidate(raw: str, schema: dict, model: type[BaseModel]) -> Ok[BaseModel] | Err[ErrorCode]:
    "Revalide localement contre LE SCHÉMA EXACT ENVOYÉ. Cinq codes d'erreur fermés."

def probe() -> Capability:
    "Trois contrôles avant campagne. Refuse de démarrer si l'un échoue."
```

**Cinq codes d'erreur fermés** : `invalid_json`, `arguments_not_object`, `unknown_tool`,
`schema_violation`, `constant_refused`.

## 3. Interdits

- **N'importe jamais `engine`.** C'est la deuxième règle d'import du projet. La **politique de retry est
  métier** et vit dans `engine` : `bridge` rend une erreur typée, il ne décide pas quoi en faire.
- **N'importe jamais `verifier`, `campaign`, `workspace`.**
- **Aucun repli silencieux sur la contrainte de décodage.** Le mode est **`require`**, jamais `prefer` : un
  repli silencieux ferait retomber la contrainte dure n°1 sans qu'aucune trace ne le signale.
- **Ne récupère jamais une sortie mal formée par extraction.** Récupérer, c'est laisser passer un littéral du
  modèle par une autre porte. On rejette et on remonte un code fermé.
- **Pas de streaming.** Voir § 4.

## 4. Les quatre pièges nommés de la frontière

La décision 17 les énumère. Ils sont la raison d'être du module.

1. **`require`, pas `prefer`.** Refus explicite si le mode strict n'est pas disponible.
2. **Thinking ≠ contenu.** N'extraire le `Criterion` que du contenu exploitable, jamais du bloc de
   raisonnement. Sur la réponse complète : trois lignes.
3. **Terminaison explicite.** Un `finish_reason` `length` **n'est pas** un `stop` : une génération tronquée
   n'est pas une réponse.
4. **Le budget réserve la sortie.** Réserver la place de la réponse **avant** l'appel ; si le contrat
   obligatoire ne rentre pas, ne pas appeler.

⚠️ **`response_format` est une intention, pas une garantie** !
→ La route peut l'ignorer, et le retry a le droit de la retirer. **La revalidation locale contre le schéma
exact envoyé est obligatoire quoi qu'il arrive** : l'acceptation par le transport n'autorise rien.

**Pas de streaming.** En mode `direct`, `bridge` fait un appel borné et attend un objet JSON complet. Pi
énonce lui-même la règle qui rend le flux inutile — *« ne jamais exécuter un JSON partiel ou réparé »* — et
**l'incident de contexte le plus grave de v1 était un incident de streaming** : 12 419 `thinking_delta`
consécutifs, zéro tool call.

## 5. Contenu

| Fichier | Contenu | ~L |
|---|---|---:|
| `client.py` | `httpx`, `POST /v1/chat/completions`, timeout 300 s, normalisation d'URL idempotente | 40 |
| `schema.py` | normalisation Pydantic → JSON Schema décodable, validation avant envoi | 70 |
| `revalidate.py` | revalidation locale, cinq codes fermés, refus de `NaN`/`Infinity` | 60 |
| `probe.py` | trois contrôles d'avant-campagne | 40 |
| `prompt/ling.md` | **fichier de données**, hors décompte de lignes | — |

**Échantillonnage fixé, et versionné comme donnée** : `temperature 0.3`, `top_p 0.95`, `top_k 20` — valeurs
mesurées par Kilo Code sur la famille `ling`, qui est notre modèle exact (décision 20).

**Le prompt système démarre court — ~20 lignes, pas 129.** Aucun des sept modes d'échec de Ling documentés
par Kilo n'a été mesuré sur *nos* prompts, et un prompt de 129 lignes consomme une part notable des 16 k à
chaque appel. **Chaque ajout ultérieur doit citer la mission où le mode d'échec a été observé** — le prompt
est un journal de contre-mesures, pas un pavé hérité.

**La sonde, trois contrôles, ~40 L** : lire `n_ctx_train` sur `/v1/models` (**la fenêtre est lue, pas
supposée**), envoyer un schéma `Criterion` réel et vérifier qu'il revalide, refuser de démarrer sinon. La
fenêtre porte sa provenance en enum à trois valeurs — `confirmed` / `asserted` / `unprobeable` — et
`unprobeable` est **fail-closed**.

## 6. Critères de socle que ce module rend verts

- **Aucun littéral émis par le modèle ne traverse la frontière modèle → exécution.**
- **Le schéma envoyé au modèle est normalisé et testé** : `$defs`/`$ref` résolus, bornes explicites, vérifié
  contre le backend réel **avant toute campagne**.
- **La sortie du modèle est revalidée localement contre le schéma exact envoyé** avant toute exécution.

## 7. Le double

`tests/doubles/bridge.py` — un **faux fournisseur scénarisé** : une file de réponses fournie au
constructeur, chacune étant soit un JSON valide, soit un JSON invalide, soit une troncature, soit une erreur
HTTP. **`engine` s'en sert pour tester la politique de retry sans Ollama.**

Le double doit savoir jouer : réponse conforme, `invalid_json`, `schema_violation`, `finish_reason=length`,
timeout, et **une réponse que le transport accepte mais que la revalidation locale rejette** — ce dernier cas
est celui qui prouve que la revalidation sert à quelque chose.

## 8. Fini quand

- [ ] `normalize_schema` résout `$defs`/`$ref` et borne les integers sur un `Criterion` réel ; le schéma
      résultant est validé avant envoi.
- [ ] Une réponse acceptée par le transport mais non conforme au schéma exact envoyé est **rejetée
      localement**, avec le bon code fermé.
- [ ] `NaN` et `Infinity` sont refusés par `parse_constant` — test explicite.
- [ ] `finish_reason=length` est distingué de `stop` et ne produit **jamais** un objet exploitable.
- [ ] Le thinking est séparé du contenu, et le `Criterion` n'est jamais extrait du bloc de raisonnement.
- [ ] Les retries implicites du SDK/client sont **désactivés** — test qui compte les requêtes.
- [ ] Le budget réserve la sortie : si le contrat obligatoire ne rentre pas, **aucun appel n'est fait**.
- [ ] `probe()` refuse de démarrer si `n_ctx_train` est illisible (`unprobeable` ⇒ fail-closed).
- [ ] Annuler l'attente **ne tue pas** l'opération : la fermeture du client attend la fin réelle de l'effet.
- [ ] `tests/boundaries/` confirme qu'aucun import de `engine` n'existe.

## 9. Pièges connus, et ce qui a été écarté

| Écarté | Pourquoi |
|---|---|
| **Le streaming SSE** (~100 L) | on ne peut rien faire d'un delta, et le pire incident de contexte de v1 était un incident de streaming |
| **`convert_openai_response_to_anthropic`** | **du legacy v1 : aucun chemin Anthropic n'existe**, la contrainte n°5 l'exclut |
| **Les transformations par fournisseur** | un fournisseur, un modèle. Une abstraction pour une implémentation |
| **La sélection de prompt par famille de modèle** | spéculatif tant que le périmètre tient : un seul modèle, contrainte assumée |
| **Tous les mécanismes de credential** | **Ollama local n'a aucune authentification** — headers d'auth, `route_fingerprint`, résolution de clé par priorité |
| **`test_tool_calling`** | sonde une capacité que le mode `direct` n'utilise pas |

**Le point d'insertion de `response_format` est déjà repéré** : `villani/openai_client.py:75-86`. C'est la
cible du **spike n°2 reformulé** — la question n'est plus « la route applique-t-elle la grammaire ? » (la
réponse est *pas toujours*) mais *« quel est le taux de rejet de la revalidation locale, par code d'erreur ? »*.

---

## Sources — reprises retenues

**110 lignes.** Chaque pointeur se lit dans `resources/`. Le détail complet et le contexte de chaque partie sont dans [`resources/IMPORT_REPORT.md`](../../resources/IMPORT_REPORT.md).
**Lis la source avant de porter.** Une reprise collée sans être relue est un défaut.

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| A4.3 | `openai_client.py:212-234` | `OpenAIClient` — 23 lignes, `httpx`, timeout **300 s** (un local lent n'est pas une panne), streaming et non-streaming séparés. | **Copier** |
| A4.3 | `openai_client.py:9-13` | `normalize_openai_base_url` — ajoute `/v1` de façon idempotente. | **Copier** |
| A4.3 | `openai_client.py:75-86` | `build_openai_payload` — **le point d'insertion de `response_format`**, alimenté par `Criterion.model_json_schema()`. | **Adapter** |
| A4.3 | `openai_client.py:89-98` | Mapping `finish_reason` avec `length` distingué de `stop`. **Une génération tronquée n'est pas une génération terminée** — cas nominal sur 16k. | **Copier** |
| A4.3 | `context_budget.py:82-93` | `_group_atomic_units` — un `tool_use` et son `tool_result` sont **inséparables** au compactage. | **Copier** |
| A4.3 | `context_budget.py:204-205` | `_preserve_exact` — un contenu portant `@@` ou `diff --git` n'est **jamais** compacté. Un diff résumé est un diff faux. | **Copier** |
| A4.3 | `context_budget.py:208-222` | `_summarize_tool_result` — compactage par extraction de signal, jamais par troncature aveugle. | **Copier** |
| A4.3 | `state_runtime.py:396-437` | `validate_anthropic_tool_sequence` — validation **avant** l'appel réseau. Un message mal formé échoue localement, gratuitement. | **Inspirer** |


#### B — Pi · `resources/pi-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| B3.3 | `packages/ai/src/api/constrained-sampling.ts:208` | **`require` et non `prefer`** : refus explicite si le mode strict est indisponible. Ne démontre pas `response_format` sur Ollama `/v1` — le spike reste indispensable. | **Adapter** |
| B3.3 | `packages/ai/src/api/constrained-sampling.ts:117` | Compatibilité du sous-ensemble JSON Schema réellement envoyé : `$defs`/`$ref`, unions, optional/null, `additionalProperties`. Tester le schéma exact de `Criterion` avec Ling. | **Adapter** |
| B3.3 | `packages/ai/src/utils/validation.ts:59` | **Contre-exemple** : Pi convertit `null` en 0/false/chaîne vide. Chez nous validation stricte, champs supplémentaires refusés, aucune coercition. Conserver la sortie brute rejetée. | **Adapter** |
| B3.3 | `packages/ai/src/utils/json-parse.ts:104` | **Ne jamais exécuter un JSON partiel ou réparé.** Accolade manquante ou fallback `{}` ⇒ rejet, pas exécution. | **Adapter** |
| B3.3 | `packages/ai/src/api/openai-completions.ts:357` | Enregistrer le payload effectif au spike : modèle, `response_format`, messages, plafond, sampling, endpoint. **Ne pas exposer un hook arbitraire au modèle.** | **Adapter** |
| B3.3 | `packages/ai/src/api/openai-completions.ts:692` | Exiger une terminaison explicite du stream. Un socket fermé avec du JSON plausible n'est pas une réussite. | **Adapter** |
| B3.3 | `packages/ai/src/api/openai-completions.ts:1550` | Normaliser la cause de fin en conservant `raw_stop_reason`. Un `finish_reason` inconnu reste un échec explicite. | **Adapter** |
| B3.3 | `packages/ai/src/api/openai-completions.ts:1507` | Normaliser l'usage sans double comptage cache/reasoning. Conserver le JSON brut et une projection documentée. | **Adapter** |
| B3.3 | `packages/ai/src/api/openai-completions.ts:601` | **Séparer thinking et contenu exploitable.** N'extraire `Criterion`/`new_source` que du contenu final désigné. | **Adapter** |
| B3.3 | `packages/ai/src/api/openai-completions.ts:364` | **Désactiver les retries implicites du SDK.** Éviter la multiplication SDK × bridge × Prefect. Vérifier le nombre de requêtes au faux serveur sur une 503. | **Adapter** |
| B3.3 | `packages/ai/src/utils/error-body.ts:38` | Diagnostic borné : type/statut/cause + extrait, corps complet dans l'artefact. **Un 400 de schéma ne se confond pas avec un 503 transitoire.** | **Adapter** |
| B3.3 | `packages/ai/src/utils/abort-signals.ts:6` | Combiner annulation opérateur et deadline, puis nettoyer les listeners. | **Adapter** |
| B3.3 | `packages/ai/src/utils/abort.ts:17` | **Annuler l'attente ne tue pas l'opération.** Prévoir fermeture du stream/client et vérification de fin. Conditionne la borne murale réelle. | **Adapter** |
| B3.3 | `packages/ai/src/api/simple-options.ts:15` | Réserver la place de la sortie avant l'appel. **Si le contrat obligatoire ne tient pas, refuser l'appel.** | **Adapter** |
| B3.3 | `packages/ai/src/api/simple-options.ts:75` | Borner le thinking pour garder assez de sortie au contrat. Les noms de paramètres Pi ne prouvent pas leur support local. | **Adapter** |
| B3.3 | `packages/ai/src/utils/estimate.ts:114` | Estimation explicitement distincte de l'usage mesuré. `chars/4` est fragile pour Unicode et code. Journaliser les deux séparément. | **Adapter** |
| B3.3 | `packages/ai/src/utils/overflow.ts:134` | Classifier dépassement de contexte et sortie trop courte séparément. Un overflow provoque une **réduction déterministe**, pas un retry identique. | **Adapter** |
| B3.3 | `packages/ai/test/constrained-sampling.test.ts:88` | Fixtures `require`/`prefer` et schémas non supportés. Le succès de ces tests TypeScript ne valide ni Pydantic ni Ollama. | **Adapter** |
| B3.3 | `packages/ai/test/openai-completions-raw-stop-reason.test.ts:55` | Corpus de raisons terminales connues et inconnues. Ajouter `length` avec JSON syntaxiquement complet : **si le protocole dit tronqué, rien n'est appliqué.** | **Adapter** |
| B3.3 | `packages/ai/src/utils/sanitize-unicode.ts:21` | Cas Unicode invalides. Décider explicitement rejet ou échappement ; **ne pas corriger silencieusement** un symbole ni les octets d'un fichier cible. | **Adapter** |


#### C — Kilo Code · `resources/kilocode-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| C3.3 | `opencode/src/tool/json-schema.ts:28-88` | **`normalize()` — l'outillage manquant du spike n°2.** Résolution des `$defs`/`$ref` que Pydantic v2 émet pour toute enum et tout modèle imbriqué. | **Traduire** |
| C3.3 | `opencode/src/tool/json-schema.ts:83-85` | Un `integer` sans bornes fait échouer certaines grammaires de décodage contraint : bornes explicites obligatoires. | **Traduire** |
| C3.3 | `opencode/src/tool/json-schema.ts:121-158` | Validation du schéma résultant avant envoi. | **Traduire** |
| C3.3 | `opencode/src/tool/json-schema.ts:8-19` | Sous-ensemble de mots-clés réellement supporté, déclaré explicitement. | **Traduire** |
| C3.3 | `opencode/src/provider/transform.ts:588-631` | **`temperature 0.3`, `top_p 0.95`, `top_k 20` pour la famille `ling`.** Mesuré par un tiers sur notre modèle. | **Traduire** |
| C3.3 | `opencode/src/session/prompt/ling.txt` (129 L) | **Le catalogue des modes d'échec de Ling et leurs contre-mesures.** Voir § C1.2. | **Traduire** |
| C3.3 | `opencode/src/session/overflow.ts:11-20` | Détection de dépassement de contexte séparée des autres erreurs. Convergent avec `pi/overflow.ts:134`. | **Traduire** |
| C3.3 | `opencode/src/tool/tool.ts:25-33,100-142` | Contrat d'outil : schéma, description, exécution, et validation d'entrée séparée de l'exécution. | **Adapter** |
| C3.3 | `codemode/src/tool-schema.ts:35-107` | Génération de schéma depuis des types, avec sous-ensemble contrôlé. | **Inspirer** |
| C3.3 | `opencode/src/provider/transform.ts:21` | Point d'entrée unique de toute transformation sortante. | **Traduire** |


#### D — Ouroboros · `resources/ouroboros-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| D3.4 | `our/request_wire_custom_validation.py:107-170` | Revalidation locale contre **le schéma exact envoyé**, reçu liant `candidate`/`catalog`/`schema`/`arguments` par SHA-256. **L'acceptation par le transport n'autorise pas l'exécution.** | **Copier** |
| D3.4 | `our/request_wire_custom_validation.py:15-22` | Cinq codes fermés — `invalid_json`, `arguments_not_object`, `unknown_tool`, `invalid_schema`, `schema_validation_failed`. Cinq raisons de rejet, pas un booléen. | **Copier** |
| D3.4 | `our/request_wire_custom_validation.py:85-87` | `parse_constant` refusant `NaN`/`Infinity`. **Une ligne, une classe de littéral illégal fermée avant Hypothesis.** | **Copier** |
| D3.4 | `our/request_wire_custom_validation.py:89-105` | Tout échec de construction/résolution de schéma est contenu à sa frontière et devient `invalid_schema`. `jsonschema` n'a pas de base commune publique pour ces erreurs. | **Copier** |
| D3.4 | `our/request_wire_custom_validation.py:24-42` | Reçu **parser-issued** : le constructeur refuse toute instanciation hors parseur. Une attestation ne se fabrique pas côté appelant. | **Inspirer** |
| D3.4 | `our/llm.py:2241-2250` · `:183-186` | `response_format` est une **intention** que la ladder de retry a le droit de retirer et que certaines routes ignorent. | **Inspirer** |
| D3.4 | `our/context_budget.py:38-93` | Un dépassement de contexte est reconnu **par code structuré d'abord**, texte ensuite ; un code structuré l'emporte toujours. Sépare « prompt trop grand » de « sortie trop grande ». | **Copier** |
| D3.4 | `our/local_model.py:579-617` | `health_check` — le `n_ctx` réel est **lu sur `/v1/models`** (`meta.n_ctx_train`), pas supposé. | **Copier** |
| D3.4 | `our/capability_evidence.py:52-158` | La fenêtre de contexte est une **preuve sourcée** (`confirmed`/`asserted`/`unprobeable`/`failed`) liée à une empreinte de route. `unknown` ⇒ fail-closed. | **Adapter** |
| D3.4 | `our/capability_evidence.py:159-203` | `require_fresh` **explicite au site d'appel** : autoriser exige la fraîcheur, dégrader ne l'exige pas. *« An outage must never erase a prior confirmed record. »* | **Copier** |


#### E — Prime Agent · `resources/prime-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| E3.3 | `ca/core/refinement/refinement.ts:570-589` | `isIncompleteJson` — distingue une réponse **tronquée** (chaîne non fermée, profondeur > 0) d'une réponse **malformée**. `JSON.parse` décrit le fragment ; ceci nomme la cause. | **Adapter** |
| E3.3 | `bridge` | `extractJsonObject` — trois voies : objet nu, bloc ```` ```json ````, découpe par accolades, avec re-diagnostic **sur le texte original**. **C'est le repli obligatoire quand la contrainte de schéma n'est pas appliquée** (décision 17). | **Adapter** |
| E3.3 | `bridge` | Normalisation **sans jeter les champs invalides**, pour que la validation d'application puisse les nommer. | **Traduire** |
| E3.3 | `bridge` | Budget de sortie **dérivé du modèle** (`min(model.maxTokens, plafond)`), avec le commentaire expliquant qu'une constante tronquerait « exactement les propositions multi-edits qui comptent le plus ». | **Traduire** |
| E3.3 | `bridge` | **Forcer le mode non-raisonnant** pour tout appel devant rendre du JSON structuré. *« Un modèle qui dépense son budget en thinking ne rend pas de JSON final. »* Ling émet du raisonnement. | **Traduire** |
| E3.3 | `bridge` | `stopReason === "length"` traité comme une **erreur nommée distincte**, avec un message qui dit quoi faire. Convergent avec Villani et Ouroboros. | **Traduire** |
| E3.3 | `ag/agent-loop.ts:106-143` | `PostTurnResult<T>` — statut discriminé plutôt qu'un `null` surchargé. | **Inspirer** |
| E3.3 | `ag/agent-loop.ts:47-79` | `raceWithAbort` — course entre l'opération et le signal, avec capture du rejet pour ne pas laisser d'exception non gérée. Convergent avec `pi/abort.ts:17`. | **Inspirer** |


#### F — Unsloth · `resources/unsloth-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| F3.3 | `studio/backend/mcp_server.py:86` | **Fabrique FastMCP unique avec liste d'outils explicitement enregistrée.** Aligne directement la surface du produit sur `registry.json`. | **Adapter** |
| F3.3 | `studio/backend/mcp_server.py:20` | Middleware bearer token **exact, non vide et ASCII**, validé avant toute exposition distante. | **Adapter** |
| F3.3 | `studio/backend/mcp_server.py:77` | **Borner (`clamp`) les entiers fournis par MCP avant appel de route.** Ne jamais faire confiance au client. | **Adapter** |
| F3.3 | `studio/backend/mcp_server.py:97` | Outil de statut **read-only** comme sonde de santé minimale. | **Adapter** |
| F3.3 | `studio/backend/mcp_server.py:126` | **Séparer les outils de lecture des outils de mutation.** Deux familles, deux politiques. | **Adapter** |
| F3.3 | `studio/backend/mcp_server.py:166` | **Valider une recette sans lancer le job** : une gate de schéma avant mutation. | **Adapter** |
| F3.3 | `studio/backend/mcp_server.py:70` | Convertir les réponses Pydantic en JSON plat avant émission MCP, pour conserver une **trace portable**. | **Adapter** |
| F3.3 | `unsloth_cli/_inference.py:259` | **Séparer texte visible et thinking** avant projection d'une réponse. **Sixième source à le dire.** | **Adapter** |
| F3.3 | `unsloth_cli/_inference.py:318` | Transformer une erreur de stream en **exception structurée avant d'écrire un événement de succès**. | **Adapter** |
| F3.3 | `unsloth_cli/_inference.py:634,650` | **Refuser les URL hors loopback** pour les connexions de contrôle locales ; **vérifier l'identité du serveur** avant de lui transmettre une requête. | **Adapter** |
| F3.3 | `unsloth_cli/_inference.py:616,752` | Découverte d'un serveur local avec candidats loopback et timeout court ; `ensure_loaded` **séparé** du streaming. | **Adapter** |
| F3.3 | `unsloth_cli/commands/start.py:1591` | Résoudre une clé par **priorité documentée** (cache, configuration, environnement) — **jamais par le modèle**. | **Adapter** |
| F3.3 | `unsloth_cli/claude_subagent_mcp.py:60,84,135` | Pont stdio vers un agent local : tâche bornée, **sortie capturée et bornée avant inclusion dans la trace**, arrêt propre du child **et de son groupe**. | **Adapter** |
| F3.3 | `unsloth_cli/codex_subagent_mcp.py:85` | **Aucune détection implicite du provider** : contrat de tâche stable, variante explicite. | **Adapter** |
| F3.3 | `unsloth_cli/pi_subagent.ts:67` | **Limiteur de slots concurrents** pour sous-agents, à adosser au budget de mission. Utile au mode `agentic` différé. | **Adapter** |
| F3.3 | `unsloth_cli/pi_subagent.ts:105` | Signaux envoyés **au process group**, pas seulement au parent. | **Adapter** |


#### G — OpenHands · `resources/OpenHands-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| G3.1 | `src/api/agent-server-config.ts:1,203,209` | **Répertoire de travail par défaut centralisé** ; workspace d'une conversation construit depuis une base contrôlée et un identifiant opaque ; **une fonction unique de chemin**, réutilisée par `engine` et `observatory`. | **Adapter** |
| G3.1 | `src/api/agent-server-config.ts:25,55` | Normaliser une URL de backend (valeurs vides, variantes triviales) et **canonicaliser un hostname avant comparaison** de provenance. | **Adapter** |
| G3.1 | `src/api/agent-server-config.ts:273` | Headers d'authentification construits **en un seul point**. | **Adapter** |
| G3.1 | `src/api/agent-server-compatibility.ts:19,50,81` | Version minimale compatible, **codes d'erreur fermés**, refus avant mission ; erreur typée distinguant **backend absent, indisponible et détail de connexion**. | **Adapter** |
| G3.1 | `src/api/agent-server-compatibility.ts:95` | **Une version inconnue est un état distinct, jamais la version courante.** | **Adapter** |
| G3.1 | `src/api/agent-server-compatibility.ts:252` | Comparaison **sémantique** de versions, jamais lexicographique. | **Adapter** |
| G3.1 | `src/api/agent-server-adapter.ts:475,546` | **Tags à clés réservées** reliant campagne, source et run ; projection stable vers une vue filtrée. | **Adapter** |
| G3.1 | `src/manifests/types.ts:30` | **Espaces de placeholders fermés** — aucune expression libre. | **Adapter** |
| G3.1 | `src/manifests/types.ts:90` | Nom de fichier de configuration de bundle **canonique**. | **Adapter** |
| G3.1 | `src/manifests/types.ts:380` | Énumérations fermées pour les filtres et tris de l'observatory. | **Adapter** |
| G3.3 | `src/api/agent-server-client-options.ts:22,38,52` | Erreur dédiée quand aucun backend n'est configuré ; host et port **normalisés avant construction** ; **fabrique typée des options — aucune URL assemblée dans l'appelant**. | **Adapter** |
| G3.3 | `src/api/agent-server-compatibility.ts:144,158` | Cache d'informations backend **explicitement invalidé au changement d'hôte** ; déterminer **mécaniquement** si un outil est annoncé par le backend. | **Adapter** |
| G3.3 | `src/api/agent-server-compatibility.ts:149` | Cache court de `/server_info` **indexé par hôte**, pour éviter les probes répétées. | **Adapter** |
| G3.3 | `src/api/agent-server-adapter.ts:136` | **Liste fermée d'outils par défaut** — ne jamais accepter une liste arbitraire du modèle. | **Adapter** |
| G3.3 | `src/api/agent-server-adapter.ts:143` | **Borner `max_iterations`** avec une valeur de repli sûre. | **Adapter** |
| G3.3 | `src/api/agent-server-adapter.ts:205,245` | Services runtime récupérés **avant** composition du contexte ; endpoints rendus sous forme de **suffixe système explicite et borné**. | **Adapter** |
| G3.3 | `src/api/agent-server-adapter.ts:668,706` | Politique de confirmation des outils **séparée des settings bruts** ; **prédicat unique d'inclusion**. | **Adapter** |
| G3.3 | `src/api/agent-server-adapter.ts:824` | **Contexte agent structuré plutôt qu'une chaîne opaque.** Converge avec la décision 14. | **Adapter** |
| G3.3 | `src/api/agent-server-adapter.ts:1151` | **Secrets isolés**, jamais mélangés aux métadonnées publiques. | **Adapter** |
| G3.3 | `src/api/agent-server-adapter.ts:1174,1335` | Fabrique de requête **séparée du transport** ; requête de planification **distincte** de la conversation d'exécution. | **Adapter** |


#### H — SWE-agent · `resources/SWE-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| H4.1 | `sweagent/agent/models.py:55` | Configuration de retry **Pydantic typée**, valeurs par défaut explicites. | **Adapter** |
| H4.1 | `sweagent/agent/models.py:66` | Contrat de modèle **provider-agnostic**, paramètres d'appel séparés de l'agent. | **Adapter** |
| H4.1 | `sweagent/agent/models.py:273,292` | Compteurs globaux de tokens et coût **conservés hors du message modèle** ; statistiques par instance. | **Adapter** |
| H4.3 | `sweagent/agent/agents.py:60` | **Template de prompt versionné** et paramétrable par backend. | **Adapter** |
| H4.3 | `sweagent/agent/agents.py:149` | Configuration d'agent minimale : modèle, tools, historique, limites. | **Adapter** |
| H4.3 | `sweagent/agent/action_sampler.py:16,23,49` | Sortie d'action Pydantic conservant **texte, action et métadonnées séparément** ; interface remplaçable ; sous-agent de consultation **séparé du chemin principal**. | **Adapter** |
| H4.3 | `sweagent/agent/models.py:311,875` | Classe abstraite avec **point d'appel commun** ; fabrique depuis configuration fermée. | **Adapter** |
| H4.3 | `sweagent/agent/models.py:578` | Adaptateur LiteLLM — **reprendre l'interface, pas la dépendance provider**. | **Adapter** |
| H4.3 | `sweagent/agent/history_processors.py:74,85` | Processeur par défaut **composable et sérialisable** ; fenêtre des dernières observations **à borne explicite**. | **Adapter** |
| H4.3 | `sweagent/agent/history_processors.py:179,215` | **Tagger les observations liées à un tool call pour préserver la causalité** ; fenêtre fermée supprimant l'historique le plus ancien **selon une règle testable**. | **Adapter** |
| H4.3 | `sweagent/agent/history_processors.py:261` | Cache-control attaché aux messages **sans modifier leur contenu métier**. | **Adapter** |
| H4.3 | `sweagent/agent/history_processors.py:305` | Suppression **par regex bornée et configurable** pour réduire le contexte. | **Adapter** |
| H4.3 | `sweagent/agent/history_processors.py:340` | Observations image traitées **séparément du texte**. | **Adapter** |


#### I — Langfuse · `resources/langfuse-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| I4.3 | `packages/shared/src/utils/prompts.ts:14` | **Interpolation de variables sans expressions** — remplacement de noms de clés, y compris avec un point, **sans résolution de propriété profonde**. Troisième source. | **Adapter** |
| I4.3 | `packages/shared/src/features/prompts/parsePromptDependencyTags.ts:18` | Référence par **nom et version ou label**, résolue avant l'appel, **versions concrètes tracées**. Le modèle ne choisit jamais une référence arbitraire. | **Adapter** |
| I4.3 | `worker/src/features/tokenisation/usage.ts:31` | **Tokenisation locale avec incertitude explicite** — usage fourni distinct de l'estimation de préflight. Les branches multi-provider ne qualifient pas Ling. | **Adapter** |
| I4.3 | `packages/shared/src/in-app-agent/server/toolErrors.ts:8` | **Une erreur d'outil se déduit d'un signal structuré, jamais d'une chaîne contenant « error ».** | **Adapter** |
| I4.3 | LF028 | **Déballage conservateur d'une réponse MCP** : un seul bloc textuel déballé, tableaux multimodaux et marqueur d'erreur préservés. | **Adapter** |


---

## Sources — reprises écartées ou reportées

**7 lignes. N'implémente aucune de ces lignes.** Le pointeur reste pour qu'un retournement de décision retrouve la source. Si tu penses qu'une raison est fausse, **écris-le dans `STATE.md`, n'implémente pas.**

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Statut |
|---|---|---|---|
| A4.3 | `openai_client.py:174-209` | `convert_openai_response_to_anthropic` — normalisation vers un format interne unique, `usage` et `stop_reason` compris. | **Écarté** |
| A4.3 | `openai_client.py:101-171` | `openai_stream_to_anthropic_events` — parsing SSE tolérant : ligne vide ignorée, JSON invalide sauté, `usage` capturé en fin. | **Écarté** |


#### C — Kilo Code · `resources/kilocode-main/`

| § | Source | Notion | Statut |
|---|---|---|---|
| C3.3 | `opencode/src/session/system.ts:46-88` · `kilocode/model-match.ts:1-6` | Sélection du prompt par famille de modèle, avec liste d'exclusions (`kling`, `bling`, `spelling`, `multilingual`). | **Écarté** |
| C3.3 | `opencode/src/provider/transform.ts:28-29,171-196` | Transformations par fournisseur isolées derrière une frontière unique. | **Écarté** |
| C3.3 | `opencode/src/provider/transform.ts:294-306,464-498` | Normalisation des messages et des blocs de contenu avant envoi. | **Écarté** |


#### D — Ouroboros · `resources/ouroboros-main/`

| § | Source | Notion | Statut |
|---|---|---|---|
| D3.4 | `our/local_model.py:618-700` | `test_tool_calling` — **sonde de capacité** d'un serveur local : chat de base, tool call réel, `tokens_per_sec` mesuré. Ne jamais supposer une capacité : la sonder. | **Écarté** |
| D3.4 | `our/capability_evidence.py:204-248` | `route_fingerprint` — credentials **exclus** de l'identité de route ; headers beta/routing inclus. | **Écarté** |

