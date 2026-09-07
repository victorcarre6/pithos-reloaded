# `broker` — la seule sortie de données

> **Lis [`AGENTS.md`](../../AGENTS.md) avant de commencer.** Ce fichier est ton contrat complet : tu ne
> devrais pas avoir besoin d'ouvrir `docs/`. Ton point d'entrée exact est la rubrique « Prochaine action » de
> [`STATE.md`](STATE.md), à côté de ce fichier.
>
> **Tu ne commites, ne pousses et ne merges jamais.** Tes commits se *proposent* dans [`git.md`](git.md),
> avec les `ga`/`gcmsg` exacts — voir [`AGENTS.md`](../../AGENTS.md) § 7.

**Cible** : ~550 L · réemploi assumé de v1 · ratchet **shrink-only**
**Dépend de** : `kernel`, `journal`.
**Niveau de dépendance** : 2.
**Stack** : `subprocess` + CLI `gh` · `httpx` pour Telegram. **Pas de GitPython.**

## 1. Autorité

**`broker` est le seul module par lequel une donnée quitte la machine.** C'est la troisième règle d'import du
projet, et elle existe pour une raison précise : elle rend la **contrainte dure n°5** — souveraineté —
mécaniquement vérifiable par un test de graphe d'imports, au lieu d'une discipline de relecture.

Le nom vient de `PROJECT.md`, qui parlait déjà de composants « déjà brokerisés ».

## 2. Interface publique

```python
# git.py
def repo_fact(repo: Path) -> RepoFact:
    "git diff + git status --porcelain=v1 -z -uall. Le fait typé que verifier consomme."
def commit(repo: Path, paths: list[Path], message: str) -> str: ...
def open_pr(repo: Path, branch: str, body: str) -> PullRequest: ...
def automerge(pr: PullRequest) -> None:
    "Uniquement après gate verte. L'humain est portier de la FIN de campagne, pas des incréments."

# telegram.py
def notify(text: str, idempotency_key: str) -> bool: ...
def poll(offset: int) -> tuple[list[Command], int]: ...   # offsets persistants
```

**Cinq commandes entrantes** : `/status`, `/latest`, `/pause`, `/stop`, `/answer`.

## 3. Interdits

- **N'importe jamais `engine`, `campaign`, `verifier`, `workspace`.** `broker` rend des faits et envoie des
  messages ; il ne connaît pas la boucle.
- **Aucun autre module n'ouvre un socket sortant.** Si tu as besoin d'un accès réseau ailleurs, la conception
  est en cause : consigne-le.
- ⚠️ **Ne publie que des fichiers explicitement désignés** !
  → Jamais `git add -A`, jamais un glob implicite. Le dépôt de campagne est écrit par un modèle.
- **N'assimile jamais un checkpoint Git à un commit.** Deux objets, deux sémantiques.
- **Valide les arguments Git avant de les passer à la CLI.**

## 4. Le réemploi est assumé

Le broker Git de v1 fait **225 lignes, a produit dix PR réelles**, et sa valeur est justement de
*restreindre* les opérations qu'on veut fermer. Telegram bidirectionnel de v1 fonctionnait : offsets
persistants, idempotence des requêtes, allowlist utilisateur.

**On porte, on ne réécrit pas.** Ce module est le seul du projet où la recommandation de couper a été
explicitement refusée, et le raisonnement tient : du code éprouvé vaut mieux qu'une réécriture élégante.

**Deux conséquences à tenir**, et elles sont dans ton périmètre :

1. **La boucle de polling Telegram est un processus à cycle de vie propre.** Elle est donc gérée par
   `lifecycle` comme tout autre processus — custody, arrêt confirmé, journal des orphelins. **Ne l'écris pas
   comme un thread daemon oublié.**
2. **`/pause` et `/stop` doivent atteindre le marcheur.** Le chemin existe : c'est l'`InterruptController` de
   `engine` — premier signal interrompt, second quitte. `broker` **émet** le signal, il ne touche pas
   l'arbre.

## 5. L'identité d'un effet sortant

**Décision 30 — l'identité logique n'est pas l'identité de transport.**

| Identité | Nature | Au retry |
|---|---|---|
| **résultat** | déterministe sur `(mission, nœud, tentative, effet)` | **stable** |
| **transport** | renouvelée à chaque tentative | **change**, et **exclue de toute comparaison** |

