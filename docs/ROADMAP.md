# Roadmap

Ordre volontaire : **l'autorité de validation est construite avant tout appel au modèle**. En v1 elle a été
ajoutée en dernier puis rapiécée pendant tout le projet ; c'est l'inversion la plus importante de v2.

Les sources notées `villani/<fichier>:<lignes>` désignent `resources/villani-code-main/villani_code/<fichier>`,
celles notées `pi/<chemin>:<ligne>` désignent `resources/pi-main/<chemin>`, `kilo/<chemin>:<ligne>`
`resources/kilocode-main/packages/<chemin>`, `our/<chemin>:<ligne>` `resources/ouroboros-main/ouroboros/<chemin>`,
`prime/<chemin>:<ligne>` `resources/prime-agent-main/<chemin>`, `uns/<chemin>:<ligne>`
`resources/unsloth-main/<chemin>`, `oh/<chemin>:<ligne>` `resources/OpenHands-main/<chemin>`,
`swe/<chemin>:<ligne>` `resources/SWE-agent-main/<chemin>`,
et `lf/<chemin>:<ligne>` `resources/langfuse-main/<chemin>`.
Le détail de chaque reprise — notion et verdict **Copier / Traduire / Adapter / Inspirer** — est dans
[`IMPORT_REPORT.md`](../resources/IMPORT_REPORT.md) § *Catalogue complet des reprises*, et regroupé par module dans
[`ARCHITECTURE.md`](ARCHITECTURE.md).

**Quatre tags, et chaque item en porte un.**

| Tag | Sens |
|---|---|
| `[TODO]` | à faire |
| `[DONE]` | fait, ou tranché de façon à ne plus être un item |
| `[ÉCARTÉ]` | sorti du périmètre — la raison suit, le pointeur de source reste |
| `[REPORTÉ]` | juste, mais son déclencheur n'existe pas encore — **ne pas implémenter au socle** |

**Passe de simplification du 06:09.** Après un examen module par module de la complexité réelle — reprises,
fichiers sources à lire, fonctions et objets — **~380 reprises sur 1 180 ont été écartées** et la cible est
passée de ~5 900 à ~5 230 L. Les items concernés portent le tag `[ÉCARTÉ]` avec leur
raison : ils gardent leur pointeur, pour qu'un retournement de décision retrouve la source.

⚠️ **Presque tout ce qui a été écarté défendait contre un agent libre** !
→ La contrainte dure n°1 et la décision 6 avaient déjà fermé ces surfaces. Réintroduire une de ces lignes,
c'est réarmer une défense contre une menace que l'architecture a supprimée.

## S — Spikes conditionnant l'architecture

Courts, à faire avant P0. Voir [`ARCHITECTURE.md`](ARCHITECTURE.md) § *Spikes avant de graver*.

- [TODO] Prefect 3 sous launchd en mode éphémère : latence par réveil, persistance, UI a posteriori.
  Mesure avec répétitions, warmup et statistiques : → `pi/scripts/profile-coding-agent-node.mjs:213`
- [TODO] **Spike n°2, reformulé.** La question binaire « la route applique-t-elle la grammaire ? » a déjà sa
  réponse : `response_format` est une **intention** que certaines routes ignorent et que la ladder de retry a
  le droit de retirer (`our/llm.py:2241-2250,183-186`). La revalidation locale est **obligatoire quoi qu'il
  arrive** ; ce qui reste à mesurer est son **coût**. Question effective : *sur un `Criterion` réel avec Ling,
  quel est le taux de rejet de la revalidation locale contre `Criterion.model_json_schema()`, par code
  d'erreur ?* Point d'accueil du code : `our/request_wire_custom_validation.py:107-170`.
- [TODO] **Spike n°4 (nouveau) — la fenêtre réelle et la densité de tokens.** Lire `n_ctx_train` sur
  `/v1/models`, puis mesurer sur dix appels réels le ratio `tokens estimés / prompt_tokens rapportés` pour
  Ling. Notre budget repose sur `len(texte)//4` et un 16 k supposé : **si la densité observée dépasse 1,2, le
  cadran de pression de la décision 14 est faux d'un palier entier.** Deux heures, et cela conditionne tout
  `engine/context`. → `our/local_model.py:579-617` · `our/capability_evidence.py:477-700`
- [TODO] **Spike n°6 (nouveau) — portage de `rt/harness.py` en Pydantic v2.** Le magasin est en dataclass +
  `json` stdlib ; nos contrats sont en Pydantic. Vérifier que la **relecture défensive champ par champ**
  survit à la traduction : **Pydantic lève là où le code d'origine dégrade**, et c'est exactement le
  comportement à ne pas reproduire — un magasin écrit par un modèle doit se relire sans jamais lever.
  → `prime/prime-agent-runtime/src/rlm/harness.py:199-275`
