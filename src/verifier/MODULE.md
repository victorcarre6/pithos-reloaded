# `verifier` — l'autorité de validation

> **Lis [`AGENTS.md`](../../AGENTS.md) avant de commencer.** Ce fichier est ton contrat complet : tu ne
> devrais pas avoir besoin d'ouvrir `docs/`. Ton point d'entrée exact est la rubrique « Prochaine action » de
> [`STATE.md`](STATE.md), à côté de ce fichier.
>
> **Tu ne commites, ne pousses et ne merges jamais.** Tes commits se *proposent* dans [`git.md`](git.md),
> avec les `ga`/`gcmsg` exacts — voir [`AGENTS.md`](../../AGENTS.md) § 7.

**Cible** : ~800 L au socle · ~950 L avec la gate hermétique · ratchet **shrink-only**
**Dépend de** : `kernel`, `journal`.
**Niveau de dépendance** : 2.
**Stack** : Hypothesis · `ast` stdlib · `subprocess` · Pydantic v2. **Ni pytest programmatique, ni `exec`.**

## 1. Autorité

`verifier` est l'autorité sur **la vérité**. C'est le module le plus important du projet et **son cœur
n'existe dans aucune des neuf sources** : `relations`, `domains` et `mutation` sont l'apport propre. Neuf
dépôts matures, dont deux avec un papier et un à 86,74 % sur Terminal-Bench, et **aucun n'a d'invariant
métamorphique, de mutation-check ni de catalogue fermé de relations.**

> **La règle qui définit ce module :**
> `verifier` n'a d'I/O que **sur ce qu'il a lui-même produit** — le script d'invariant qu'il vient d'écrire,
> le process qu'il vient de lancer.
> **L'état du monde lui arrive toujours comme fait typé.**

| Fait | Fourni par | Contenu |
|---|---|---|
| contenu avant / après de la cible | `workspace` | `FileFact` — empreintes, plage splicée, bilan chiffré |
| `git diff` et `git status` | `broker` | `RepoFact` — fichiers touchés, lignes ± |
| attestation d'hôte, horloge, ancre de démarrage | `lifecycle` | `HostFact` |
| artefact d'exécution de l'invariant | **lui-même** | script rendu, code de retour, sortie bornée |

Deux conséquences voulues : **le module le plus critique se teste intégralement avec des faits en dur**, et
il reste structurellement au-dessous de tout ce qui a des effets.

## 2. Interface publique

```python
# relations — les 9 relations fermées, chacune rend un script exécutable
class Relation(str, Enum):
    round_trip = "round_trip"          # f(g(x)) == x
    idempotent = "idempotent"          # f(f(x)) == f(x)
    commutes_with = "commutes_with"
    preserves = "preserves"
    invariant_under = "invariant_under"
    monotone = "monotone"
    total = "total"                    # ne lève jamais sur le domaine
    raises_on = "raises_on"
    schema_conform = "schema_conform"

def render(criterion: Criterion, target: Path) -> str:
    "Rend le script d'invariant exécutable. Squelette fixe, f-string — pas de moteur de template."

# domains — un dict FERMÉ enum -> stratégie Hypothesis. Le modèle ne touche jamais Hypothesis.
DOMAINS: dict[Domain, SearchStrategy]

# mutation — ~5 opérateurs ast.NodeTransformer maison
def mutants(source: str) -> Iterator[tuple[str, str]]: ...   # (nom de l'opérateur, source muté)
def kill_check(criterion: Criterion, source: str) -> KillReport: ...

# gates — la séquence d'acceptation, verdict typé
def run(criterion: Criterion, facts: list[Fact]) -> Verdict: ...

# receipt — verifier est le SEUL à en émettre un
def emit_receipt(node_id: str, attempt: int, facts: list[Fact], artifact: Path) -> Receipt | None:
    "Rend None si l'écriture durable a échoué — l'appelant doit alors bloquer le nœud."
```

## 3. Interdits

- **N'importe jamais `bridge`, ni aucun client de modèle.** C'est la première règle d'import du projet.
- **N'importe jamais `engine`, `campaign`, `workspace`, `broker` ni `lifecycle`.** Il reçoit des faits, il
  ne va pas les chercher.
- **N'ouvre aucun fichier du workspace. N'appelle jamais `git`.**
- **N'émet aucun jugement scalaire.** Pas de score de confiance, pas de moyenne pondérée. La décision 23 dit
  que le résultat est un **produit d'axes**, pas un statut — et un score de confiance est un jury, pas une
  vérification.

## 4. La double gate — le cœur du projet

Un invariant est accepté **si et seulement si** les deux passent :

```text
1. rouge-avant   l'invariant échoue AVANT l'implémentation, et passe après
2. mutation-check  l'invariant échoue sur au moins un mutant AST de la cible
```

⚠️ **La seconde est celle que personne n'a** !
→ Un invariant qui survit à **toutes** les mutations de l'implémentation est **tautologique** — il ne teste
rien — et il est rejeté. C'est la garde qui rend fiable une autorité de validation produite par un modèle
faible.

**Le modèle n'émet jamais de valeur.** Il émet `{relation, symbols, domain}` : un choix dans une
énumération fermée plus des noms de symboles que `codeview` a vérifiés. **Le harness génère les entrées** via
Hypothesis. C'est la correction directe de la cause d'échec n°1 de v1, mesurée sur six micro-rushes.

**Exécution** : fichier rendu + `subprocess`. Isolation totale, timeout trivial, et **le script rendu est un
artefact relisible après coup** — ce que la décision 13 exige. Pas de pytest programmatique, pas d'`exec`.

**Hypothesis pour le shrinking**, et c'est la raison qui tranche : quand un invariant casse, Hypothesis rend
le contre-exemple **minimal**, qui part directement dans le feedback au modèle. v1 renvoyait « 6 lignes
significatives » de sortie pytest brute à un 8B.

## 5. Contenu

| Fichier | Contenu | ~L |
|---|---|---:|
| `relations.py` | les 9 relations, chacune rendant un script exécutable | 250 |
| `domains.py` | dict fermé enum → stratégie Hypothesis | 100 |
| `mutation.py` | ~5 opérateurs `ast.NodeTransformer` + `kill_check` | 200 |
| `gates.py` | séquence d'acceptation, exécution subprocess, verdict typé | 150 |
| `receipt.py` | émission du reçu, identité typée | 100 |