Un push Git ou un message Telegram rejoué après un échec de transport porte **la même identité de résultat**
et **une identité de transport neuve**. Il ne compte pas deux fois.

**Et l'ordre d'écriture est la protection** : les métadonnées de provenance de l'hôte s'écrivent **après** la
charge utile, jamais avant.

## 6. Persister l'intention avant l'effet

C'est la brique qui rend la contrainte dure n°4 réellement tenable. Sans elle, **une reprise ne peut pas
distinguer *non commencé* d'*effet inconnu***, et rejouer devient un pari.

```text
1. écrire l'intention (durable)     "je vais pousser la branche X"
2. exécuter l'effet
3. écrire le résultat (durable)     "poussé, sha Y"
```

Une reprise qui trouve 1 sans 3 est en **effet inconnu** : elle interroge l'état distant avant de rejouer,
jamais l'inverse.

## 7. Contenu

| Fichier | Contenu | ~L |
|---|---|---:|
| `git.py` | `subprocess` + `gh`, branche, PR, auto-merge, `RepoFact`, préflight dépôt sale | 230 |
| `telegram.py` | notifications sortantes, polling, offsets persistants, allowlist, 5 commandes | 220 |
| `identity.py` | identité de résultat vs identité de transport, idempotence | 60 |
| `intent.py` | persistance de l'intention avant effet, réconciliation à la reprise | 40 |

## 8. Critères de socle que ce module rend verts

- Contribue à **la contrainte dure n°5** : c'est le seul module d'egress, et le test de graphe d'imports le
  garde.
- **Republier un résultat déjà calculé ne le compte jamais deux fois** : l'identité logique du résultat est
  déterministe, l'identité de transport est renouvelée à chaque tentative.
- **Une reprise distingue non commencé / effet inconnu / résultat enregistré** et n'exécute jamais un effet
  externe deux fois sans interrogation préalable.
- **Aucune régression du produit n'atteint `main` sans être détectée par la gate de régression** —
  l'auto-merge ne se déclenche qu'après un verdict vert.

## 9. Le double

`tests/doubles/broker.py` — un dépôt Git **simulé** (dict de fichiers + historique en liste) et un Telegram
en mémoire (file de messages sortants, file de commandes entrantes). Il doit savoir jouer :

- un `RepoFact` cohérent avec un `FileFact` donné, **et un `RepoFact` qui le contredit** — c'est ce dernier
  cas qui teste la preuve d'effet croisée de `verifier` ;
- un échec de transport suivi d'un retry, pour vérifier que le résultat ne compte qu'une fois ;
- un dépôt sale au préflight.

## 10. Fini quand

- [ ] `repo_fact` rend les **deux côtés** d'un rename, et une ligne malformée de `--porcelain` est une
      erreur, pas un silence.
- [ ] Un rejeu après échec de transport ne compte **pas deux fois** — test explicite sur l'identité de
      résultat.
- [ ] Une reprise trouvant l'intention sans le résultat **interroge** l'état distant avant de rejouer.
- [ ] `commit` ne publie **que** les chemins explicitement désignés — test qui salit le dépôt et vérifie que
      les fichiers non désignés ne sont pas commités.
- [ ] Le préflight refuse de démarrer sur un dépôt sale, avec la liste des fichiers en cause.
- [ ] Les arguments Git sont validés avant passage à la CLI — test d'injection.
- [ ] Les offsets Telegram sont **persistants** : un redémarrage ne rejoue pas les commandes déjà traitées.
- [ ] Une commande d'un utilisateur hors allowlist est **ignorée et journalisée**.
- [ ] `/pause` et `/stop` atteignent l'`InterruptController` sans que `broker` touche l'arbre.
- [ ] La boucle de polling s'arrête proprement sur signal, avec état de sortie confirmé par `lifecycle`.
- [ ] Le backoff est **monotone et partagé** entre le poller et le notifier.
- [ ] `tests/boundaries/` confirme que **seul** `broker` ouvre un socket sortant.

## 11. Pièges connus

- **Découpe le texte Telegram en unités UTF-16, pas en caractères** — la limite de l'API est en UTF-16, et
  un emoji coupé en deux casse le message.
- **Deux erreurs typées** : une réponse négative explicite du service n'est pas une panne de transport. Ne
  les confonds pas dans un `except`.