- [TODO] **Spike n°7 (nouveau) — empreinte d'arbre de travail.** Chronométrer `git status --porcelain=v1 -z
  -uall` + `git diff --binary HEAD` + hash des non-suivis sur le dépôt de campagne, à chaque frontière de
  nœud. Si le coût est négligeable — attendu, le dépôt est petit — la règle **« ne pas relancer une gate sur
  un arbre inchangé »** devient gratuite, et elle ferme les six heures de boucle stérile de v1.
  → `prime/packages/coding-agent/src/core/autonomous.ts:374-423`
- [TODO] **Spike n°5 (nouveau) — le coût de la gate hermétique.** Mesurer l'assemblage d'un worktree jetable
  (`git worktree add` + capture `--binary` + copie des non-suivis) sur le dépôt de campagne. **De l'ordre de
  la seconde** ⇒ la gate de régression tourne dans un worktree jetable à chaque mission et la classe entière
  « verte parce que le worktree était sale » disparaît. **De l'ordre de la dizaine de secondes** ⇒ réservée à
  la fin de mission. → `our/preflight_runner.py:1189-1330`
- [TODO] Contrainte de schéma sur la route `/v1` d'Ollama avec Ling, sur un `Criterion` réel.
  Point d'insertion déjà repéré : `villani/openai_client.py:75-86`. Le mode doit être **`require`**, pas
  `prefer` — un repli silencieux ferait retomber la contrainte dure n°1 : → `pi/packages/ai/src/api/constrained-sampling.ts:208`
- [TODO] **Prérequis du spike n°2** : normaliser le schéma Pydantic avant de l'envoyer. Pydantic v2 émet des
  `$defs`/`$ref` pour toute enum et tout modèle imbriqué ; un `integer` sans bornes fait échouer certaines
  grammaires. À écrire et tester **avant** de mesurer `response_format`.
  → `kilo/opencode/src/tool/json-schema.ts:8-158`
- [TODO] Fixer l'échantillonnage `temperature 0.3` / `top_p 0.95` / `top_k 20` et dériver le prompt système
  de `ling.txt` et de ses sept modes d'échec documentés.
  → `kilo/opencode/src/provider/transform.ts:588-631` · `kilo/opencode/src/session/prompt/ling.txt`

## M — Scaffold, doubles et jalon « premier vert »

Entre les spikes et P0. **Aucune de ces étapes n'écrit de logique métier** : elles posent les frontières et
prouvent qu'elles s'emboîtent. Voir décisions 32 et 33.

- [TODO] `git init`, `.gitignore` excluant les neuf dépôts de `resources/`, et `resources/MANIFEST.md`
  figeant nom, version, taille et licence de chaque source. Les pointeurs `fichier:ligne` de ce document
  restent vérifiables sans versionner 475 Mo de code tiers.
- [DONE] **06:09** — Environnement d'exécution : virtualenv pyenv **`pithos`, Python 3.12.9**, sélectionné par
  `.python-version`, figé par `requires-python` dans `pyproject.toml`, dépendances déclarées et justifiées
  dans `requirements.txt`. **Rien ne peut être testé avant cette étape** : la boucle de travail d'un agent
  (`AGENTS.md` § 5) s'arrête à « lancer les tests du module ».
- [TODO] Arborescence `src/<module>/` pour les **onze** modules, avec un **`MODULE.md` rempli par module** —
  huit rubriques fixes, dont la cible de lignes et la liste « fini quand ». **Écrits avant la moindre ligne
  de Python.** → `ARCHITECTURE.md` § *Développement par module*
- [TODO] `typing.Protocol` + modèles Pydantic pour les **onze** interfaces, et un **double conforme** par module
  dans `tests/doubles/`. Test de conformité double ↔ implémentation, pour que le double ne dérive pas.
- [TODO] **Test de graphe d'imports des trois règles** : `verifier` sans le bridge ni le modèle, `bridge`
  sans `engine`, et `broker` seul module d'egress. → `pi/scripts/check-entry-graphs.mjs:33`
- [DONE] **Jalon « premier vert », de bout en bout et à la main** : une nano-étape, un invariant d'une seule
  relation, un mutation-check, un reçu, un fichier de campagne réellement modifié. Ne qualifie rien ;
  détecte une erreur de découpe pendant qu'elle coûte encore peu. Constaté le 15:09 dans
  trial-25ugxn94 sous unit_projection ; un reçu durable, trois gates et un fichier modifié.

## P0 — Socle d'état et de traces

- [TODO] Modèle de nœud de travail et sérialisation atomique de l'arbre (`tree.json`).
  → `villani/mission_state.py:12-95,114-117`
- [TODO] **Module `journal`** : `append` retournant un booléen, `fsync` explicite, **un verrou global
  unique** (~15 L), écriture atomique temp+rename portant pid + timestamp + suffixe aléatoire, flag
  `durable`, champ `v` par ligne et **signature de génération de fichier**. Une écriture, deux sorties —
  la ligne JSONL complète puis sa projection d'une ligne dans `live.log`.
  → `our/utils.py:212-338,463-612` · `prime/ca/core/event-log.ts:15-52` · `kilo/opencode/src/util/filesystem.ts:84-113`
- [TODO] **Sens lecture de `journal`** : itération, lecture bornée, **détection de queue déchirée sans
  réparation**, et reprise des identifiants d'événement après redémarrage. Un format, un parseur —
  `observatory` lit par lui. → `villani/trace_summary.py:16-51` · `pi/…/jsonl/storage.ts:87`
- [TODO] **Une seule fonction de rédaction** `redact(structure) -> (valeur, chemins_rédigés)`, alimentée par
  une liste de motifs nommée. ~25 L. → `our/observability.py:1083-1087`
- [TODO] **Magasin à deux familles vivantes, propriété de `campaign`** — `prompt`, `memory`, `skill`, `subagent` —
  avec relecture défensive champ par champ qui **ne lève jamais** sur une entrée mal formée, versionnement,
  deux scopes et rendu compact pour le prompt. La famille `skill` **est** le registre d'outils.
  → `prime/rt/harness.py:94-820` (spike n°6) — décision 26 amendée
- [TODO] **Écriture de la famille `memory` dès le socle** : nœud `blocked` avec cause mécanique, invariant
  rejeté comme tautologique, proposition récurrente avec son compteur — indexés par empreinte de contrat.
  Trois écrivains, une seule clé. Décision 31.
- [TODO] Types de fait remontés à `verifier` — `FileFact` par `workspace`, `RepoFact` par `broker`,
  `HostFact` par `lifecycle` — et la forme du `Receipt` qu'ils alimentent. **`kernel` porte la forme,
  `verifier` seul a l'autorité d'émettre.** Décision 13 amendée.
- [TODO] Prédicat `authoritative` unique et classification des chemins, partagé par tous les modules.
  → `villani/repo_rules.py:44-91` · `villani/state_execution.py:17-30` · `villani/benchmark/policy.py:29-57`
- [TODO] Lecture AST du workspace : symboles, arité, `def` de niveau module, snippet borné.
  → `villani/indexing.py:69-114,146-150` — **sans** les regex de `indexing.py:57-66`
- [TODO] Empreinte de repo par SHA-256 `path:size:mtime`, pour invalider un index sans le relire.
  → `villani/indexing.py:117-127`
- [TODO] Écriture atomique par temporaire portant **pid + timestamp + suffixe aléatoire** puis `rename` ;
  erreurs identifiables par nom après sérialisation ; magasin arborescent de JSON à clé hiérarchique.
  → `kilo/opencode/src/util/filesystem.ts:84-113` · `kilo/core/src/util/error.ts:3-72` · `kilo/opencode/src/storage/storage.ts:53-81`
- [TODO] Abonnement au bus acquis **au yield**, pas à la première lecture ; flux terminé par un événement
  terminal explicite, jamais par du silence.
  → `kilo/opencode/src/bus/index.ts:41-89`
- [TODO] Planchers sur les champs de budget — **un zéro dans un champ de durée est un interrupteur
  silencieux** ; état persisté séparant ce que l'opérateur possède de ce que le harness possède.
  → `kilo/kilo-memory/src/schema.ts:174-227`
- [TODO] Écriture JSONL append-only par mission avec flag `durable`, réplication dans `live.log`.
  → `villani/runtime_events.py:8-34` · `villani/event_recorder.py:20-33`
- [TODO] Version explicite du format persistant (`Event`, `tree`, `registry`) ; refus d'une version inconnue.
  → `pi/packages/agent/src/harness/session/jsonl/types.ts:4`
- [TODO] Publier sur disque **avant** de modifier la projection mémoire ; ids uniques et parent antérieur
  validés avant publication.
  → `pi/packages/agent/src/harness/session/jsonl/storage.ts:253` · `pi/packages/agent/src/harness/session/commit.ts:90`
- [TODO] Détecter une fin de journal tronquée **sans jamais la réparer** ; framing sur LF uniquement.
  → `pi/packages/agent/src/harness/session/jsonl/storage.ts:87` · `pi/packages/coding-agent/src/modes/rpc/jsonl.ts:21`
- [TODO] Résultats discriminés à codes fermés ; snapshots de trace détachés des objets mutables.
  → `pi/packages/agent/src/harness/result.ts:1` · `pi/packages/telemetry/src/memory.ts:54`
- [TODO] Identifiants d'événement reprenant après redémarrage ; compteurs de tokens jamais coercés à zéro.
  → `villani/trace_summary.py:16-51,104-133`
- [TODO] Reprise d'une mission interrompue depuis l'arbre persistant, sans historique conversationnel.
  → `villani/mission_state.py:162-171`
- [TODO] Réconciliation au démarrage des missions restées actives dont le processus a disparu.
- [TODO] Primitives d'écriture durable : temporaire sibling + `os.replace` avec bits préservés, `fsync`
  explicite, balayage des temporaires orphelins, `append_jsonl` renvoyant **`bool`** et jamais un succès
  simulé, verrou sidecar, signature de génération pour détecter une rotation.
  → `our/utils.py:151-169,212-612`
- [TODO] Registre append-only à **séquence dense** et machine à états validée au replay ; validation
  **incrémentale** de la queue ; deux exceptions typées — **un registre corrompu ne se lit pas « comme vide »**.
  → `our/usage_ledger.py:41-48,228-477`
- [TODO] Rédaction de secrets à **quatre couches** de reconnaissance, projection unique renvoyant la valeur
  rédigée **et la liste des rédactions**, modes POSIX privés, filtre `logging`.
  → `our/observability.py:33-192,1083-1087,1452-1470`
- [TODO] Payload volumineux transformé en **ref content-addressé** au-delà d'un seuil ; rétention des blobs
  comme fonction nommée. → `our/observability.py:262-340,1378-1450`
- [TODO] Axes d'issue séparés et **vocabulaires de non-échec** : un garde-fou qui fonctionne n'est pas une
  panne (décision 23). → `our/outcomes.py:83-142,284-295`
- [TODO] Substrat JSONL crash-safe : append `O_APPEND` unique, `fsync` à la demande, **offsets en octets sur
  buffers bruts** (les indices de chaîne divergent au premier caractère multi-octets), bornes de lecture
  vérifiées **sur le même fd** que l'allocation.
  → `prime/ca/core/event-log.ts:15-52,158-175`
- [TODO] Idempotence : une clé de requête n'est sûre que pour un **retry octet-identique** — hash de contenu
  de la requête, pas seulement son identifiant. → `prime/ca/core/semantic-edges.ts:118-149`
- [TODO] **Espace disque mesuré avant écriture** d'un snapshot, d'une trace ou d'un artefact ; insuffisance
  transformée en `blocked` mécanique avec cause. Temporaires redirigés vers un emplacement contrôlé.
  → `uns/unsloth/disk_utils.py:83,109,120`
- [TODO] Résolution **unique** des capacités matérielles derrière un prédicat mis en cache ; parallélisme
  dérivé des ressources avec **repli mono-processus** ; nettoyage de cache entre étapes.
  → `uns/unsloth/device_type.py:62,100,257` · `uns/unsloth/dataset_num_proc.py:1`
- [TODO] **Chat template centralisé et normalisé** : l'exécuteur ne reçoit jamais un template arbitraire du
  modèle ; EOS effectifs déduits du tokenizer et consignés dans le contrat d'exécution.
  → `uns/unsloth/chat_templates.py:1885,2370`
- [TODO] **Version minimale de backend compatible**, codes d'erreur fermés, refus **avant toute mission** ;
  **une version inconnue est un état distinct, jamais la version courante** ; comparaison **sémantique** ;
  erreur typée distinguant backend absent, indisponible et détail de connexion.
  → `oh/src/api/agent-server-compatibility.ts:19,50,81,95,252`
- [TODO] **Placeholders fermés sans expression évaluable** : lecture par chemin fermé, interpolation
  conservant le type quand le placeholder occupe tout le champ, **aucune évaluation**.
  → `oh/src/manifests/types.ts:30` · `oh/src/manifests/manifest-template.ts:21,65,76`
- [TODO] Mode **offline** détecté explicitement et inscrit dans l'événement de mission ; présence locale des
  fichiers vérifiée **avant tout appel réseau** ; sessions réinitialisées après erreur pour qu'un état global
  contaminé ne traverse pas les missions.
  → `uns/unsloth/models/loader_utils.py:1694,1900,2156`
- [TODO] **`thought` / `action` / `observation` en champs typés distincts**, jamais concaténés ;
  `message_type` en littéral fermé obligatoire ; **le dictionnaire de formatage n'est pas l'objet machine**.
  → `swe/sweagent/types.py:15-41,56-74`
- [TODO] Fusion récursive de configuration **sans écraser silencieusement les sous-clés** ; chemins absolus
  retirés **avant d'écrire une trace partageable**.
  → `swe/sweagent/utils/serialization.py:36` · `swe/sweagent/utils/config.py:30`
- [TODO] **Treize hooks nommés du cycle de vie** et un combinateur qui compose sans que l'appelant sache
  combien il y en a. → `swe/sweagent/agent/hooks/abstract.py:10-56`
- [TODO] **Identité de résultat déterministe distincte de l'identité de transport** (décision 30) : hash sur
  `(mission, nœud, tentative, relation)` stable au retry, identifiant d'émission renouvelé et **exclu de toute
  comparaison**. → `lf/packages/shared/src/server/evals/evalScoreIds.ts:6` · `lf/worker/src/features/evaluation/evalScoreEvent.ts:21`
- [TODO] **Métadonnées de provenance écrites après la charge utile**, dans un espace de champs réservé ; la
  valeur d'autorité **inatteignable par le schéma d'admission**, pas seulement par un défaut sûr.
  → `lf/worker/src/features/evaluation/evalScoreEvent.ts:54` · `lf/packages/shared/src/domain/scores.ts:18`
- [TODO] **Mesure fournie distincte de mesure calculée** — valeur, origine, disponibilité ; ne jamais agréger
  une absence en zéro. → `lf/packages/shared/src/domain/observations.ts:82`
- [TODO] Utilitaires de chemin partagés (`is_path_within`, normalisation, comparaison).
  → `villani/utils.py:22-27` · `villani/benchmark/policy.py:29-57`

## P1 — Autorité de validation

Le cœur — relations, domaines, mutations — est **sans équivalent chez Villani** et s'écrit de zéro. Les
reprises portent sur ce qui l'entoure.

- [TODO] Catalogue fermé des relations métamorphiques et de leur rendu exécutable. *(neuf)*
- [TODO] Catalogue fermé des générateurs de domaine, déterministes et seedés, mappé sur Hypothesis. *(neuf)*
- [TODO] Mutation-check : rejet d'un invariant qui survit à toutes les mutations de la cible. *(neuf)*
- [TODO] Vérification AST des symboles nommés : existence, arité, compatibilité avec la relation. *(neuf)*
- [TODO] Gate rouge-avant, avec exigence d'un échec par assertion et non par erreur d'arité. *(neuf)*
- [TODO] Exécution d'un script rendu en `subprocess`, avec archivage `stdout` / `stderr` / `meta.json`.
  → `villani/benchmark/verifier.py:39-137`
- [TODO] Capture de sortie bornée avec métadonnées de troncature ; **fin de processus distincte de fin de
  sorties** (inactivité + deadline absolue) ; délais invalides refusés avant création du processus.
  → `pi/packages/agent/src/harness/utils/output-capture.ts:26` · `pi/packages/coding-agent/src/utils/child-process.ts:49` · `pi/packages/coding-agent/src/core/tools/bash.ts:25`
- [TODO] Matrice de reprise couvrant chaque état durable ; injection déterministe d'un crash entre admission
  et persistance ; faux provider scénarisé à ids et horloge fixés.
  → `pi/packages/agent/test/harness/runtime/drive-reconcile.test.ts:450` · `pi/packages/agent/src/harness/session/testing/gating-storage.ts:26` · `pi/packages/ai/src/providers/faux.ts:144`
- [TODO] Normalisation de commande (`pytest` → `sys.executable -m pytest`) et distinction
  **échec de lancement** (exit 127/9009) vs contrat rouge.
  → `villani/benchmark/verifier.py:15-36`
- [TODO] Suite de régression accumulée, rejouée en gate au démarrage de chaque mission ; commandes persistées
  comme donnée, pas comme constante du harness.
  → `villani/project_memory.py:99-142` · `villani/validation_loop.py:302-329`
- [ÉCARTÉ] Planification de validation : périmètre, ordre par coût croissant, ciblage puis
  élargissement. **La stack actée n'a ni linter ni typechecker : l'échelle a une seule marche, il n'y a rien
  à ordonner.** ~150 L. → `villani/validation_loop.py:110-169,190-279`
- [TODO] Résumé d'échec structuré rendu au modèle (`failure_class`, `relevant_error_lines`,
  `recommended_repair_scope`) et compactage tête/queue borné.
  → `villani/validation_loop.py:282-299` · `villani/planning.py:403-411`
- [TODO] Rendu d'échec au format diagnostics : **seules les erreurs montrées**, plafond par fichier,
  `... and N more` visible ; au-delà des plafonds le texte intégral part dans un fichier dont l'aperçu porte
  le chemin. Deux plafonds (lignes **et** octets) et le message dit lequel a été atteint.
  → `kilo/opencode/src/lsp/diagnostic.ts:3-28` · `kilo/opencode/src/tool/truncate.ts:12-15,87-149`
- [TODO] Prélude git fixe sur chaque invocation (`--no-optional-locks`, `core.autocrlf=false`,
  `core.quotepath=false`…) ; échec de spawn normalisé en résultat, jamais en seconde forme d'erreur.
  → `kilo/opencode/src/git/index.ts:6-30,64-101`
- [TODO] Vérificateur adversarial : preuve d'effet réel par `before_contents` + `git diff`, largeur suspecte,
  réconciliation des findings contredits par la preuve directe.
  → `villani/autonomy.py:62-246,261-302`
- [TODO] Détection de boucle stérile par empreinte de findings répétée à l'identique.
  → `villani/autonomy.py:203-210`
- [TODO] Taxonomies fermées de findings et de causes d'échec, avec compteur d'occurrences déclenchant
  `REPEATED_NO_PROGRESS` au troisième.
  → `villani/autonomy.py:17-27,311-387`
- [TODO] **Reçu attesté par l'hôte** : exécuter la vérification déclarée **et** écrire le reçu dans le même
  acte ; un reçu non écrit **retire l'attestation**. Modes de comparaison en énumération fermée ; aucune
  coercition `or` sur un code de retour. → `our/tools/verify.py:44-110,282-366,553-850`
- [TODO] **Trois capteurs de faux-vert**, drapeau seul et jamais le verdict : masquage d'exit dans une
  commande de régression persistée, cycle de vie des artefacts déclarés, provenance du critère
  (`task_stated` / `agent_defined`, défaut `agent_defined`).
  → `our/tools/verify.py:116-155,368-433,632-641`
- [TODO] **Identité de vérification en clé typée** `(kind, value)`, table de kinds **totale**, tampon de
  version du rendu, canonicalisation qui ne jette aucun octet, décideur et rapporteur sur la même projection
  (décision 22). → `our/_outcome_receipts.py:50-64,131-300,344-460`
- [TODO] Ensemble des vérifications **encore ouvertes** calculé une fois — c'est « le nœud qui ne peut pas se
  déclarer vert ». → `our/_outcome_receipts.py:687-806`
- [TODO] **Gate hermétique** : worktree git jetable, capture `--binary` durcie, **scrub d'environnement**
  (variables du harness, secrets, `PYTEST_*`), refus de démarrer sans budget de rendu, ANSI retiré avant tout
  matching. → `our/preflight_runner.py:99-176,414-480,576-625,1189-1330`
- [TODO] **Attribution de mutation avec époques de baseline** : candidats = changés moins sales-au-baseline,
  blockers typés, ré-ancrage strict, `dirty_overflow` plutôt qu'une approximation coûteuse.
  → `our/mutation_attribution.py:31-158,213-800`
- [TODO] **Indépendance et parité de la preuve** : quels fichiers de vérification l'agent a lui-même écrits,
  et la borne du décideur qui suit celle de l'acteur. → `our/review_evidence.py:17-105`
- [TODO] **Ne pas relancer une gate si l'arbre de travail n'a pas bougé** : le compteur de tentative avance,
  le message dit pourquoi. Empreinte = `status --porcelain=v1 -z -uall` + `diff --binary HEAD` + hash des
  non-suivis, avec pathspec d'exclusion. **Un snapshot partiel est un non-snapshot** — pas d'empreinte donc
  pas d'égalité, donc la gate est relancée : le repli est sûr.
  → `prime/ca/core/autonomous.ts:294-311,374-469`
- [TODO] **Les tokens de lecture de cache ne comptent pas dans le budget.**
  → `prime/ca/core/autonomous.ts:186-194`
- [TODO] Les gates sont interrogées **avant** les limites : une gate verte arrête proprement même s'il reste
  du budget. → `prime/ca/core/autonomous.ts:227-252`
- [TODO] **Tester l'absence d'import eager d'une dépendance optionnelle** — complément direct du test de
  graphe d'imports. Et **idempotence des correctifs d'initialisation** : exécutés deux fois, ils ne modifient
  plus l'état. → `uns/tests/test_torchao_nf4tensor_move.py:152,191` · `uns/tests/test_peft_symbol_backfill.py:96`
- [TODO] **Normaliser les kwargs pour que deux configurations sémantiquement égales aient la même
  empreinte** — brique directe de la clé typée de la décision 22.
  → `uns/unsloth/models/loader_utils.py:180`
- [TODO] Vérifier qu'une borne tient **au moment de l'usage**, pas seulement à la déclaration ; refuser une
  combinaison incompatible **avant exécution** plutôt que laisser le backend échouer tard.
  → `uns/unsloth/models/rl.py:906,921,1005` · `uns/unsloth/models/loader_utils.py:1522`
- [TODO] **Admission déclarative (décision 28)** : identifiants validés par regex avant insertion au
  registre, markup interdit dans tout texte rendu, **commandes restreintes à un alphabet sans métacaractères
  shell**, chemins restreints à des préfixes autorisés et vérifiés relatifs, énumérations fermées, bornes
  dures de longueur, **fonction publique unique renvoyant `{valid, errors}`**.
  → `oh/src/manifests/manifest-validation.ts:25,28,42,44,51,65,148,165,576`
- [TODO] **Accumulateur d'erreurs avec chemin de champ : toutes les violations retournées en une fois.** Sur
  un modèle à 16 k, une proposition à trois défauts coûte sinon trois sessions au lieu d'une.
  → `oh/src/manifests/manifest-validation.ts:93` · `oh/src/manifests/automation-setup.ts:403`
- [TODO] **Gate locale rapide avant tout appel réseau ou création d'effet.**
  → `oh/src/manifests/manifest-local-validation.ts:167`
- [TODO] **Catalogue de parsers fermés** pour lire une sortie modèle sans tool calling natif : action seule,
  → `swe/…/flake8_utils.py`
- [ÉCARTÉ] Catalogue de douze parsers fermés. **Il existe pour des backends sans sortie structurée
  native ; nous avons `response_format` json_schema plus revalidation locale, et une sortie non conforme est
  rejetée, jamais récupérée.** Deux notions survivent et passent dans `bridge` : rejeter un appel de fonction
  inconnu, et localiser l'erreur JSON. ~200 L.
  → `swe/sweagent/tools/parsing.py:52,97,109,168,225,324,354,371,457,574`
- [TODO] **Exceptions internes distinctes** — action bloquée, retry, forfeit, timeout global : quatre causes,
  quatre types. → `swe/sweagent/agent/agents.py:199`
- [TODO] **Relocaliser les erreurs de lint après une édition** — les numéros de ligne ont bougé.
  → `swe/tools/windowed/lib/flake8_utils.py:26,59,92`
- [TODO] **Publier la preuve durable avant la transition terminale**, réconciliation au démarrage entre les
  deux. **Un `catch` qui journalise un échec d'écriture de trace et continue est inacceptable pour la preuve
  primaire.** → `lf/worker/src/features/evaluation/evalCompletion.ts:23` · contre-exemple `lf/packages/shared/src/server/evals/codeEvalExecution.ts:363`
- [TODO] **Taxonomie d'erreurs de l'exécuteur** — source invalide, timeout, erreur du code, réponse invalide —
  et **les retries se déterminent depuis la cause**. Résultat structuré **non vide** : un booléen seul n'est
  pas un verdict. → `lf/packages/shared/src/server/evals/codeEvalDispatcherTypes.ts:131,161`
- [TODO] **Schéma compilé réutilisé pour un lot**, erreurs avec `path`/`message`/`keyword`. Ne **pas** reprendre
  la configuration voisine qui ne renvoie que la première erreur.
  → `lf/packages/shared/src/utils/jsonSchemaValidation.ts:58` · contre-exemple `:25`
- [TODO] Contrat de preuve par type de nœud : un artefact de validation exige `(exit=0)` littéral.
  → `villani/autonomous_helpers.py:88-120`

## P2 — Boucle de nano-étapes

- [TODO] Phase `decompose` : scission d'un nœud sans critère, sortie structurée bornée.
- [TODO] Phase `implement` en mode `direct` : génération bornée, patch appliqué par le harness.
- [TODO] Contrainte de décodage **requise** (`require`, jamais `prefer`) ; thinking séparé du contenu ;
  terminaison de stream explicite ; budget réservant la place de la sortie ; retries SDK désactivés.
  → `pi/packages/ai/src/api/constrained-sampling.ts:208` · `pi/packages/ai/src/api/openai-completions.ts:601,692,364` · `pi/packages/ai/src/api/simple-options.ts:15`
- [TODO] Annulation qui ferme réellement stream et client ; admission de nouveaux effets fermée avant
  propagation de l'annulation.
  → `pi/packages/ai/src/utils/abort.ts:17` · `pi/packages/agent/src/harness/execution/effect-gate.ts:31`
- [TODO] Phase `verify` : exécution du critère, puis de la régression.
- [TODO] Splice AST d'une fonction unique (`{function_name, new_source}`), avec extraction du code depuis un
  payload enveloppé en blocs ```` ``` ```` et sanitisation du chemin cible.
  → `villani/state_tooling.py:44-86,177-207`