**La gate hermétique** — worktree jetable, scrub d'environnement, sonde à nonce, vérification des plugins
avant que le code candidat soit sur disque — est **conditionnée au spike n°5** : si assembler un worktree
coûte de l'ordre de la seconde, elle tourne à chaque mission ; si c'est de l'ordre de la dizaine de
secondes, elle est réservée à la fin de mission. **Ne l'écris pas avant que le spike ait tranché.**

## 6. Critères de socle que ce module rend verts

- **Un invariant qui survit à toutes les mutations de l'implémentation est rejeté comme tautologique.**
- **Un invariant doit être rouge avant l'implémentation et vert après, sinon il est rejeté.**
- **Un nœud dont la cible n'a pas effectivement changé ne peut pas être compté vert** — preuve par
  comparaison au contenu antérieur croisée avec `git diff`, et artefact d'exécution littéral pour toute
  validation. **Écrire n'échoue jamais ; compter vert exige le reçu effectivement écrit.**
- **Toute identité d'enregistrement est une clé typée, jamais une chaîne de repli** (décision 22).
- Contribue à : *aucun littéral émis par le modèle ne traverse la frontière modèle → exécution.*

## 7. Le double

`tests/doubles/verifier.py` — rend un `Verdict` déterministe piloté par une table `{criterion → verdict}`
fournie au constructeur. **`engine` s'en sert pour tester le marcheur sans jamais exécuter un subprocess.**

Le double doit savoir rendre : un vert, un rouge avec contre-exemple minimal, un rejet pour tautologie, et un
**reçu absent** (`emit_receipt` → `None`) — ce dernier cas est celui qui teste le chemin
`receipt_not_written`.

## 8. Fini quand

- [ ] Les 9 relations rendent un script qui s'exécute, avec un test par relation.
- [ ] Le script rendu est **écrit sur disque et conservé** comme artefact, chemin porté par le reçu.
- [ ] Un invariant tautologique — vrai pour toute implémentation — est **rejeté**, test explicite.
- [ ] Un invariant vert avant implémentation est **rejeté**, test explicite.
- [ ] `kill_check` tue au moins un mutant sur une implémentation correcte, et zéro sur une tautologie.
- [ ] Les ~5 opérateurs de mutation produisent du code **parsable** — un mutant qui ne compile pas est un
      défaut de l'opérateur, pas un kill.
- [ ] Le contre-exemple rendu au modèle est le **minimal** d'Hypothesis, borné tête + queue.
- [ ] `exit 127` est classé **panne d'outillage**, pas test rouge. `cmp` où `>1` signifie panne aussi.
- [ ] Aucune coercition `or` sur un code de retour — test avec `returncode=None`.
- [ ] `emit_receipt` rend `None` quand `journal.emit` rend `False`, et l'appelant bloque.
- [ ] `tests/boundaries/` confirme : aucun import de `bridge`, `engine`, `workspace`, `broker`, `lifecycle`.
- [ ] Un test vérifie qu'aucune fonction du module n'ouvre un fichier du workspace ni ne lance `git`.

## 9. Pièges connus, et ce qui a été écarté

**Écarté — ne réintroduis pas.** Les raisons sont dans `docs/EXPLANATIONS.md` § décision 13 amendée.

| Écarté | Pourquoi |
|---|---|
| **Les trois capteurs de faux-vert** (~250 L) | ils supposent un modèle qui compose ses commandes shell et écrit ses assertions ; **le script d'invariant est rendu par le harness** |
| **Le catalogue de douze parsers** (~200 L) | il existe pour des backends sans sortie structurée ; une sortie non conforme est **rejetée, jamais récupérée** |
| **La planification de gate par coût** (~150 L) | `format → lint → typecheck → test` alors que la stack n'a **ni linter ni typechecker** |
| **L'admission déclarative** (17 lignes) | valider une proposition n'est pas vérifier un invariant : mécanisme dans `kernel`, règles dans `campaign` |
| **Le score de confiance et la réconciliation de findings** | un scalaire borné `[0.05, 0.95]` est un jury, pas une vérification |

**Gardés malgré la coupe**, parce qu'ils ne dépendent d'aucun modèle de menace : aucune coercition `or` sur
un code de retour, `cmp` où `>1` signifie panne d'outillage, `compact_failure_output` (tête + queue borné),
`summarize_validation_failure` (classe d'échec + lignes d'erreur pertinentes), `_is_launch_failure`,
normalisation de commande en `[sys.executable, "-m", …]`.

---

## Sources — reprises retenues

**147 lignes.** Chaque pointeur se lit dans `resources/`. Le détail complet et le contexte de chaque partie sont dans [`resources/IMPORT_REPORT.md`](../../resources/IMPORT_REPORT.md).
**Lis la source avant de porter.** Une reprise collée sans être relue est un défaut.

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| A4.2 | `validation_loop.py:282-299` | `summarize_validation_failure` → `failure_class`, `relevant_error_lines`, `recommended_repair_scope`. **C'est le feedback rendu au modèle**, pas du stdout brut. | **Copier** |
| A4.2 | `validation_loop.py:302-329` | `run_validation` — sortie au **premier échec**, callback avant/après chaque étape, durée en `monotonic`. | **Copier** |
| A4.2 | `planning.py:403-411` | `compact_failure_output` — tête + `...` + queue, borné en lignes et caractères. | **Copier** |
| A4.2 | `benchmark/verifier.py:15-29` | `_normalize_verification_command` — réécrit `pytest ...` en `[sys.executable, "-m", "pytest", ...]`. **v1 a payé exactement ce bug.** | **Copier** |
| A4.2 | `benchmark/verifier.py:32-36` | `_is_launch_failure` — exit 127/9009 + « not found » ⇒ **la commande n'existe pas**, ce n'est pas un contrat rouge. | **Copier** |
| A4.2 | `benchmark/verifier.py:39-137` | `run_commands` — chaque exécution archive `stdout`, `stderr` et un `meta.json`. Notre script d'invariant rendu produit le même triplet. | **Copier** |
| A4.2 | `autonomy.py:62-246` | `VerificationEngine` — vérificateur **adversarial** post-changement, indépendant des tests. | **Adapter** |
| A4.2 | `autonomy.py:99-126` | `before_contents` vs contenu courant croisé avec `git diff --name-only` ⇒ finding « no effective change ». Pilier de la décision 13. | **Copier** |
| A4.2 | `autonomy.py:169-188` | Finding `SUSPICIOUS_BREADTH` si `git diff --stat` dépasse 8 fichiers. | **Adapter** |
| A4.2 | `autonomy.py:203-210` | Empreinte des findings ⇒ `repeated_verification_state`. **Détecte la boucle stérile par la répétition à l'identique du diagnostic.** | **Copier** |
| A4.2 | `autonomy.py:261-302` | `_reconcile_findings` — un finding contredit par une preuve directe est retiré, **et le retrait est journalisé**. | **Copier** |
| A4.2 | `autonomy.py:17-27` | `FindingCategory` — taxonomie fermée de huit catégories de défauts. | **Copier** |
| A4.2 | `autonomy.py:311-324` | `FailureCategory` — 13 causes fermées, dont `REPEATED_NO_PROGRESS` et `EXCESSIVE_BLAST_RADIUS`. | **Copier** |
| A4.2 | `autonomy.py:337-387` | `FailureClassifier` — classe par mots-clés **et compte les occurrences** : trois échecs de même catégorie forcent un changement de stratégie. | **Copier** |
| A4.2 | `autonomous_helpers.py:88-120` | `meets_contract` / `has_real_validation_artifact` — un artefact doit contenir littéralement `(exit=0)`. Pilier de la décision 13. | **Copier** |