- **Le backoff est partagé** entre poller et notifier : deux backoffs indépendants se désynchronisent et
  martèlent le service.
- **Un socket périmé ne se supprime qu'après vérification** qu'aucun processus ne l'écoute.
- **La rédaction de secrets s'applique ici aussi** : `journal.redact` avant tout envoi, parce que **deux
  frontières sortent de la machine** et que les JSONL ne sont jamais effacés.

---

## Sources — reprises retenues

**81 lignes.** Chaque pointeur se lit dans `resources/`. Le détail complet et le contexte de chaque partie sont dans [`resources/IMPORT_REPORT.md`](../../resources/IMPORT_REPORT.md).
**Lis la source avant de porter.** Une reprise collée sans être relue est un défaut.

#### B — Pi · `resources/pi-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| B3.7 | `packages/coding-agent/src/utils/shell.ts:216` | **Arrêter le groupe de processus, pas le seul parent.** | **Adapter** |
| B3.7 | `packages/coding-agent/src/utils/shell.ts:206` | Nettoyage des descendants suivis lors de l'arrêt. | **Adapter** |
| B3.7 | `packages/coding-agent/src/core/tools/bash.ts:80` | Exécution injectable avec `cwd` et environnement explicites. | **Adapter** |
| B3.7 | `packages/coding-agent/src/core/settings-manager.ts:172` | Précédence de configuration **documentée et testée**. | **Adapter** |
| B3.7 | `packages/coding-agent/src/core/settings-manager.ts:197` | Erreurs de configuration rapportées avec scope et chemin. | **Adapter** |
| B3.7 | `packages/coding-agent/src/core/auth-storage.ts:25` | Permissions restrictives des fichiers contenant des secrets. | **Adapter** |
| B3.7 | `packages/coding-agent/src/core/trust-manager.ts:125` | Mise à jour de configuration sous verrou, publication par rename. | **Adapter** |
| B3.7 | `packages/protocol/src/protocol.ts:49` | Enveloppe de commande : id, cible, résultat discriminé. Directement applicable au broker Telegram. | **Adapter** |
| B3.7 | `packages/protocol/src/protocol.ts:40` | **Empêcher une commande tardive de viser la nouvelle mission.** Un `/stop` envoyé pendant la mission N ne doit pas tuer la mission N+1. | **Adapter** |
| B3.7 | `packages/coding-agent/examples/extensions/dirty-repo-guard.ts:10` | Préflight des changements non commités. | **Adapter** |
| B3.7 | `packages/coding-agent/examples/extensions/git-checkpoint.ts:22` | **Ne pas assimiler un checkpoint Git à notre rollback à l'octet près.** | **Adapter** |
| B3.7 | `packages/coding-agent/examples/extensions/auto-commit-on-exit.ts:42` | Ne publier que des fichiers explicitement verts. | **Adapter** |
| B3.7 | `packages/coding-agent/docs/security.md:7` | **Séparer confiance de chargement et confinement d'exécution.** Charger une capacité de confiance ne l'autorise pas à tout faire. | **Adapter** |
| B3.7 | `packages/coding-agent/src/utils/git.ts:84` | Validation des arguments Git avant passage à la CLI. | **Adapter** |
| B3.7 | `packages/client/src/client.ts:45` | Corrélation des requêtes et nettoyage des attentes. | **Adapter** |
| B3.7 | `packages/server/src/transports/unix/listener.ts:299` | **Ne supprimer un socket périmé qu'après vérification de son identité.** | **Adapter** |
| B3.7 | `packages/server/src/transports/unix/listener.ts:11` | Permissions et fermeture bornée du transport local. | **Adapter** |
| B3.7 | `packages/coding-agent/src/experimental/mini/shared/rpc.ts:65` | Liveness séparée de la durée d'un appel long. | **Adapter** |