- [TODO] **Strip des préfixes `N: ` de `new_source` avant parse** — Ling recopie la numérotation de lignes
  dans son payload. Sans cette garde, chaque splice échoue silencieusement.
  → `kilo/opencode/src/session/prompt/ling.txt:109-115` · `kilo/opencode/src/tool/read.ts:352-364`
- [TODO] Garde de complétude contre la troncature : un `def` tronqué peut rester syntaxiquement valide.
- [TODO] **Projection de fichier déclarant ce qu'elle cache (décision 29)** : ligne de statut
  `[File: X (N lines total)]`, `(N more lines above)`, `(N more lines below)`, fenêtre numérotée.
  → `swe/tools/windowed/lib/windowed_file.py:150-175`
- [TODO] **Fusion des intervalles chevauchants avant projection** — sans elle, deux hunks voisins projettent
  trois fois le même bloc ; `context_length` et `linenos` explicites.
  → `swe/sweagent/utils/patch_formatter.py:28-49,98,147`
- [TODO] **Une mutation rend son bilan chiffré** — ligne de départ, lignes cherchées, lignes remplacées,
  **nombre de remplacements** ; plus un `undo_edit` au niveau du fichier, distinct du rollback de mission.
  → `swe/tools/windowed/lib/windowed_file.py:36-52,276`