#### B — Pi · `resources/pi-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| B3.2 | `packages/agent/src/harness/execution/tools.ts:78` | Séparer préparation, admission, exécution, finalisation. La validation d'arguments Pi ne prouve **aucune** relation métamorphique. | **Adapter** |
| B3.2 | `packages/coding-agent/src/core/tools/bash.ts:25` | Refuser les délais invalides avant de créer un processus : zéro, négatif, infini, dépassement du budget restant. | **Adapter** |
| B3.2 | `packages/coding-agent/src/utils/child-process.ts:49` | **Fin de processus ≠ fin de ses sorties.** Délai d'inactivité ET deadline absolue ; ne pas attendre indéfiniment le close d'un pipe. | **Adapter** |
| B3.2 | `packages/agent/src/harness/utils/output-capture.ts:26` | Vue bornée avec métadonnées de troncature : exit_code, cause, totaux, extrait, chemin de l'artefact complet. **L'extrait n'est jamais la preuve.** | **Adapter** |
| B3.2 | `packages/evals/src/pi-harness.ts:212` | Préserver l'échec initial quand le nettoyage échoue aussi. Pas de suppression du workspace avant sauvegarde des preuves. | **Adapter** |
| B3.2 | `packages/agent/src/harness/session/testing/conformance/storage.ts:134` | Suite de conformité commune : mêmes contrats testés sur un fake et un répertoire réel, sans interface multi-backends en production. | **Adapter** |
| B3.2 | `packages/agent/src/harness/session/testing/gating-storage.ts:26` | Injection déterministe d'un crash entre admission et persistance. **Éviter les tests de race fondés sur `sleep`.** | **Adapter** |
| B3.2 | `packages/agent/src/harness/session/testing/instrumented-storage.ts:6` | Observer les tentatives de commit, pas seulement l'état final. Vérifier qu'une entrée invalide n'a tenté aucune écriture. | **Adapter** |
| B3.2 | `packages/agent/test/harness/jsonl-storage.test.ts:278` | Corpus de fins tronquées et lignes invalides, **en inversant l'attendu de la réparation Pi**. Ajouter coupure UTF-8, disque plein, échec de rename/fsync. | **Adapter** |
| B3.2 | `packages/agent/test/harness/runtime/drive-reconcile.test.ts:450` | **Matrice de reprise couvrant chaque état durable** : couper avant/après chaque effet, relancer sans conversation. | **Adapter** |
| B3.2 | `packages/agent/test/harness/runtime/drive-tools.test.ts:421` | Distinguer effet rejouable et effet de résultat inconnu. Pilier de la décision 16. | **Adapter** |
| B3.2 | `packages/ai/src/providers/faux.ts:144` | Provider scénarisé sans réseau. Fixer ids/horloge/découpage : **le faux de Pi utilise du hasard par défaut**, il n'est pas déterministe. | **Adapter** |
| B3.2 | `packages/coding-agent/test/suite/harness.ts:34` | Harness de scénario isolé de la configuration utilisateur. Tester que les credentials machine ne sont pas chargés. | **Adapter** |
| B3.2 | `packages/protocol/test/framing.test.ts:14` | Fragmentation arbitraire des flux : mêmes octets en un bloc, octet par octet, coupés au milieu d'un caractère. Résultat identique. | **Adapter** |
| B3.2 | `packages/chord/test/delta.test.ts:19` | Formes de tests pour utilitaires purs : rejeu et immuabilité. **Ne pas injecter leurs valeurs attendues dans les `Criterion` proposés par le modèle.** | **Adapter** |
| B3.2 | `packages/telemetry/src/testing/conformance.ts:61` | Fermeture d'un span exactement une fois, conservation du résultat, indépendance des snapshots. | **Adapter** |
| B3.2 | S | Séparer tests hors ligne et intégrations avec modèle réel. Sélection pytest explicite sans endpoint ni credentials ambiants. | **Adapter** |