#### C — Kilo Code · `resources/kilocode-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| C3.7 | `core/src/util/flock.ts:148-240` | **Verrou de fichier à heartbeat et verrou breaker.** Notre `RunLock` v1 décide de la péremption par liveness de PID : deux prétendants peuvent conclure simultanément que le verrou est périmé et le casser ensemble. Le heartbeat règle l'éviction à tort d'une section longue, le breaker règle la course. | **Traduire** |
| C3.7 | `core/src/util/flock.ts:25-37,103-107` | Écriture en `wx` pour détecter un verrou compromis. | **Traduire** |
| C3.7 | `core/src/util/flock.ts:212-221` | Libération sûre même après péremption constatée. | **Traduire** |
| C3.7 | `opencode/src/git/index.ts:6-18` | Prélude fixe rendant git déterministe. Voir § C3.2. | **Traduire** |
| C3.7 | `opencode/src/worktree/index.ts:102-113` | Création de worktree isolée avec nettoyage garanti. | **Adapter** |
| C3.7 | `kilo-memory/src/capture/redact.ts:2-42,44-79,105-111` | **Rédaction de secrets** par motifs nommés, appliquée avant persistance. À appliquer à nos deux frontières brokerisées et à des JSONL qui ne sont jamais effacés. | **Traduire** |


#### D — Ouroboros · `resources/ouroboros-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| D3.8 | `our/process_custody.py:233-260,496-560` | Appariement par empreinte **stricte** `(pid, start_time, cmd_sha256)`, jamais par classe de commande. PID mort ou empreinte non concordante ⇒ on n'adopte pas. | **Copier** |
| D3.8 | `our/process_custody.py:12-19` | Scopes `task` / `session` / `daemon` à sémantique de moisson distincte. Notre verrou de campagne et nos subprocess de vérification ne sont pas le même scope. | **Copier** |
| D3.8 | `sup/state.py:177-187` | Procéder sans verrou est un arbitrage de disponibilité assumé (un verrou coincé ne doit pas figer le superviseur), **mais jamais silencieux**. | **Copier** |
| D3.8 | `sup/state.py:33-51` | Sous pytest, tout writer qui résout vers l'arbre de données **vivant** lève. Nos tests écriront sous `~/logs/pithos2/`. | **Copier** |
| D3.8 | `our/agent_startup_checks.py:823-915` | `verify_system_state` — une vérification de démarrage qui émet **un seul événement JSONL typé** portant chaque contrôle et un verdict global. | **Copier** |
| D3.8 | `our/agent_startup_checks.py:916-929` | Réconciliation limitée aux **propriétaires prouvés morts d'une génération antérieure**. Un TTL n'autorise jamais un renvoi payant. | **Copier** |
| D3.8 | `our/agent_startup_checks.py:710-805` | `hot_store_growth_notes` — tripwire déterministe sur la croissance des stores chauds, surfacé au démarrage **et** à chaque tour. | **Copier** |
| D3.8 | `pk/systemd/ouroboros.service:1-24` | **Aucune politique de redémarrage** : *« the launcher owns its crash fuse and treats a panic exit as a complete stop until the owner starts Ouroboros again. »* Directement applicable à nos LaunchAgents. | **Copier** |
| D3.8 | `pk/systemd/README.md:1-40` | Un seul chemin de lancement par instance, verrou d'instance **partagé** par les deux chemins ; l'installation n'active ni ne démarre jamais l'unité. | **Copier** |
| D3.8 | `sk/telegram/lib/telegram_api.py:39-75` | Deux erreurs typées : `TelegramRequestRejected` (réponse négative explicite, `transient` = 429/5xx) et `TelegramTransportError` (pas de réponse). | **Copier** |
| D3.8 | `sk/telegram/lib/telegram_api.py:61-75` | Backoff **monotone partagé** par le poller et le notifier : 5 s → doublement → 60 s, **remis à l'initial par tout tour réussi**. | **Copier** |
| D3.8 | `sk/telegram/lib/telegram_api.py:24-36,82-113` | Découpe de texte en **unités UTF-16**, pas en caractères : la limite Telegram est en UTF-16 et un emoji en compte deux. | **Copier** |
| D3.8 | `sk/telegram/lib/telegram_state.py:37-70` | `_jsonl_tail` renvoyant `(lignes, un_préfixe_a_été_omis)` — un tail borné **déclare** son omission. | **Copier** |
| D3.8 | `od/DEVELOPMENT.md:494-541` | Invariant **Projection over replay** : un lecteur *par interaction* ne rejoue jamais un store qui grandit. Par-boot est autorisé. **Notre choix « index JSONL au démarrage » est conforme** — voir conflit n°7. | **Copier** |
| D3.8 | `our/observability.py:262-340` | `write_blob` / `read_blob_ref` — au-delà d'un seuil le payload devient un **ref content-addressé** ; le résumé porte le ref, jamais la copie. | **Copier** |
| D3.8 | `our/_outcome_receipts.py:529-670` | `receipt_identity_projection` et `verification_receipt_ledger_row` — projection destinée au relecteur portant **le compte omis et un hash durable de l'identité complète** ; une ligne de registre par reçu, prête pour le dashboard. | **Adapter** |
| D3.8 | `our/outcomes.py:1387-1525` | `build_verification_ledger` — registre par tâche construit depuis **les seuls faits d'exécution faisant autorité**, jamais une reformulation. | **Adapter** |
| D3.8 | `sup/state.py:772-917` | `status_text` — rendu texte compact de l'état complet, réutilisé par le CLI, Telegram et le dashboard. **Une seule vue, trois transports.** | **Copier** |