- [TODO] **Revalidation locale** de la sortie contre le schéma exact envoyé, reçu liant requête / catalogue /
  schéma / arguments par SHA-256, cinq codes d'erreur fermés, `json.loads` refusant `NaN`/`Infinity`.
  → `our/request_wire_custom_validation.py:15-22,85-105,107-170`
- [TODO] Canonicalisation du chemin **en premier**, puis root, puis artefacts protégés — *« a guard that
  judges a different string than the one that executes is not a guard »* ; lot d'éditions annulé **entier
  avant écriture** si le nombre d'occurrences attendu diffère.
  → `our/tools/edit_ops.py:79-157,573-677`
- [TODO] Parseurs argv **partagés par tous les garde-fous** et un seul seam décidant si une commande est
  *write-shaped*. → `our/shell_parse.py:1-60` · `our/tools/write_shape.py:1-40`
- [TODO] **Deux réserves murales distinctes** — « ne plus démarrer » calibrée par EWMA, et « finaliser » —
  avec **latch de l'ancre de départ** (décision 8 amendée).
  → `our/task_pacing.py:87-110,148-279,233-245`
- [TODO] **Ledger d'arbre append-only par racine**, kinds fermés, curseur `(ts, ids vus)`, disposition
  d'enfant liée au SHA-256 du résultat, bornes explicites avec message qui dit quoi faire.
  → `our/task_tree_ledger.py:34-61,108-168,384-433,580-705`
- [TODO] **`disposition` nommée sur chaque fichier du codeview** — l'index ne ment jamais par omission — et
  `relevant_files`/`impact_files` avec **une raison textuelle par fichier**, sans aucun appel modèle.
  → `our/code_intelligence.py:73-121,485-635,737-800`
  → `kilo/opencode/src/session/prompt/ling.txt:23`
- [ÉCARTÉ] Seuils de mutation nommés et analyse de réécriture par `SequenceMatcher`, en seconde ligne.
  **Le splice par plage AST borne le rayon d'action par construction : une réécriture massive n'est pas un cas
  à détecter, c'est un cas que le mécanisme ne peut pas produire.** ~60 L.
  → `villani/state_tooling.py:21-122`
- [TODO] Garde syntaxique sur les changements `.py` avant écriture, avec message d'erreur nommant fichier,
  validateur, type d'exception et action attendue.
  → `villani/state_tooling.py:236-291`
- [REPORTÉ] Snapshot / restauration par **dépôt Git fantôme** : `git init` dans un `--git-dir` hors projet,
  `write-tree` pour capturer, `read-tree` + `checkout-index` pour restaurer, tous les hashes validés avant de
  toucher un fichier, échec fatal plutôt que restauration partielle. **Au socle, la transaction est une copie
  d'octets** — `before = read_bytes()` / `write_bytes(before)`, ~10 L au lieu de ~150 — parce que la
  contrainte dure n°3 dit « son fichier cible », au singulier, et que `Node.target` est désormais un `Path`,
  pas une liste. Le dépôt fantôme revient quand une étape devra toucher plusieurs fichiers.
  → `kilo/opencode/src/snapshot/index.ts:107,111,406-408,465-501` · `kilo/opencode/src/session/revert.ts:78-118`
- [TODO] **`writeIfUnchanged`** — compare-and-swap sur le contenu, sous verrou par chemin canonique et
  section ininterruptible. Un changement concurrent devient un `StaleContentError` typé.
  → `kilo/core/src/file-mutation.ts:79-83,144-158`
- [TODO] **Le marqueur de complétude est le point de commit** : écrit en dernier, après journal, arbre et
  artefacts, par `rename` atomique ; le curseur n'avance qu'ensuite.
  → `lf/worker/src/features/blobstorage/handleBlobStorageIntegrationProjectJob.ts:1433` · `lf/worker/src/features/blobstorage/manifest.ts:22`
- [TODO] **Référence d'artefact publiée seulement après écriture réussie** ; en cas d'échec, la valeur reste
  en place. → `lf/worker/src/features/observation-field-overflow/processObservationFieldOverflow.ts:35`
- [TODO] **Exclusivité conservée jusqu'à la fin réelle de l'écriture** — un verrou libéré à l'annulation
  autorise une écriture tardive après rollback. Testé par intercalation.
  → `pi/packages/coding-agent/src/core/tools/write.ts:69`
- [TODO] Staging + `os.replace` avec temporaire unique dans le même filesystem, flush/fsync, nettoyage sur
  échec ; préservation BOM et fins de ligne ; détection d'un patch sans effet.
  → `pi/packages/agent/src/harness/session/jsonl/storage.ts:94` · `pi/packages/coding-agent/src/core/tools/edit.ts:192` · `pi/packages/coding-agent/src/core/tools/edit-diff.ts:357`
- [TODO] Politique d'écriture : cible `authoritative` obligatoire, read-before-edit, refus hors cible.
  → `villani/state_runtime.py:479-505,508-590`
- [TODO] Protection contre le shadowing des dépendances du harness par le repo produit, et `sys.path`
  temporaire restauré intégralement.
  → `villani/runtime_safety.py:42-66`
- [TODO] Borne murale de mission, finalisation des nœuds verts à l'expiration ; bornes d'exploration stérile
  (`max_no_edit_turns`, `max_reconsecutive_recon_turns`).
  → `villani/execution.py:6-43`
- [TODO] Contexte de nœud comme inventaire typé : raisons d'inclusion et d'exclusion, paliers de pression,
  évictions comptées, détection de dérive. **Évincer, jamais résumer** — si le contenu irréductible dépasse le
  budget, le nœud est `blocked` avec cause mécanique.
  → `villani/context_governance.py:11-31,34-71,200-220,252-266`
- [TODO] **Dump de contexte en fin de session** : `~/logs/pithos2/missions/<id>/CONTEXT.md`, une section par
  session — nœud, critère, inclusions et exclusions avec leur raison, pression, évictions, verdict, et
  **l'empreinte des fichiers décrits**. Écrit par le harness, ~30 L. Réinjecté plus tard, il est traité comme
  tout élément de contexte et soumis à `detect_stale_context`.