#### C — Kilo Code · `resources/kilocode-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| C3.2 | `opencode/src/lsp/diagnostic.ts:3-28` | `report()` — **seules les erreurs (`severity === 1`) sont montrées au modèle**, plafonnées à `MAX_PER_FILE = 20`, suivies de `... and N more`, dans un bloc `<diagnostics file="...">`. Les avertissements sont du bruit pour un 8B ; la troncature est visible. **Format cible de notre rendu d'échec d'invariant.** | **Traduire** |
| C3.2 | `opencode/src/tool/truncate.ts:87-149` | Au-delà des plafonds, **le texte intégral est écrit dans un fichier** et l'aperçu porte son chemin plus l'instruction pour le récupérer. Rien n'est jamais détruit. | **Traduire** |
| C3.2 | `opencode/src/tool/truncate.ts:14-15` | `MAX_LINES = 2000` **et** `MAX_BYTES = 50 KB` : deux plafonds appliqués, et le message dit **lequel** a été atteint. | **Traduire** |
| C3.2 | `opencode/src/tool/truncate.ts:131-137` | L'instruction de récupération **s'adapte à ce que l'appelant peut faire**. | **Inspirer** |
| C3.2 | `opencode/src/tool/truncate.ts:12,53-66` | Rétention 7 jours purgée **par mtime** sur une boucle horaire forkée dont l'échec est journalisé, jamais propagé. | **Traduire** |
| C3.2 | `opencode/src/git/index.ts:6-18` | **Chaque invocation de git reçoit un prélude fixe** : `--no-optional-locks`, `core.autocrlf=false`, `core.fsmonitor=false`, `core.longpaths=true`, `core.quotepath=false`. Rend git déterministe quelle que soit la config utilisateur. | **Traduire** |
| C3.2 | `opencode/src/git/index.ts:22-30` | `fail(err)` — un échec de *spawn* normalisé en `{exitCode: 1, stderr}`. **Les appelants n'ont jamais deux formes d'erreur.** | **Traduire** |
| C3.2 | `opencode/src/git/index.ts:64-70,128` | `maxOutputBytes` par exécution, `truncated` porté dans le résultat. **Le lanceur de processus borne, l'appelant sait.** | **Traduire** |
| C3.2 | `opencode/src/git/index.ts:80-101` | `kind(code)` — code porcelain → `added`/`deleted`/`modified`, avec `??` et `U` traités explicitement. | **Traduire** |
| C3.2 | `opencode/src/format/index.ts:44-52,74-119` | Formatteurs déclarés par extension avec détection de disponibilité, exécutés après édition ; échec journalisé, jamais fatal. | **Adapter** |
| C3.2 | `http-recorder/src/matching.ts:73-106` | Appariement de requêtes enregistrées : méthode, URL normalisée, corps canonicalisé. Base d'un faux bridge rejouable. | **Adapter** |
| C3.2 | `http-recorder/src/cassette.ts:17-51` | Cassettes versionnées avec rédaction des secrets à l'enregistrement. | **Adapter** |
| C3.2 | `verifier` | Paquet entier : cassettes HTTP + WebSocket, appariement, rédaction, versionnement. Modèle pour rejouer une campagne sans Ollama. | **Adapter** |
| C3.2 | `opencode/src/session/retry.ts:35-176` | Classification d'erreur séparée de la politique, backoff borné, annulation propagée. Convergent avec `pi/retry.ts:163,224`. | **Traduire** |


#### D — Ouroboros · `resources/ouroboros-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| D3.3 | `our/tools/verify.py:553-850` | `verify_and_record` — l'hôte exécute **et** atteste dans le même appel. Le reçu porte `status`, `returncode`, `matched`, `check`, `check_rendering`, `summary`, `duration_ms`, `signal`. | **Copier** |
| D3.3 | `our/tools/verify.py:68-75` | `_CONTRACT_KINDS` — six kinds fermés, dont l'échappatoire honnête `no_visible_machine_contract` et la décision `delegation_zero_run`, structurellement non-probante. | **Inspirer** |
| D3.3 | `our/tools/verify.py:59-66` | `_receipt_custody_failure` — **un reçu non écrit retire l'attestation.** | **Copier** |
| D3.3 | `our/tools/verify.py:85-110` | `_EXPECTED_MATCH_KINDS` — `substring` / `exact` / `exact_line` / `json_equals` / `bytes_equal`. Le mode de comparaison est une énumération fermée, pas une convention. | **Copier** |
| D3.3 | `our/tools/verify.py:282-366` | `bytes_equal` — comparaison octet à octet avec **hexdump borné autour de la première divergence**. Forme « golden file » qu'un `substring` sous-vérifie silencieusement. | **Adapter** |
| D3.3 | `our/tools/verify.py:322-330` | `cmp` sort 0=égal, 1=différent, **>1 = panne d'outillage**. Généralisation de `_is_launch_failure` de Villani. | **Copier** |
| D3.3 | `our/tools/verify.py:311-321` | **Aucune coercition `or` sur un code de retour** : `None or 0` lisait un résultat inconnu comme un succès. | **Copier** |
| D3.3 | `our/tools/verify.py:44-49` | Deux bornes distinctes : `_RECEIPT_OUTPUT_CAP = 20000` (preuve durable) et `_TOOL_OUTPUT_CAP = 4000` (transport vers le modèle). **La preuve n'est pas bornée par le budget de contexte.** | **Copier** |
| D3.3 | `our/_outcome_receipts.py:154-215` | `ReceiptIdentity` — trois composants **indépendants**, dérivés **une fois**, puis utilisés pour comparaison, hash, comptage et projection. Trois notions subtilement différentes ne peuvent plus diverger. | **Copier** |
| D3.3 | `our/_outcome_receipts.py:216-266` | **Une** clé typée `(kind, value)`. *A chain is not an equivalence relation.* | **Copier** |
| D3.3 | `our/_outcome_receipts.py:273-287` | `IDENTITY_KINDS` — table fermée **totale**, y compris pour le kind « aucune identité ». Un quatrième kind ajouté sans sa ligne lève `KeyError` : la gate qui fonctionne. | **Copier** |
| D3.3 | `our/_outcome_receipts.py:50-64` | `check_rendering` — le **rendu** fait partie de l'identité. Un rendu inconnu est son propre espace de noms, donc sûr sans changement de code. | **Copier** |
| D3.3 | `our/_outcome_receipts.py:131-152` | `canonical_path_set` — dédup + tri, **verbatim sinon**. Canonicaliser → rendre → borner, jamais l'inverse. | **Copier** |
| D3.3 | `our/_outcome_receipts.py:395-460` | Un reçu **sans clé** garde la règle ancienne ; deux reçus sans clé ne sont **jamais** égaux, même entre eux. *Indiscernables n'est pas connu-égal.* | **Copier** |
| D3.3 | `our/_outcome_receipts.py:344-394` | Décideur et rapporteur lisent **la même projection**. Une preuve qui décrit faussement sa propre base est le défaut que la surface existe pour éliminer. | **Copier** |
| D3.3 | `our/_outcome_receipts.py:687-806` | `_outstanding` / `unreconciled_failed` — l'ensemble des vérifications **encore ouvertes**, calculé une fois. C'est notre « nœud qui ne peut pas se déclarer vert ». | **Copier** |
| D3.3 | `our/preflight_runner.py:1189-1330` | `run_hermetic_pytest` — **worktree git jetable**, candidat = capture `--binary` durcie + copie des non-suivis, budget partagé, sortie au premier rouge. | **Copier** |
| D3.3 | `our/preflight_runner.py:414-447` | `_apply_diff` — `-c core.autocrlf=false -c core.eol=lf`, `--binary`, `--unidiff-zero`. Une capture fidèle aux octets doit atterrir sur un checkout qui l'est aussi. | **Copier** |
| D3.3 | `our/preflight_runner.py:448-480` | `_copy_untracked` — `os.fsdecode` (surrogateescape), confinement `relative_to` des deux côtés. Un nom non-UTF-8 ne disparaît pas en silence. | **Copier** |
| D3.3 | `our/preflight_runner.py:576-625` | `_preflight_env` — scrub des variables du harness, secrets, `GH_*` et **tout `PYTEST_*`**, puis ré-injection contrôlée. **Un vert sous une variable héritée est indiscernable d'un vrai vert.** | **Copier** |
| D3.3 | `our/preflight_runner.py:500-575` | Sonde à **nonce** : *« the difference between "the argv said -n" and "concurrency actually happened" »*. Une gate qui ne peut pas prouver son mode ne l'annonce pas. | **Inspirer** |
| D3.3 | `our/preflight_runner.py:626-748` | Vérification des plugins requis **avant** que le moindre code candidat soit sur le disque, avec remédiation nommée. | **Adapter** |
| D3.3 | `our/preflight_runner.py:389-412` | `_head_tracks_tests` — distingue « pas de suite » de « ce candidat a supprimé la suite ». Une ref illisible **bloque**. | **Copier** |
| D3.3 | `our/preflight_runner.py:1234-1242` | Un budget de rendu non positif **refuse de lancer la gate** : un diagnostic non rendu se lit comme un succès. | **Copier** |
| D3.3 | `our/preflight_runner.py:99-103,142-176` | Séquences ANSI retirées avant tout matching ; motifs de crash **ancrés en début de ligne nettoyée** — un test dont l'assertion *mentionne* un crash recevait une remédiation confiante et fausse. | **Copier** |
| D3.3 | `our/commit_admission.py:30-228` | Préflights déterministes d'admission au commit : compilation des `.py` stagés, synchronisation des métadonnées de version, tests avec preuve. | **Adapter** |
| D3.3 | `our/mutation_attribution.py:447-525` | `attributed_git_candidates` — candidats = changés **moins** sales-au-baseline ; blockers typés `baseline_missing` / `baseline_stale` / `baseline_surface_ambiguous` / `baseline_dirty_overflow`. | **Copier** |
| D3.3 | `our/mutation_attribution.py:335-426` | `clean_eligible = not blockers`. **La preuve est une liste de raisons, et son absence est un fait, pas un verdict.** | **Copier** |
| D3.3 | `our/mutation_attribution.py:676-800` | **Époques de baseline** : ré-ancrage strict (ancêtre de HEAD **et** intervalle disjoint des chemins sales). Sans ça, `baseline_stale` coince toutes les missions après le premier commit. | **Copier** |
| D3.3 | `our/mutation_attribution.py:85-108` | `--porcelain=v1 -z --untracked-files=all` avec **les deux côtés** d'un rename. Une ligne malformée lève, elle n'est pas ignorée. | **Copier** |
| D3.3 | `our/mutation_attribution.py:126-158` | `_path_fingerprint` — empreinte d'**un chemin connu exact**, sans jamais parcourir un parent ; `kind ∈ {missing, symlink, file, directory, other}`. | **Copier** |
| D3.3 | `our/mutation_attribution.py:31-35,213-220` | Un worktree poubelle rend le baseline **honnêtement inutilisable** (`dirty_overflow`) plutôt que coûteusement approximatif. | **Copier** |
| D3.3 | `our/review_evidence.py:17-66` | **Indépendance de la preuve** : quels fichiers de vérification l'agent a lui-même écrits. Étiqueté honnêtement « état du worktree » faute de baseline. | **Copier** |
| D3.3 | `our/review_evidence.py:66-80` | **Parité de preuve** : la borne du décideur suit celle de l'acteur. *Un juge affamé produit des verdicts « non montré », donc des boucles.* | **Copier** |
| D3.3 | `our/review_evidence.py:83-105` | Deux formes d'« ouvert » : jamais répondu, et **répondu par l'agent mais non tranché**. Une réfutation déposée est une prétention, pas un règlement. | **Copier** |
| D3.3 | `our/outcomes.py:430-470` | Deux signaux structurels distincts : `receipt_absent` (effets réels, aucune attestation) et `expected_output_ungrounded` (livrable déclaré, zéro tool call). | **Adapter** |