#### E — Prime Agent · `resources/prime-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| E3.7 | `ca/core/session-lease.ts:160-263` | **Verrou de mission par `pid` + heure de démarrage du processus.** Ferme le PID recyclé que le `RunLock` v1 ne savait pas distinguer. | **Adapter** |
| E3.7 | `verrou` | `processStartId` absent ou illisible ⇒ **le détenteur est présumé vivant**. Le repli protège le travail en cours plutôt que le nettoyage. | **Traduire** |
| E3.7 | `verrou` | Récupération d'un verrou périmé par **renommage atomique** vers `<dir>.stale-<pid>-<uuid>` puis suppression. Deux processus ne peuvent pas réclamer le même. | **Adapter** |
| E3.7 | `verrou` | `release()` idempotent, **ne supprime que si le token correspond toujours**. Un verrou récupéré par un autre processus n'est pas détruit par le premier. | **Traduire** |
| E3.7 | `ca/core/cron-jobs.ts:1591-1598` | **`nextRunAt` est avancé à la réclamation, pas à la fin d'exécution.** Un job déjà réclamé est marqué `lastSkippedAt` : **les ticks manqués sont coalescés, jamais empilés.** | **Adapter** |
| E3.7 | `réveil` | `recoverInterruptedDispatches` — au démarrage, les dispatches restés ouverts sont réconciliés. C'est notre item P0. | **Adapter** |
| E3.7 | `réveil` | En cas d'exception pendant la réclamation, les dispatches déjà réclamés sont **explicitement remis en réconciliation** avant de propager. | **Traduire** |
| E3.7 | `réveil` | **Une file par session cible** : deux jobs de la même session ne se marchent pas dessus. | **Inspirer** |
| E3.7 | `réveil` | Un seul timer vers le prochain job dû, clampé, re-planifié après chaque exécution. **Pas de tick périodique.** | **Adapter** |
| E3.7 | `réveil` | **Politique de délivrance pendant une mission active** : `steer` (interrompre le tour) vs `follow_up` (attendre la fin). | **Traduire** |
| E3.7 | `réveil` | Intervalle minimum rejeté **à l'analyse**. Une borne basse dans le parseur vaut mieux qu'un garde dans la boucle. | **Traduire** |


#### G — OpenHands · `resources/OpenHands-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| G3.6 | `scripts/dev-safe.mjs:72,123` | **Clé d'API générée côté hôte, jamais par le modèle** ; fichier de clé persistante au chemin contractuel. | **Adapter** |
| G3.6 | `scripts/dev-safe.mjs:218,266` | **Port libre trouvé par bind explicite sur loopback** ; plusieurs ports vérifiés **avant** de démarrer le stack. | **Adapter** |
| G3.6 | `scripts/dev-safe.mjs:896,915` | Disponibilité d'un serveur attendue **avec timeout** ; spawn encapsulé dans **une abstraction unique**. | **Adapter** |
| G3.6 | `scripts/dev-safe.mjs:1177` | **Leases de conversations périmées libérées au démarrage**, pas à l'arrêt. Un crash ne bloque jamais le réveil suivant. | **Adapter** |
| G3.6 | `scripts/dev-safe.mjs:433,569` | Commande construite **en liste d'arguments** ; configuration dérivée d'un `cwd` et d'un environnement contrôlés. | **Adapter** |
| G3.6 | `scripts/dev-process-utils.mjs:13,85` | Existence d'un processus testée **sans supposer son état** ; **signal envoyé à l'arbre**, pas au seul parent. Cinquième source. | **Adapter** |
| G3.6 | `scripts/dev-process-utils.mjs:131` | **Registre de hooks d'arrêt exécutés à toute sortie.** | **Adapter** |
| G3.6 | `scripts/proxy-utils.mjs:69,206` | `/server_info` traité **séparément** pour enrichir la topologie ; fabrique de handlers **centralisant erreurs et timeouts**. | **Adapter** |
| G3.6 | `electron/main.mjs:262,618` | **Readiness de l'agent-server vérifiée séparément de la readiness UI** ; démarrage du stack encapsulé dans **une phase unique et observable**. | **Adapter** |
| G3.6 | `electron/main.mjs:462,596` | Ligne de log **nettoyée avant affichage ou persistance** ; logs routés **avec niveau et nom de service**. | **Adapter** |
| G3.6 | `scripts/dev-extra-backend.mjs:80` | **Probe générique de readiness HTTP avec deadline.** | **Adapter** |
| G3.6 | `scripts/download-uv.mjs:107` | **Version d'outil résolue avant téléchargement** — ne jamais suivre une URL non versionnée. | **Adapter** |