- [ÉCARTÉ] Compactage par type de source et contrat de résumeur haché. **Session neuve par nœud : il
  n'y a aucune conversation à compacter, et un résumé serait du texte du modèle entrant dans le prompt
  suivant.** ~150 L. → `our/context_compaction.py:280-417,681-738`
- [TODO] Filtrage des chemins d'artefacts runtime avant projection au modèle ; paquet structuré puis rendu
  texte séparé.
  → `villani/context_projection.py:9-70`
- [TODO] Classification déterministe de la tâche : classes d'action, portée, impact, risque, mode.
  → `villani/planning.py:11-57,215-332,388-400`
- [TODO] Boucle de réparation ciblée sur la seule étape en échec, avec historique de tentatives réinjecté.
  → `villani/repair.py:11-106`
- [TODO] **Buffer de sortie borné tête + queue roulante** avec marqueur d'octets jetés, pour toute exécution
  de code produit ; code de sortie récupéré par **canal de statut sur fd dédié**, pas par le retour du shell ;
  `NO_COLOR` / `TERM=dumb` sur tout sous-processus dont la sortie est rendue au modèle.
  → `prime/rt/bash.py:60-104,711-727,731`
- [TODO] Trois fonctions de troncature nommées (`head` / `tail` / `line`) plutôt qu'un paramètre de mode ;
  deux limites indépendantes, jamais de ligne partielle, et la troncature **rend son bilan**.
  → `prime/ca/core/tools/truncate.ts:1-38,67-249`
- [TODO] Points d'extension **nommés** dans la boucle (`shouldStopAfterTurn`, `getSteeringMessages`,
  `getContinuationMessages`) : une boucle, plusieurs politiques. Une interruption arrivée au moment de l'arrêt
  **gagne contre l'arrêt**. → `prime/ag/agent-loop.ts:304-450`
- [TODO] **Un seul deadline monotonique de mission propagé à toutes les sous-opérations**, plutôt que des
  timeouts indépendants qui s'additionnent ; terminaison **récursive de l'arbre de processus** avec son propre
  timeout de nettoyage. → `uns/unsloth/dataprep/synthetic.py:52,162,172`
- [TODO] **Claim idempotent d'une demande d'effet à identité connue** — lancement d'un nœud enfant, promotion
  d'un outil, création de PR : une seconde réclamation du même identifiant est un no-op. Face amont de la
  décision 16. → `oh/src/services/child-conversation-launch.ts:110,205,241`
- [TODO] **Modes d'isolation énumérés** plutôt qu'un booléen implicite ; **secret vide traité comme absent**,
  n'écrasant jamais une valeur existante.
  → `oh/src/constants/child-conversation.ts:26` · `oh/src/api/agent-server-adapter.ts:600`
- [TODO] Collecter un stream **sans perdre le texte déjà reçu** quand la connexion se ferme prématurément ;
  transformer une erreur de stream en **exception structurée avant d'écrire un événement de succès**.
  → `uns/unsloth_cli/_inference.py:310,318`
- [TODO] **Masquer les frontières de séquences** pour qu'une validation ne puisse pas traverser deux
  exemples — analogue direct : un invariant ne déborde pas sur le nœud voisin.
  → `uns/unsloth/utils/packing.py:719`
- [TODO] Interruption : premier signal interrompt, second quitte.
  → `villani/interrupts.py:7-18`
- [TODO] Résumés de phase déterministes, jamais générés.
  → `villani/summarizer.py:9-55`

## P3 — Registre et propositions

- [TODO] `registry.json` : outils, schémas, statuts, invariants tenus, **empreinte de vérification**.
  → `villani/autonomy.py:390-411` · `villani/autonomous.py:53-60`
- [TODO] Indexation par **empreinte de contrat canonicalisé**, pas par identifiant fourni par le modèle.
  → `pi/packages/evals/src/vitest-evals/harness-table.ts:66,105`
- [TODO] Persistance de l'intention avant tout effet externe ; réconciliation sur chemin distinct ; état
  contradictoire bloqué avec cause.
  → `pi/packages/agent/src/harness/runtime/drive/generation.ts:132` · `pi/packages/agent/src/harness/runtime/reconcile.ts:132` · `pi/packages/agent/src/harness/runtime/restore.ts:131`
- [TODO] Satisfaction invalidée dès que l'empreinte des fichiers de l'outil change.
  → `villani/autonomous.py:1014-1042`
- [TODO] Proposition d'outil suivant à partir du `seed` et du registre, avec heuristiques déterministes
  déchargeant le modèle d'une part des propositions.
  → `villani/autonomy.py:523-631,716-722`
- [TODO] Rejet mécanique d'une proposition redondante avant toute inference : clé normalisée **avec table
  d'alias**, filtre en cascade, déduplication par priorité effective.
  → `villani/autonomous_helpers.py:9-64`
- [TODO] **La récurrence se compte, elle ne se jette pas** : un doublon incrémente son compteur, rouvre un
  item clos et élève son rang ; le vivier est déterministe, classé et **plafonné à 20 avant tout appel
  modèle** ; la fermeture d'un item se fait **sur commit, par le code** (décision 5 amendée).
  → `our/improvement_backlog.py:199-374,423-455`
- [TODO] **Filtre de pression interne** : une proposition qui *retire une gate* est rejetée par la même
  mécanique qu'une proposition redondante. *Self-started does not mean self-exempt* (décision 24).
  → `BIBLE.md:412-429`
- [TODO] Module **feuille sans dépendances** pour l'empreinte de redondance, afin que compteur et gate lisent
  la même valeur. → `our/evolution_fingerprint.py:1-42`
- [TODO] Verdict de revue **lié au hash de contenu**, fichiers de contrôle exemptés du hash de l'objet qu'ils
  gouvernent — **même primitive que la satisfaction périmée**. → `our/skill_loader.py:1-33`
- [TODO] Moteur lexical sans dépendance pour le recouvrement de termes, tolérant aux formes fléchies —
  meilleur socle que `difflib` seul pour le rejet de redondance.
  → `kilo/kilo-memory/src/recall/topics.ts:21,26-96`
- [TODO] Couche de configuration **écrite par le runtime**, distincte de celle de l'opérateur ; substitution
  de variables bornée, sans exécution de commande.
  → `kilo/opencode/src/config/managed.ts:20-68` · `kilo/opencode/src/config/variable.ts:43-118`
- [TODO] Retries dépendant du type de contrat du nœud.
  → `villani/autonomous_helpers.py:61-64`
- [TODO] Proposition d'arrêt : taxonomie fermée (`planner_churn`, `stagnation`…), raison énumérant ce qui a
  été examiné par catégorie, machine à états `discovered` → `attempted`, tâches de suivi automatiques.
  → `villani/autonomous_stop.py:7-47` · `villani/autonomous_progress.py:10-88`
- [TODO] Rapport final de campagne distinguant changements intentionnels, incidents et **préexistants**.
  → `villani/autonomous_reporting.py:77-145`

## P4 — Raccordement des composants v1

Cette phase est celle qui a éclaté : `hostside` est devenu **`lifecycle`** (verrou, launchd, custody,
garde disque) et **`broker`** (Git + Telegram). Chaque item ci-dessous appartient à l'un ou à l'autre, et le
`MODULE.md` correspondant tranche.

- [TODO] **`broker`** — Git, politique de branche et de PR, auto-merge après gate verte. *(porté de v1)*
  Produit le `RepoFact` que `verifier` consomme.
- [TODO] **`broker`** — une identité logique par effet sortant, distincte de l'identité de transport : un
  push ou un message rejoué après échec de transport ne compte pas deux fois. Décision 30.
- [TODO] LaunchAgent de réveil périodique et verrou anti-chevauchement. **Verrou à heartbeat et verrou
  breaker** plutôt que péremption par liveness de PID : deux prétendants peuvent sinon casser le verrou
  simultanément, et une section longue être évincée à tort.
  → `kilo/core/src/util/flock.ts:25-37,103-240`
- [TODO] Rédaction de secrets par motifs nommés, appliquée **avant persistance** — nos JSONL ne sont jamais
  effacés, et deux frontières sortent de la machine.
  → `kilo/kilo-memory/src/capture/redact.ts:2-111`
- [TODO] Proposition d'arrêt comme **objet persistant à cycle de vie**, pas comme prompt bloquant.
  → `kilo/opencode/src/question/index.ts:28-32,90-124`
- [TODO] Notifications Telegram bidirectionnelles, idempotentes. *(porté de v1)*
- [TODO] Enveloppe de commande à id/cible/résultat discriminé ; **une commande tardive ne peut pas viser la
  mission suivante**.
  → `pi/packages/protocol/src/protocol.ts:40,49`
- [TODO] Arrêt du **groupe** de processus et nettoyage des descendants suivis.
  → `pi/packages/coding-agent/src/utils/shell.ts:206,216`
- [TODO] **Aucune politique de redémarrage automatique** : le lanceur possède son fusible et un arrêt de
  panique reste un arrêt jusqu'à relance explicite par l'opérateur. Un seul chemin de lancement, verrou
  d'instance partagé. → `pk/systemd/ouroboros.service:1-24` · `pk/systemd/README.md:1-40`
- [TODO] Custody de processus par empreinte **stricte** `(pid, start_time, cmd_sha256)` ; scopes `task` /
  `session` / `daemon` distincts. → `our/process_custody.py:12-19,233-560`
- [TODO] Vérification de démarrage émettant **un seul événement JSONL typé** portant chaque contrôle et un
  verdict global ; tripwire de croissance des stores chauds.
  → `our/agent_startup_checks.py:710-929`
- [TODO] Telegram : deux erreurs typées (rejet explicite vs absence de réponse), backoff **monotone partagé**
  remis à l'initial par tout tour réussi, découpe en **unités UTF-16**.
  → `sk/telegram/lib/telegram_api.py:24-113`