#### E — Prime Agent · `resources/prime-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| E3.2 | `ca/core/autonomous.ts:284-348` | `runAutonomousQualityGates` — les gates tournent **avant que la session ait le droit de se terminer**, dans l'ordre déclaré, sortie au premier rouge. | **Adapter** |
| E3.2 | `ca/core/autonomous.ts:294-311` | **Ne pas relancer une gate si l'arbre de travail n'a pas bougé.** Le compteur de tentative avance, le message dit pourquoi. **Ferme les six heures de boucle stérile de v1, à coût nul.** | **Adapter** |
| E3.2 | `ca/core/autonomous.ts:374-423` | Empreinte d'arbre = `status --porcelain=v1 -z -uall --no-renames` + `diff --binary HEAD` + hash des non-suivis, avec **pathspec d'exclusion des artefacts**. | **Adapter** |
| E3.2 | `ca/core/autonomous.ts:402-417` | **Un snapshot partiel est un non-snapshot** : sortie tronquée, timeout ou exit non nul ⇒ pas d'empreinte, donc pas d'égalité, donc la gate est relancée. Le repli est sûr. | **Traduire** |
| E3.2 | `ca/core/autonomous.ts:446-469` | Un lien symbolique est hashé **par sa cible**, un non-fichier par `mode:size:mtime`, une erreur devient `error:<message>` **dans le hash** au lieu d'être avalée. | **Adapter** |
| E3.2 | `ca/core/autonomous.ts:350-360` | Le feedback rendu au modèle porte **commande, tentative sur maximum, sortie bornée, horodatage ISO**. | **Adapter** |
| E3.2 | `ca/core/autonomous.ts:581-586` | `outputAlreadyTruncated` propagé depuis le sous-processus : on n'annonce pas « tronqué » deux fois pour la même sortie. | **Traduire** |
| E3.2 | `ca/core/autonomous.ts:80,88-91` | `AutonomousDecision.reason` = `missing_terminal_evidence` / `gate_failed` / `not_needed` / `limit_reached`. **La décision porte sa raison**, pas un booléen. | **Traduire** |
| E3.2 | `ca/core/autonomous.ts:186-194` | **Les tokens de lecture de cache ne comptent pas dans le budget** : les compter cumulativement épuise le budget bien avant que le travail soit fait. | **Traduire** |
| E3.2 | `ca/core/refinement/refinement.ts:673-714` | `validateEdit` — validation **par cas fermés**, chaque refus renvoyant sa phrase. | **Adapter** |