#### H — SWE-agent · `resources/SWE-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| H4.7 | `sweagent/tools/tools.py:41,56` | **Blocklist de commandes interactives ou dangereuses** ; blocklist exacte contre les **shells imbriqués**. | **Adapter** |
| H4.7 | `sweagent/environment/swe_env.py:130` | **Timeout distinct par commande de setup**, pas un timeout global unique. | **Adapter** |
| H4.7 | `sweagent/environment/swe_env.py:124` | Commandes de setup exécutées **dans la même session shell** que l'agent. | **Adapter** |
| H4.7 | `sweagent/utils/log.py:44,93` | Handler centralisé **avec nom de thread et contexte** ; file handler ajouté ou retiré **par identifiant**, sans reconfigurer tout le logging. | **Adapter** |
| H4.7 | `sweagent/utils/jinja_warnings.py:4` | **Avertir d'une syntaxe de template probablement erronée avant l'appel modèle.** Une session perdue sur une accolade mal fermée est une session perdue. | **Adapter** |
| H4.7 | `sweagent/inspector/server.py:221,295` | Handler HTTP **read-only** ; répertoire et port **explicitement fournis**. | **Adapter** |


#### I — Langfuse · `resources/langfuse-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| I4.7 | `worker/src/utils/RedisLock.ts:55` | **Libération conditionnée à l'identité du propriétaire** — comparer le jeton avant suppression **et avant renouvellement**. | **Adapter** |
| I4.7 | `worker/src/utils/RedisLock.ts:4` | **Lock à trois états** : acquis, détenu par autrui, **indisponible**. Le défaut `onUnavailable = proceed` est **inadapté : indisponible doit bloquer**. | **Adapter** |
| I4.7 | `worker/src/utils/PeriodicExclusiveRunner.ts:69` | Renouvellement de lease **mutualisé et limité en fréquence**, perte typée. | **Adapter** |
| I4.7 | `packages/shared/src/server/ingestion/processEventBatch.ts:116` | **Admission d'un lot avec résultat par événement** et inventaire des rejets. | **Adapter** |
| I4.7 | LF067 | **Persistance des payloads avant mise en queue** — un upload échoué empêche l'enqueue. | **Adapter** |
| I4.7 | `worker/src/features/blobstorage/inFlightExports.ts:30` | **Registre des opérations en cours pour l'arrêt** : handle inscrit, retiré en `finally`, attente bornée. | **Adapter** |
| I4.7 | `worker/src/scripts/replayIngestionEventsV2/replay.ts:182` | Script opérateur : **dry-run, retry, rate limit et sémaphore**, débit borné indépendamment de la concurrence. | **Adapter** |
| I4.7 | LF070 · **X** | **Checkpoint non sûr** : le compteur inclut les lots en erreur et **ne représente pas un préfixe contigu**. | **Adapter** |
| I4.7 | `web/src/features/mcp/server/security.ts:70` | **Validation de `Host` et `Origin`** — sans l'échappatoire `allowedHosts=["*"]`, et **l'absence d'`Origin` n'est pas une preuve de confiance**. | **Adapter** |
| I4.7 | LF104 | **Frontière de licence définie par les chemins** : MIT pour le socle, exceptions `ee/`, `web/src/ee/`, `worker/src/ee/`. | **Adapter** |