- [TODO] **Avertir d'une syntaxe de template probablement erronée avant l'appel modèle** — une session perdue
  sur une accolade mal fermée est une session perdue. → `swe/sweagent/utils/jinja_warnings.py:4`
- [TODO] **Timeout distinct par commande de setup**, pas un timeout global unique ; blocklist de commandes
  interactives et blocklist exacte contre les shells imbriqués.
  → `swe/sweagent/environment/swe_env.py:130` · `swe/sweagent/tools/tools.py:41,56`
- [TODO] Frontières d'import testées comme contrats d'architecture, dépendances déclarées, versions figées.
  → `pi/scripts/check-entry-graphs.mjs:33` · `pi/scripts/check-runtime-deps.mjs:11` · `pi/scripts/check-pinned-deps.mjs:5`
- [TODO] **Verrou de mission par `pid` + heure de démarrage du processus** ; `processStartId` illisible ⇒
  détenteur présumé vivant ; récupération d'un verrou périmé par **renommage atomique** ; `release()`
  idempotent ne supprimant que si le token correspond encore.
  → `prime/ca/core/session-lease.ts:36-60,160-263`
- [TODO] **Réveil : `nextRunAt` avancé à la réclamation, pas à la fin d'exécution** ; ticks manqués
  **coalescés, jamais empilés** ; dispatches interrompus réconciliés au démarrage ; pas de tick périodique
  mais un seul timer vers le prochain job dû.
  → `prime/ca/core/cron-jobs.ts:758-775,1053-1077,1591-1620`
- [TODO] Politique de délivrance d'un réveil **pendant une mission active** : `steer` (interrompre) vs
  `follow_up` (attendre la fin). → `prime/ca/core/cron-jobs.ts:25-27,1350-1378`
- [TODO] Journal des processus orphelins apparié par `pid` + heure de démarrage.
  → `prime/ca/core/orphan-process-journal.ts:24-80`
- [TODO] **Politique d'exposition réseau (décision 27)** : prédicat `is_public_address` **unique et partagé**
  par le bind, l'affichage et la politique d'outils ; détection couvrant **résolution DNS et IP littérale** ;
  **binds wildcard normalisés avant évaluation** ; énumération des adresses n'incluant jamais aveuglément
  loopback ni interfaces hôte-only. **[ÉCARTÉ 06:09] — `observatory` binde `127.0.0.1` en dur et aucun chemin
  de code ne peut binder ailleurs : l'interdiction est dans le type, pas dans la configuration. La politique
  s'écrira le jour où l'ouverture au LAN sera décidée.** ~120 L.
  → `uns/unsloth_cli/_tool_policy.py:19,108,165` · `uns/studio/backend/lan_access.py:72,213`
- [TODO] Cycle de vie d'un service local : **readiness observable sous deadline, jamais le spawn** ; sur
  échec de bind, **tous les sockets partiellement ouverts fermés et la cause conservée** ; état de confiance
  suivant l'état réel du listener ; arrêt idempotent.
  → `uns/studio/backend/cloudflare_tunnel.py:354,507,516` · `uns/studio/backend/lan_access.py:350,370,423`
- [TODO] **Jeton d'admission/génération à l'arrêt** pour qu'une ancienne instance ne tue pas la nouvelle —
  deux réveils launchd rapprochés dont le premier est lent à mourir.
  → `uns/studio/backend/cloudflare_tunnel.py:930` · `uns/unsloth_cli/commands/start.py:1191`
- [TODO] **Garde des répertoires système** : liste nommée de chemins de configuration protégés contre toute
  écriture, indépendante du prédicat de workspace (décision 12 amendée).
  → `uns/unsloth_cli/_system_dir_guard.py:1`
- [TODO] Écriture privée à permissions restrictives pour secrets et tokens ; clé testée contre le serveur
  **avant** d'être mémorisée. → `uns/unsloth_cli/commands/start.py:1498,1507,1569`
- [TODO] **Registre de hooks d'arrêt exécutés à toute sortie** ; **leases périmées libérées au démarrage**,
  pas à l'arrêt ; port libre trouvé par **bind explicite sur loopback**, plusieurs ports vérifiés avant
  démarrage ; clé d'API générée **côté hôte, jamais par le modèle**.
  → `oh/scripts/dev-process-utils.mjs:131` · `oh/scripts/dev-safe.mjs:72,218,266,1177`
- [TODO] **Fencing du cycle de vie (décision 16 amendée)** : claim conditionnel où une seule transition
  réussit, **heartbeat à perte de propriété explicite**, classification de péremption à quatre causes où **la
  durée maximale l'emporte sur le heartbeat**, et **réconciliation qui ne réapplique une transition que si
  l'état observé n'a pas changé**.
  → `lf/packages/shared/src/in-app-agent/server/runLifecycle.ts:37,64,673,702`
- [TODO] **Verrou à trois états** — acquis / détenu par autrui / **indisponible**, où indisponible **bloque** ;
  libération et renouvellement **conditionnés au jeton de propriétaire**.
  → `lf/worker/src/utils/RedisLock.ts:4,55`
- [TODO] **Validation de `Host` et `Origin` avant traitement**, sans échappatoire wildcard ; **l'absence
  d'`Origin` n'est pas une preuve de confiance**. → `lf/web/src/features/mcp/server/security.ts:70`
- [TODO] Plafond d'échecs consécutifs par nœud, dès le socle et non après incident.
- [ÉCARTÉ] Politique de commande : allowlist par préfixe de tokens, matching conscient des opérateurs,
  arité des commandes shell, découpage de ligne shell, décision accompagnée de sa raison. **Le modèle n'émet
  aucune commande — il n'y a rien à autoriser. Son code, lui, est exécuté : c'est `sandbox` (P7bis) qui
  défend, pas la permission.** ~200 L, réactivables avec le mode `agentic`.
  → `villani/permissions.py:51-233` · `kilo/opencode/src/permission/arity.ts:1-161`
- [TODO] Environnement d'exécution expurgé des chemins privés du harness, et diagnostiqué.
  → `villani/command_environment.py:32-48,153-260`

## P5 — Dashboard

- [TODO] Agrégat reconstruit depuis les seuls JSONL, indexé en mémoire au démarrage et suivi par mtime.
  → `villani/trace_summary.py:439-757` · `pi/packages/agent/src/harness/session/in-memory-storage-state.ts:62`
- [TODO] Registre de vérification par mission construit depuis **les seuls faits d'exécution faisant
  autorité**, jamais une reformulation ; projection portant le compte omis et un hash durable de l'ensemble
  complet. → `our/outcomes.py:1387-1525` · `our/_outcome_receipts.py:529-670`
- [TODO] Rendu texte compact de l'état complet, **réutilisé par CLI, Telegram et dashboard** — une seule vue,
  trois transports. → `sup/state.py:772-917`
- [TODO] Aplatissement de l'arbre en lignes conservant parenté et branche active ; état de repli séparé des
  données métier ; **échappement des traces avant rendu HTML**.
  → `pi/packages/coding-agent/src/modes/interactive/components/tree-selector.ts:27,121` · `pi/packages/coding-agent/src/core/export-html/ansi-to-html.ts:63`
- [TODO] Agrégat **validé contre un contrat** avant d'être servi, et versionné par la logique qui l'a produit.
  → `villani/trace_summary.py:11-13,777-820`
- [TODO] Reconstruction des appels d'outils depuis les événements bruts, signalant ses propres anomalies.
  → `villani/trace_summary.py:196-427`
- [TODO] Manifeste d'artefacts par run et digest bon marché pour les listes.
  → `villani/trace_summary.py:758-776` · `villani/event_recorder.py:35-59`
- [TODO] Toute écriture d'observabilité encapsulée : une panne du recorder ne casse jamais la mission.
  → `villani/debug_recorder.py:64-72`
- [TODO] Résumé final systématique en fin de run, statut et raison de terminaison compris.
  → `villani/debug_recorder.py:414-446`
- [TODO] **Usage propre du nœud vs usage total du sous-arbre** ; statut de nœud **dérivé de la branche,
  jamais stocké** ; arbre reconstruit depuis le disque sans le processus vivant.
  → `prime/ca/core/context-tree.ts:76-105,161-197,250-320`
- [TODO] **Arbre résistant aux IDs dupliqués** — sinon un doublon crée un graphe multiparent explosif ;
  parcours itératif avec ensemble `visited` ; **durée du nœud distincte de l'enveloppe temporelle du
  sous-arbre**, jamais une somme de durées concurrentes.
  → `lf/web/src/features/traces/fns/treeBuilding.ts:111,164` · `lf/web/src/features/traces/fns/getSubtreeDurationOverflowMs.ts:23`
- [TODO] **Une lecture coûteuse est subordonnée à un périmètre** — nœud, mission ou intervalle exigé avant
  gros IO ; projection compacte par défaut, payloads **chargés à la demande** ; `limit+1` pour `hasMore` et
  curseur opaque validé.
  → `lf/web/src/features/mcp/server/observations/schema.ts:137,182` · `…/tools/listObservations.ts:385,443`
- [TODO] **Budget de rendu en nœuds distinct du budget en caractères** ; sérialisation unique réutilisée pour
  taille, aperçu et téléchargement. → `lf/web/src/features/traces/components/IOPreview/fns/jsonViewSizeGate.ts:59,78`
- [TODO] **Ne jamais corriger silencieusement une anomalie temporelle** : une fin antérieure au début se
  conserve et se montre. → contre-exemple `lf/worker/src/services/IngestionService/index.ts:1211`
- [TODO] Parseur de journal **injecté par le consommateur**, qui décide ce qu'il rejette et ce qu'il saute.
  Un même journal sert plusieurs vues. → `prime/ca/core/event-log.ts:73-111`
- [TODO] **Rejouer une mission enregistrée sans rappeler le modèle** pour les étapes déjà validées, avec une
  configuration de replay **indépendante du runner original**.
  → `swe/sweagent/run/run_replay.py:46,66`