#### F — Unsloth · `resources/unsloth-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| F3.2 | `tests/test_torchao_nf4tensor_move.py:191` | **Tester l'absence d'import eager d'une dépendance optionnelle.** Applicable à nos frontières d'import : le test de graphe de la décision 22 y trouve son complément. | **Adapter** |
| F3.2 | `tests/test_torchao_nf4tensor_move.py:152` · `tests/test_peft_symbol_backfill.py:96` | **Idempotence des correctifs et des patches d'initialisation** : un mécanisme de compatibilité exécuté deux fois ne modifie plus l'état. | **Adapter** |
| F3.2 | `tests/test_peft_symbol_backfill.py:136` | Annoncer explicitement une fonction de mapping manquante, **avec une catégorie de panne exploitable**. | **Adapter** |
| F3.2 | `tests/test_deliberate_crashes_suppress_cores.py:140` | Éviter les introspections AST coûteuses dans les chemins de test ; **borner les diagnostics**. | **Adapter** |
| F3.2 | `unsloth/models/loader_utils.py:1522` | Refuser une combinaison incompatible **avant exécution**, plutôt que laisser le backend échouer tard. | **Adapter** |
| F3.2 | `unsloth/models/loader_utils.py:180` | **Normaliser les kwargs pour que deux configurations sémantiquement égales aient la même empreinte.** Directement applicable à notre clé de redondance (décision 22). | **Adapter** |
| F3.2 | `unsloth/models/loader_utils.py:326` | Résolution avec **repli explicite et raison** — utile pour expliquer un `blocked`. | **Adapter** |
| F3.2 | `unsloth/models/rl.py:973,987` | **Empreinte d'un dataset borné, invalidée dès qu'une mutation change le contenu** ; token de mutation pour invalider un cache entre deux cycles. Même mécanisme que notre satisfaction périmée. | **Adapter** |
| F3.2 | `unsloth/models/rl.py:906,1005` | Contrôler une limite **après matérialisation** et vérifier que la borne tient **au moment de l'usage**, pas seulement à la déclaration. | **Adapter** |
| F3.2 | `unsloth/models/rl_replacements.py:526` | Remplacements regex de fonctions tierces : **trop fragiles**. Conserver l'idée d'un patch versionné, pas le mécanisme. | **Adapter** |


#### G — OpenHands · `resources/OpenHands-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| G3.2 | `src/manifests/manifest-validation.ts:25` | **Identifiants validés par regex avant insertion au registre.** | **Adapter** |
| G3.2 | S | **Markup interdit** dans tout texte fourni par une extension. | **Adapter** |
| G3.2 | S | **Commandes déclaratives restreintes à un alphabet sans métacaractères shell** ; toute syntaxe shell refusée. Complément du capteur de masquage d'exit d'Ouroboros. | **Adapter** |
| G3.2 | S | **Chemins de source restreints à des préfixes autorisés.** | **Adapter** |
| G3.2 | S | Modes de setup et types de champ **énumérés explicitement**. | **Adapter** |
| G3.2 | S | **Borne dure de longueur** pour tout message rendu au contexte. | **Adapter** |
| G3.2 | S | **Accumulateur d'erreurs avec chemin de champ : toutes les violations retournées en une fois.** | **Adapter** |
| G3.2 | S | Chemin vérifié **relatif et sans échappement** du workspace. | **Adapter** |
| G3.2 | S | Champ obligatoire imposé pour les déclencheurs qui en ont besoin. | **Adapter** |
| G3.2 | S | Vérification d'un bundle **avant empaquetage** ; détection rapide d'un bloc de setup admissible. | **Adapter** |
| G3.2 | S | **Fonction publique unique de validation**, renvoyant `{valid, errors}`. | **Adapter** |
| G3.2 | A | Contraintes validées **séparément** du schéma de présentation ; unicité et forme des champs de formulaire. | **Adapter** |
| G3.2 | `src/manifests/interface-validation.ts:103` | **Même patron d'admission** pour une seconde famille de manifests — la règle est réutilisée, pas réécrite. | **Adapter** |
| G3.2 | `src/manifests/interface-validation.ts:709` | Valider une interface complète **avant de l'exposer** à l'observatory. | **Adapter** |
| G3.2 | `src/manifests/manifest-local-validation.ts:24` | **Caractères dangereux interdits** dans les expressions de formulaire locales. | **Adapter** |
| G3.2 | `src/manifests/manifest-local-validation.ts:167` | **Gate locale rapide avant tout appel réseau** ou création de job. | **Adapter** |
| G3.2 | `src/manifests/manifest-error-map.ts:75,127` | Normaliser les erreurs distantes vers **les chemins de champs du contrat local**, pour les rendre exploitables par le modèle. | **Adapter** |