- [TODO] Comparer deux campagnes en **distinguant mêmes résultats et divergences** ; identifier les runs
  inachevés en **dry-run par défaut** ; résumé de campagne sans charger les détails dans le contexte.
  → `swe/sweagent/run/compare_runs.py:8,69` · `swe/sweagent/run/remove_unfinished.py:13` · `swe/sweagent/run/quick_stats.py:16`
- [TODO] **Résultat absent chargé comme état lisible plutôt qu'exception opaque** ; statut **déduit des
  artefacts présents**. → `swe/sweagent/inspector/server.py:188,205`
- [TODO] **Rédaction systématique des tails de log avant projection** à l'utilisateur ou au modèle, queue
  bornée en lignes ; affichage de progression **séparé du journal durable** — ne pas confondre UI et preuve.
  → `uns/unsloth_cli/commands/start.py:900,1145,1152`
- [TODO] **Distinguer erreur différée côté serveur, corps incomplet et erreur HTTP** dans l'affichage ; un
  refus porte une **raison courte et stable, exploitable dans un finding**.
  → `uns/unsloth_cli/_inference.py:69,882`
- [TODO] Statuts terminaux **énumérés avant agrégation**, prédicat de succès **distinct** du prédicat
  d'échec, état métrique vide explicite plutôt que des `undefined`, message d'incompatibilité **stable et
  actionnable**.
  → `oh/src/manifests/automation-insights.ts:81,86,144` · `oh/src/stores/metrics-store.ts:21` · `oh/src/api/agent-server-compatibility.ts:302`
- [TODO] Agréger plusieurs sondes d'état **en parallèle** puis restituer un snapshot cohérent ; endpoint de
  statut read-only **sans jamais exposer le token de contrôle**.
  → `uns/studio/backend/mcp_server.py:263` · `uns/studio/backend/lan_access.py:479`
- [TODO] Reprise du frontend React de v1 et de son design.
- [TODO] Vue d'arbre : profondeur, statut par nœud, critère retenu et cause de rejet.

## P6 — Auto-extension

- [TODO] Config MCP en couches, dont une couche `managed` écrite exclusivement par le harness.
  → `villani/mcp.py:11-35`
- [TODO] Enregistrement d'un outil `verified` dans la couche `managed`, mise à disposition aux nœuds suivants.
- [TODO] **`reload(server)` — un outil vérifié devient appelable dans la mission en cours**, sans redémarrage,
  sous verrou par nom et génération remplacée atomiquement. Rend la question expérimentale 4 mesurable dans
  une seule mission. → `prime/rt/mcp.py:397-416,483-491`
- [TODO] Environnement d'un serveur MCP réduit à une **allowlist** de variables ; stderr en tail borné,
  ANSI strippé et **redacté** — une valeur de configuration courte fait supprimer tout le stderr.
  → `prime/rt/mcp.py:28,37-95,249-261`
- [TODO] Installation d'outil **par hash de `pyproject.toml`**, ordre topologique des dépendances, fichier de
  version dans le venv portant l'identité du runtime et la liste des outils.
  → `prime/ca/core/kernel/bootstrap.ts:554-560,686-712,738-821`
- [TODO] Nom d'outil = **nom du répertoire parent**, `[a-z0-9-]`, ≤ 64 caractères ; **description vide ⇒ outil
  non chargé** ; métadonnées seules au prompt de démarrage, contrat complet chargé à la demande.
  → `prime/ca/core/skills.ts:122-161,443-475`
- [TODO] **Fabrique FastMCP unique à liste d'outils explicitement enregistrée** ; bearer token **exact, non
  vide et ASCII** ; **clamp des entiers fournis par le client avant appel de route** ; outil de statut
  read-only comme sonde de santé ; **outils de lecture séparés des mutations** ; gate de schéma validant une
  requête **sans lancer le job**.
  → `uns/studio/backend/mcp_server.py:20,70,77,86,97,126,166`
- [TODO] Registre **typé, enregistré explicitement par famille** plutôt que découvert dynamiquement depuis le
  modèle. → `uns/unsloth/registry/registry.py:20,56`
- [TODO] Découverte de capacités par `SKILL.md` à frontmatter, si le besoin se confirme.
  → `villani/skills.py:16-33`
- [TODO] Mesure de la réutilisation effective, indicateur de la question expérimentale 4.

## P7 — Campagne

- [TODO] Rédaction du `seed` et création du dépôt Git de la campagne.
- [TODO] Gate complète du socle avant le premier réveil autonome.
- [TODO] Premier réveil supervisé, puis activation périodique.
- [TODO] Collecte et revue des dix premières missions ; révision de la borne murale.

## P8 — Discipline de dépôt (décision 25)

Ne sert ni le socle ni la campagne : elle sert la **relisibilité**, qui est la contrainte réelle d'un modèle
à 16 k et d'un opérateur seul.

- [TODO] **Ratchet de taille, désormais nécessaire et non plus confortable** : manifeste généré, dette
  shrink-only, bande à justification obligatoire et immuable, comptes d'octets décroissants, correspondance
  exacte avec l'inventaire vivant. La cible globale est passée à **~6 000 lignes** le 06:09 après comptage
  des portages ; **un plafond relevé ne mord plus par lui-même**, et la contrainte s'exerce maintenant sur
  **la cible inscrite dans chaque `MODULE.md`**, qui ne peut que descendre. Décision 25 amendée.
  → `our/review.py:19-26,292-830` · `our/size_ratchet_manifest.py`
- [TODO] Validation **paire** (base contre tip) plutôt que par archéologie d'historique.
  → `our/review.py:540-602`
- [TODO] Emplacements canoniques **nommés** dans `PROJECT.md`, et la règle « quand un fait déménage, toutes
  ses références bougent dans le même commit ». → `BIBLE.md:564-622`
- [TODO] Anti-pattern **identité dérivée du contenu** appliqué aux enregistrements créés par le harness
  (missions, nœuds, propositions) : identité capturée à la création, passée par valeur.
  → `od/DEVELOPMENT.md:127-180`
- [TODO] Opérations exemptes de gate : un rollback mécanique restaure un état déjà vert ; le soumettre aux
  gates piégerait le harness avec du code cassé qu'il ne peut pas annuler. → `BIBLE.md:707-726`

## P9 — Auto-amélioration (décision 26)

À placer **après P6**. `enabled: false` au socle ; activation après mesure sur les dix premières missions.

> **Le magasin n'est plus ici.** Il appartient à `campaign` et se construit en **P0** (décision 26
> amendée) : un fichier, un propriétaire. Ce qui reste en P9 est la **politique** — proposer et accepter —
> soit `refinery/propose.py` et `refinery/gate.py`, ~150 lignes. Écrire dans la famille `memory` ne dépend
> pas de cette phase (décision 31) ; **seul le fait de s'en servir pour se réécrire l'attend.**
- [TODO] Historique de raffinement en JSONL append-only, **séparé du fichier d'état**, sur le substrat
  crash-safe de P0. → `prime/ca/core/refinement/refinement.ts:374-400`
- [TODO] Application d'une proposition : validation **par cas fermés**, edit invalide enregistré et **non
  fatal**, détection de conflit par état de base capturé avant l'appel modèle.
  → `prime/ca/core/refinement/refinement.ts:673-714,716-811,735-749`
- [TODO] **Rollback par reconstruction inverse** depuis les `before`/`after`, en ordre inverse.
  → `prime/ca/core/refinement/refinement.ts:813-845`
- [TODO] **Immuabilité de la politique de base** : un edit visant l'entrée de base est refusé mécaniquement.
  Trois lignes qui séparent « s'améliore » de « se détruit ».
  → `prime/ca/core/refinement/refinement.ts:680-682`
- [TODO] Injection dans le contexte de nœud, **bornée par famille**, avec compteur de débordement et les cinq
  derniers raffinements visibles — l'agent voit son propre historique d'amélioration.
  → `prime/ca/core/refinement/refinement.ts:429-520` · `prime/rt/harness.py:722-769`
- [TODO] Proposition **déterministe d'abord** (`plan_refinement`, zéro appel modèle) ; appel modèle en dernier
  recours, en **mode non-raisonnant**, budget de sortie dérivé du modèle.
  → `prime/rt/harness.py:705-720` · `prime/ca/core/refinement/refinement.ts:199-205,921-926`
- [TODO] **Gate d'effet** *(neuf — n'existe dans aucune des cinq sources)* : une entrée `memory` ou `prompt`
  reste en `shadow` tant qu'elle n'a pas démontré un effet mesurable sur le taux de nœuds verts. C'est le
  mutation-check transposé du code vers le contexte.
- [TODO] `evidence` d'un événement de raffinement = **identifiant de nœud + verdict d'invariant**, jamais la
  rationale générée.
- [DONE] Fusion de la famille `skill` avec `registry.json` — **tranchée le 06:09** : ce n'est plus
  une fusion à faire mais un **objet unique dès P0**, propriété de `campaign`. L'entrée porte `version`, les
  horodatages, `source` et l'historique, plus notre péremption par empreinte.
- [TODO] **Label mobile séparé de la version immuable** : le contenu est versionné et jamais modifié, et
  **seul le déplacement du label `active` est soumis à la gate d'effet**. Version créée **avec ses
  dépendances publiées ensemble**, versions réellement résolues tracées, graphe borné en cycles et profondeur.
  → `lf/web/src/features/prompts/server/utils/updatePromptLabels.ts:3` · `…/actions/createPrompt.ts:93` · `lf/packages/shared/src/server/services/PromptService/index.ts:242`
- [TODO] **Clé de cache typée distinguant label et version** — sinon la version `2` et le label `"2"`
  collisionnent. → `lf/packages/shared/src/server/services/PromptService/index.ts:204`

## P7bis — Confinement d'exécution (décision 21)