#### H — SWE-agent · `resources/SWE-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| H4.2 | `sweagent/tools/parsing.py:52` | `AbstractParseFunction` — interface séparant **texte modèle, action et erreur de parsing**. | **Adapter** |
| H4.2 | `sweagent/tools/parsing.py:72,97` | `ActionParser` et **`ActionOnlyParser`** — le second pour quand **aucune pensée libre ne doit atteindre l'exécution**. *(l'extraction attribuait « action-only » à `:72`)* | **Adapter** |
| H4.2 | `sweagent/tools/parsing.py:109,168` | `ThoughtActionParser` et sa **variante XML**, pour un backend sans tool calling natif. | **Adapter** |
| H4.2 | `sweagent/tools/parsing.py:225` | `XMLFunctionCallingParser` — function calling **exprimé en XML**. *(l'extraction le décrivait comme le parser FC générique)* | **Adapter** |
| H4.2 | `sweagent/tools/parsing.py:371` | `FunctionCallingParser` — **rejette les appels de fonction inconnus**. *(l'extraction annonçait « table de fonctions autorisées »)* | **Adapter** |
| H4.2 | `sweagent/tools/parsing.py:457` | `JsonParser` — **erreurs localisées** plutôt que stdout brut. | **Adapter** |
| H4.2 | `sweagent/tools/parsing.py:543,574` | `BashCodeBlockParser` et **`SingleBashCodeBlockParser`**, borné à un bloc unique. *(l'extraction attribuait « unique » à `:543`)* | **Adapter** |
| H4.2 | `sweagent/tools/parsing.py:324,354` *(hors extraction)* | `EditFormat` (spécialisation de `ThoughtActionParser`) et `Identity` — **le parser identité est nommé**, pas implicite. | **Adapter** |
| H4.2 | `sweagent/tools/commands.py:33,79` | Clés attendues d'un format de commande **extraites avant rendu** ; commande déclarative à **arguments typés et description générée**. | **Adapter** |
| H4.2 | `sweagent/tools/tools.py:29,227` | **Blocklist et allowlist au niveau configuration** ; handler unique qui filtre, exécute et **normalise** le résultat. | **Adapter** |
| H4.2 | `sweagent/tools/utils.py:8,75` | Garde contre les **entrées multi-lignes ambiguës** ; documentation générée depuis les signatures, sans duplication manuelle. | **Adapter** |
| H4.2 | `sweagent/agent/agents.py:199` | **Exceptions internes distinctes** : action bloquée, retry, forfeit, timeout global. Quatre causes, quatre types. | **Adapter** |
| H4.2 | `sweagent/agent/agents.py:443` | `DefaultAgent` dont `forward` **sépare appel modèle et exécution d'action**. | **Adapter** |
| H4.2 | `sweagent/agent/reviewer.py:30,559` | Modèle de soumission et résultat de revue **séparés du résultat d'exécution** ; boucle de scoring **à retry borné** quand le reviewer produit une sortie invalide. | **Adapter** |
| H4.2 | `tools/windowed/lib/flake8_utils.py:26,92` *(hors extraction)* | `Flake8Error` typée et `format_flake8_output` — et surtout `_update_previous_errors` (`:59`) qui **relocalise les erreurs de lint après une édition**, les numéros de ligne ayant bougé. | **Adapter** |


#### I — Langfuse · `resources/langfuse-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| I4.2 | `packages/shared/src/server/evals/codeEvalDispatcherTypes.ts:139` | **Frontière explicite entre orchestration et exécuteur** — contrat entrée / résultat / erreur. Remplacer `code.source` par une relation admise. | **Adapter** |
| I4.2 | LF012 | Contexte d'exécution typé et borné : scope, runtime, identité, payload. **Caps en octets à la vraie frontière d'exécution.** | **Adapter** |
| I4.2 | LF013 | **Résultat structuré non vide** — un booléen ou un score numérique ne constitue pas à lui seul un verdict. | **Adapter** |
| I4.2 | LF014 | **Taxonomie d'erreurs de l'exécuteur** : source invalide, timeout, erreur du code, réponse invalide. **Les retries se déterminent depuis la cause.** | **Adapter** |
| I4.2 | `worker/src/features/evaluation/evalExecutionDeps.ts:128` | Dépendances injectables — horloge, stockage, lancement de processus. **Ne pas mettre `callLLM` dans le même objet que le verifier.** | **Adapter** |
| I4.2 | `worker/src/features/evaluation/evalCompletion.ts:23` | **Publier la preuve avant la transition terminale.** Décision 13 amendée. | **Adapter** |
| I4.2 | LF017 | Exécution reliée à **une version et à sa trace** : protocole, relation, empreinte de code, entrée. | **Adapter** |
| I4.2 | `packages/shared/src/server/evals/codeEvalExecution.ts:363` | **Contre-exemple** : un `catch` qui journalise l'échec de trace et continue. Acceptable en télémétrie, **inacceptable pour la preuve primaire**. | **Adapter** |
| I4.2 | `packages/shared/src/utils/jsonSchemaValidation.ts:58` | **Schéma compilé réutilisé pour un lot**, erreurs avec `path` / `message` / `keyword`. | **Adapter** |
| I4.2 | LF020 · **X** | **Contre-exemple direct de la décision 28** : cette configuration ne renvoie que **la première erreur** et désactive la validation des formats. | **Adapter** |
| I4.2 | `scripts/code-eval-runners/python/code_based_eval_handler.py:188` | Diagnostic Python **avec type et ligne du code exécuté**, en plus de stderr brut. Petit port utile pour notre enveloppe de subprocess. | **Adapter** |
| I4.2 | LF022 · **X** | **`exec` n'est pas une isolation.** Le modèle ne choisit jamais le code exécuté chez nous. | **Adapter** |
| I4.2 | `packages/shared/src/server/evals/localCodeEvalDispatcher.ts:17` | Runner VM local : **plusieurs timeouts locaux et un `Promise.race` ne constituent ni une deadline globale ni un arrêt des effets**. | **Adapter** |


---

## Sources — reprises écartées ou reportées

**10 lignes. N'implémente aucune de ces lignes.** Le pointeur reste pour qu'un retournement de décision retrouve la source. Si tu penses qu'une raison est fausse, **écris-le dans `STATE.md`, n'implémente pas.**

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Statut |
|---|---|---|---|
| A4.2 | `validation_loop.py:110-124` | `infer_validation_scope` — dérive `docs_only`, `formatting_only`, `dependency_changed` des seuls chemins modifiés. Aucun appel modèle. | **Écarté** |
| A4.2 | `validation_loop.py:127-154` | `infer_validation_targets` — mappe une source vers ses tests probables avec un **score de confiance** (0.95 direct, 0.65 inféré). | **Écarté** |
| A4.2 | `validation_loop.py:157-164` | `infer_targeted_command` — restreint `pytest` aux cibles inférées au lieu de la suite entière. | **Écarté** |
| A4.2 | `validation_loop.py:167-169` | `_step_order` — étapes ordonnées par **coût croissant** (format → lint → typecheck → test → build). | **Écarté** |
| A4.2 | `validation_loop.py:190-279` | `plan_validation` — sélection d'étapes avec une **raison textuelle par étape retenue**. | **Écarté** |
| A4.2 | `validation_loop.py:274-278` | `ValidationEscalationPolicy` — *targeted first, then broaden*. Un changement de dépendance force directement la gate large. | **Écarté** |
| A4.2 | `autonomy.py:212-225` | Score de confiance par pénalité de sévérité, borné `[0.05, 0.95]`. Jamais 0 ni 1. | **Écarté** |


#### D — Ouroboros · `resources/ouroboros-main/`

| § | Source | Notion | Statut |
|---|---|---|---|
| D3.3 | `our/tools/verify.py:116-155` | true`, `>/dev/null`. Tokenisation opérateur-consciente. Drapeau seul, jamais le verdict. | **Écarté** |
| D3.3 | `our/tools/verify.py:368-433` | **Capteur 2 — cycle de vie des artefacts.** Sonde après-seulement des chemins déclarés : attrape le build-puis-delete. Chemin absolu ou `..` non sondé. | **Écarté** |
| D3.3 | `our/tools/verify.py:632-641` | **Capteur 3 — `criterion_source`**, défaut `agent_defined`. | **Écarté** |

## Décisions locales — 07:09

### Tranche disponible pendant la conception des faits kernel

L'API livrée est `verifier.check_sources(criterion, before, after, *, artifact_root, timeout)`.
Elle prend deux **sources en mémoire**, crée ses propres copies et rend un `Verdict` de la double gate.
`artifact_root` est un répertoire existant fourni par le harness ; chaque exécution crée un sous-répertoire
exclusif. `timeout` est partagé entre rouge-avant, vert-après et mutants. Le module publie
`SourceVerifier`, satisfait par le package `verifier` et `tests/doubles/verifier.py::MemoryVerifier`.
Le double prend une table de couples `(Criterion, Verdict)` et une table `(RecordKey, Receipt | None)` ;
aucune réponse implicite pour un scénario absent, aucun subprocess ni fichier.

**Cette interface n'est pas encore `run(criterion, facts)`** : le `FileFact` actuellement publié ne
transporte aucun contenu avant/après, et `RepoFact` n'existe pas. Lire `FileFact.path` pour pallier cette
absence violerait notre autorité. Le prochain raccordement doit recevoir des snapshots attestés avec
empreintes correspondant aux octets sources, puis croiser le changement avec un `RepoFact` complet.

`Verdict.verification == 'passed'` signifie seulement : invariant rouge avant, vert après, mutant tué.
Les autres axes restent explicites : `ExecutionResult.execution`, `ExecutionResult.check`,
`KillReport.status`, motifs fermés et artefacts. **Aucun nœud n'est marqué vert ici.**

### Catalogue, admission et preuve conservée

- `Relation` et `Domain` viennent du kernel ; aucune enum concurrente. Huit relations sont exécutables.
  `round_trip` suit la décision 2 et l'exemple encode/decode : **g(f(x)) == x** ; le commentaire inverse
  de l'interface initiale est une coquille. `monotone` n'admet que les domaines numériques, seuls dotés
  ici d'un ordre explicite. `raises_on` exige une classe d'exception déclarée et son **type exact**.
- `schema_conform` refuse `schema_binding_missing` avant I/O : l'outil n'est pas encore relié à son modèle
  Pydantic de sortie déclaré. Le schéma n'est pas inféré des annotations, conformément à l'architecture.
- `small_ints` : [-1000, 1000] ; flottants finis ; texte Unicode de longueur ≤100 ; JSON récursif borné à
  20 feuilles ; chemins lexicaux relatifs de 1 à 4 segments. Aucun domaine paramétré libre ni littéral du
  modèle ne choisit une stratégie. Les expressions embarquées dans le script sont fixes.
- Admission sur la copie en mémoire : ≤2 000 000 octets UTF-8, symbole unique non remplacé par une
  affectation/import, fonction synchrone sans décorateur ni générateur acceptant l'appel unaire. Les
  définitions imbriquées ont leur propre portée. Les annotations/defaults ne sont jamais évalués par
  l'admission AST. Les arguments des propriétés sont copiés pour isoler l'attendu des mutations in place.
- Hypothesis : **seed 0**, 100 exemples, shrinking actif, `database=None`, deadline portée par le runner.
  Les notes du contre-exemple restent intégrales dans `counterexample.txt` ; aperçu distinct borné à
  24 lignes / 1 800 caractères, tête et queue. La borne de caractères n'est pas annoncée comme une borne
  d'octets. Source, script, stdout, stderr, rapport terminal et `meta.json` sont conservés.
- Un exit seul ne prouve rien : seuls **0 + rapport passed** ou **20 + rapport failed** émis à la fin
  du squelette constituent un résultat de propriété. Les sorties prématurées, l'absence de rapport,
  exit 127, panne d'écriture ou timeout n'établissent ni rouge ni vert. `returncode=None` reste inconnu.
- Cinq mutations, un site à la fois dans les corps directs des fonctions ; signatures et définitions
  imbriquées préservées. Chaque mutant est compilé sans exécution avant émission. Un kill exige un
  invariant effectivement rouge. Zéro mutant, erreur d'exécution, délai épuisé ou plafond de 64 mutants
  sans kill : blocage. Survie à tous les mutants effectivement disponibles : rejet tautologique.

### Reçu et limites d'intégration

`emit_receipt(node_id, attempt, facts, artifact, *, key, verdict, journal)` reçoit explicitement la clé
typée, le verdict et le `Journal` injecté. Il vérifie la cohérence nœud/tentative/relation et le chemin de
l'artefact après, puis émet un événement durable de type `validation`. Il rend le `Receipt` **après**
acquittement strict `True`, sinon `None`. Identité, verdict et reçu partagent le même événement ; aucun
repli sur une chaîne d'identité. Aucun fichier externe n'est relu par l'émetteur.

**Portée actuelle de ce reçu : vérification des sources uniquement.** Le payload l'annonce avec
`scope='source_verification'` et `effect='unproven'`. Il ne suffit pas à attester un nœud vert : le futur
`run` doit aussi établir le changement effectif depuis les faits et son appelant doit bloquer sur
`receipt_not_written` lorsque le reçu manque. Ce raccordement n'est pas simulé par une fausse attestation.

Le runner utilise un argv fixe `[sys.executable, '-I', '-B', script]`, un environnement minimal et des
sorties directement vers fichiers, donc aucun pipe hérité ne bloque la fin. Il termine son groupe de
processus. **Ce n'est pas une sandbox contre du code hostile** ; l'isolation hermétique reste suspendue
au spike 5. Les sources testées sont des modules Python autonomes, sans imports de fichiers du workspace.

Stack stdlib utilisée en complément d'`ast`/`subprocess` : `copy`, `datetime`, `hashlib`, `json`, `math`,
`os`, `pathlib`, `signal`, `sys`, `tempfile`, `textwrap`, `time`, `typing`. Aucune dépendance installée.
Les reprises Villani ont été relues sous leur chemin réel `villani_code/` ; la permission de copie est
documentée dans `resources/MANIFEST.md`. Leur tronc d'archivage a été adapté : pas de shell, pas de chemin
workspace, pas de code de retour coercé. Le compacteur conserve aussi la queue après la borne en caractères.
Les reprises de purge, Git, capteurs exclus et gate hermétique n'ont pas été portées.