Conditionne l'exécution autonome non supervisée, pas le socle. **Remonte en P2** si le premier réveil
supervisé montre que le `verifier` exécute du code produit touchant des chemins inattendus.

- [TODO] Profil `sandbox-exec` de base et composition des racines lecture / écriture / réseau ; détection de
  disponibilité avant de s'y fier.
  → `kilo/kilo-sandbox/src/seatbelt-base.ts:1-4` · `kilo/kilo-sandbox/src/seatbelt.ts:34-73` · `kilo/kilo-sandbox/src/profile.ts:1-33`
- [TODO] Garde in-process sur chaque écriture, **refus des descripteurs de fichier inscriptibles**, en
  complément du sandbox OS.
  → `kilo/kilo-sandbox/src/filesystem.ts:107-230`
- [TODO] Arité des commandes shell et découpage d'une ligne en commandes, opérateurs et substitutions
  traités explicitement.
  → `kilo/opencode/src/permission/arity.ts:1-161` · `kilo/opencode/src/tool/shell.ts:280-285,387-457`
- [TODO] **Politique réseau du profil : refus par défaut.** Le code produit exécuté sous invariant n'a aucune
  raison légitime d'ouvrir une socket (décision 21 amendée).
  → `kilo/opencode/src/kilocode/sandbox/network.ts:13-23`

## Différé — mode `agentic`

Non implémenté au socle. Activé seulement si le mode `direct` plafonne, et avec la mesure qui le justifie.

- [TODO] Rôles de sous-agent avec allowlist d'outils, droit d'écriture et exigence de preuve explicites ;
  brief transmettant les faits établis **et ce qui a été écarté**.
  → `villani/subagent_runtime.py:19-40` · `villani/subagents.py:22-27`
- [TODO] Exécuteur de feuille LangGraph + `langchain-mcp-adapters`, bindant les outils déjà construits.

## Études de sources — 06:09

- [DONE] Extraction de Langfuse : [`resources/langfuse.md`](../resources/langfuse.md), **105 mappages**
  sur les neuf modules, avec priorités, adaptations, exclusions, tests source et carte de couverture.
  Références locales vérifiées ; suggestions non encore absorbées dans les décisions d'implémentation.


## Maintenance transverse — 11:09

- [DONE] Rendre la collecte globale obligatoire et définir le rôle transverse dans AGENTS § 14,
  avec reprise dans `tests/STATE.md` et propositions dans `tests/git.md` ; miroir CLAUDE synchronisé.
- [DONE] Mutualiser chargeur de doubles et scanner AST ; éprouver le balayage réel par injections
  sur copies, les chemins homonymes et la divergence des signatures de chaque contrat existant.
- [DONE] Fixer l’unité de lignes sans augmenter les cibles ; aligner les onze STATE sur des mesures
  et empreintes, avec plafonds explicites pour les six dépassements persistants.
- [DONE] Corriger les exclusions Git : documents Markdown visibles, caches et code tiers ignorés.
- [DONE] Valider la suite racine dans Python 3.12.9 / pithos : **1 286 passed, 3 skipped, 7 warnings en 34,59 s**.
- [TODO] Humain : exécuter les propositions de `tests/git.md`, notamment le retrait de l’index des
  **27 caches suivis** et l’ajout des documents désormais visibles. Aucun Git d’écriture exécuté.
- [DONE] Jalon « premier vert » démontré le 15:09 dans trial-25ugxn94 ; les autres livraisons
  métier restent suivies dans leurs STATE. Aucun module déclaré fini sur ce seul résultat.

## Chaîne de faits vers le premier vert — 12:09

- [DONE] Publier SourceFact et RepoFact canoniques dans kernel, avec octets bornés et complétude explicite.
- [DONE] Raccorder workspace et broker aux faits publics, avec doubles conformes.
- [DONE] Implémenter Verifier.run : croisement pur avant exécution, double gate, reçu lié aux faits,
  budget restant et refus de toute attestation sans acquittement durable.
- [DONE] Livrer engine/select.py : sélection avec raisons, dépendances et importeurs depuis l'index injecté.
- [DONE] Vérifier dans pithos/Python 3.12.9 : **1 367 passed, 3 skipped, 7 warnings en 37,10 s** ;
  tests broker **114 passed en 1,99 s** après refus des sockets locales par la sandbox.
- [DONE] Humain : arbitrer la contradiction `new_source` / contrainte dure n°1 — code candidat autorisé le 12:09, critères et entrées sous contrôle du harness.
- [TODO] Engine : premier walk transactionnel sur doubles, rollback sur rejet ou reçu absent,
  finalisation des verts à la borne murale et baseline de mission ; puis démonstration réelle avec Ollama.
- [TODO] Définir le binding outil → modèle Pydantic pour schema_conform et le propriétaire du polling Telegram.

Les cases ci-dessus livrent des unités ; elles ne déclarent aucun module fini et ne cochent pas le jalon réel.

## Banc audio et nano-étape — 13:09

- [DONE] Autoriser et borner le schéma de code candidat ; conserver requête et génération intégrales.
- [DONE] Publier l'admission pure du critère avant appel modèle ou effet workspace.
- [DONE] Livrer run_attempt avec double conforme : transaction, faits, reçu et CAS ; rollback sur rejet.
- [DONE] Adapter l'idée du visualiseur dans experiments/visualizer : trois trajectoires mesurées sur disque,
  bridge/Git simulés ; cinq régressions permanentes, **1 402 tests verts** dans la suite complète.
- [DONE] Sonder le modèle Ollama réel ; conserver la troncature initiale puis le critère conforme.
- [DONE] Humain : dépôt dédié initialisé, HEAD 57e47c5 constaté le 13:09.
- [DONE] Trial réel trial-44kcg6ig conservé : tautology, 0 reçu, rollback exact, 5 gates.
- [DONE] Composer walk/flow avec reprise, finalisation broker et worker lifecycle ; preuve intégrée sur Git/Prefect réels, modèle simulé (14:09).
- [TODO] Définir domaine de tableaux et relations avant les essais bass/mid/treble et lissage.

Le trial du 13:09 valide le schéma candidat mais refuse sa vérification faute de sensibilité aux mutants.
Il ne valide ni la mission composée livrée le 14:09, ni le contrat produit complet du visualiseur.

## Observabilité et références J–K — 13:09

- [DONE] API de lecture des essais, état publié, refus, sources et gates sans reçu ; aucun brut réécrit.
- [DONE] Dashboard React/Vite local : arbre, preuves, contexte, outils, chronologie et artefacts ; 8 tests web verts.
- [DONE] Capacité/provenance/durée et rapports de vérification tracés pour les prochains appels.
- [DONE] Omissions de ContextPacket visibles et comptées dans son budget estimé.
- [DONE] Contrôle documentaire de 20 interfaces livrées sur 11 modules ; prévu distingué de livré.
- [DONE] GVS5H/Graphify catalogués sélectivement, avec les limites et reprises écartées.
- [DONE] Dashboard déclaré fonctionnel et terminé pour le moment par l’utilisateur ; aucune nouvelle vérification visuelle revendiquée par l’agent (14:09).
- [TODO] Relier ContextPacket et la mesure de non-progrès par faits au marcheur complet, lors de sa composition.


## Entrée Pithos — 13:09

- [DONE] `src/main.py` partage les arguments du banc et affiche projet, inférence, travail et activité.
- [DONE] Conserver le JSON hors terminal et vérifier l'interruption après splice en pseudo-terminal.
- [TODO] Raccorder les futurs tours du marcheur lorsque son contrat de reprise sera livré ; le TUI
  actuel expose les événements de la nano-étape disponible.


## Composition de mission — 14:09

- [DONE] GreenFinalizer : reçu durable, intention avant commit, deadline commune, interrogation avant rejeu.
- [DONE] Worker lifecycle : admission durable, verrou vivant préservé, groupe récolté, reprise des orphelins.
- [DONE] CLI mission.py : même --run à la reprise, budget ancré avant spawn et sonde, serveur Prefect explicite.
- [DONE] Réconcilier un leader zombie sans signal, après constat natif d'absence de membres vivants (15:09).
- [DONE] Vérifier coupure après splice, restauration à la reprise et commit sans acquittement sur runtime local.
- [DONE] Consolider les contrats Walker/MissionRunner/GreenFinalizer et la frontière flow dans les corpus partagés (15:09).
- [DONE] Reproduire et expliquer les trois mutants survivants du trial-44kcg6ig ; contre-exemple [0,2] à branches accepté par idempotence, limites documentées (15:09).

Suite complète : **1 568 passed, 3 skipped, 7 warnings en 103,09 s**. Le modèle reste simulé dans
la preuve de composition ; aucune nouvelle expérience Ollama, aucun push ni PR.


- [DONE] **Blocage de clôture du 14:09 résolu** : port verifier relié aux gardiens lifecycle,
  groupes enregistrés avant admission ; vraie gate coupée et orphelins récupérés avant reprise.
  La contre-preuve initiale reste dans les STATE ; CLI réouverte et reprise effective testée.

## Projection exacte — 15:09

- [DONE] Extension explicitement autorisée : relation unaire fermée unit_projection sur floats_finite.
- [DONE] Identité sur [0, 1], saturation, sortie numérique bornée et idempotence ; aucun seuil fourni par le modèle.
- [DONE] Comparaisons exactes et onze exemples fixes ; deux écritures correctes acceptées, 19 variantes incorrectes refusées.
- [DONE] Nouveaux trial/mission raccordés ; critères et reçus historiques inchangés, relation affichée à la reprise.
- [DONE] Rejouer les sources archivées : nouvelle double gate verte, 44 fichiers historiques inchangés.
- [DONE] Premier vert Ollama trial-25ugxn94 : 44,898 s, trois gates, un reçu effect confirmed, fichier réellement modifié.
- [TODO] Mission composée avec Ollama sur un nouveau dépôt seed ; le trial vert ne finalise pas de commit Git.
