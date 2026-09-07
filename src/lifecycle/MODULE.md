# `lifecycle` — la machine, pas le réseau

> **Lis [`AGENTS.md`](../../AGENTS.md) avant de commencer.** Ce fichier est ton contrat complet : tu ne
> devrais pas avoir besoin d'ouvrir `docs/`. Ton point d'entrée exact est la rubrique « Prochaine action » de
> [`STATE.md`](STATE.md), à côté de ce fichier.
>
> **Tu ne commites, ne pousses et ne merges jamais.** Tes commits se *proposent* dans [`git.md`](git.md),
> avec les `ga`/`gcmsg` exacts — voir [`AGENTS.md`](../../AGENTS.md) § 7.

**Cible** : ~250 L · ratchet **shrink-only**
**Dépend de** : `kernel`, `journal`.
**Niveau de dépendance** : 2.
**Stack** : **stdlib pur** — `os`, `signal`, `shutil`, `subprocess` (`launchctl`), `pathlib`.

## 1. Autorité

`lifecycle` possède **le verrou de mission, le réveil launchd, la custody des processus et la garde
disque**. C'est lui qui produit le `HostFact` que `verifier` consomme : attestation d'hôte, horloge monotone,
ancre de démarrage.

**Il ne possède rien de réseau.** Ce qui sort de la machine appartient à `broker`.

## 2. Interface publique

```python
class RunLock:
    "Verrou-répertoire atomique + (pid, heure de démarrage) + péremption par durée maximale."
    def acquire(self) -> LockState: ...      # held | unavailable | stale_reclaimed
    def release(self) -> None: ...

def install_agent(plist: Plist) -> None: ...          # génération + launchctl
def claim_tick(tick_id: str) -> bool:
    "Réclamation AVANT délivrance. Les ticks manqués sont coalescés, jamais empilés."

def kill_group(pid: int) -> None:
    "Arrête le GROUPE de processus, pas le seul parent."
def sweep_orphans() -> list[int]:
    "Rejoue le journal des orphelins, apparié par (pid, identité de démarrage)."

def ensure_space(path: Path, needed: int) -> None:
    "Lève une cause `blocked` mécanique, jamais une exception d'écriture."

def wait_ready(probe: Callable[[], bool], deadline: Deadline) -> Readiness:
    "Readiness OBSERVABLE. Un spawn n'est jamais une preuve de disponibilité."
```

## 3. Interdits

- **N'importe jamais `broker`, `engine`, `campaign`, `verifier`.**
- **Aucun accès réseau.** Pas de socket, pas de `httpx`, pas de résolution DNS.
- **Aucune adresse d'écoute configurable.** Voir § 5.
- **Ne déclare jamais un service prêt sur la base de son spawn.**

## 4. Le verrou — quatre sources, une composition

| Source | Ce qu'elle apporte | Contre quoi |
|---|---|---|
| v1 `RunLock` | verrou-répertoire atomique + PID vivant, 78 L | un PID mort — **incident réel traité** |
| Prime Agent | `pid` **+ heure de démarrage** | un PID recyclé |
| Langfuse | trois états dont `indisponible`, qui **bloque** | un état de verrou illisible traité comme « libre » |
| Kilo | heartbeat + breaker | **`Reporté`** — voir ci-dessous |

**~40 L, aucun thread.** Le heartbeat est le seul qui exige un thread écrivain, et il ne détecte qu'une chose
que les trois autres ne voient pas : un processus **vivant mais bloqué**. Or ce cas est déjà couvert par la
borne murale de `engine` et le `timeout_seconds` de Prefect en kill de dernier recours. Il arrive si un
incident de verrou coincé se produit réellement.

**Réserve reprise telle quelle** : un CAS de statut n'est pas à lui seul un jeton de propriété. Et **une
lecture de nœud périmé ne donne pas le droit de tuer une nouvelle incarnation** — c'est exactement le risque
des deux réveils launchd rapprochés dont le premier est lent à mourir.

## 5. Le réseau — l'interdiction est dans le type

**L'adresse d'écoute d'`observatory` est une constante, pas un réglage** : aucun chemin de code ne peut
binder ailleurs que `127.0.0.1`.

Une ligne — et `is_public_address`, la résolution DNS, la détection d'IP littérale, la normalisation des
binds wildcard et la validation `Host`/`Origin` deviennent **sans objet**. ~120 L évitées.

> La décision 27 est tenue **mieux** qu'avant : *« LAN différé »* cesse d'être l'absence de règle, parce que
> l'interdiction est dans le type et non dans la configuration. Ouvrir au LAN redeviendra un changement de
> code, donc une décision, avec la politique à écrire à ce moment-là.

**Gardé** : le cycle de vie complet d'un service local — readiness observable sous deadline, arrêt
idempotent, état de sortie confirmé, **fermeture de tous les sockets partiellement ouverts sur échec de
bind**.

## 6. Contenu

| Fichier | Contenu | ~L |
|---|---|---:|
| `lock.py` | verrou-répertoire, `(pid, start_time)`, péremption par durée, trois états | 60 |
| `launchd.py` | génération de plist, `launchctl`, réclamation de tick, coalescence | 70 |
| `custody.py` | groupe de processus, journal des orphelins, readiness, arrêt idempotent | 80 |
| `disk.py` | espace libre avant écriture, estimation de taille, redirection des temporaires | 40 |

## 7. Critères de socle que ce module rend verts

- **Aucun service local n'est déclaré prêt sur la base de son spawn** : une readiness observable est
  attendue sous deadline, et un arrêt confirme son état de sortie.
- **L'espace disque est vérifié avant écriture** d'un snapshot, d'une trace ou d'un artefact ;
  l'insuffisance est un `blocked` mécanique avec cause, **jamais une exception d'écriture**.
- Contribue à : *une reprise distingue non commencé / effet inconnu / résultat enregistré* — c'est
  l'ancre de démarrage du `HostFact` qui permet de distinguer une incarnation d'une autre.

## 8. Le double

`tests/doubles/lifecycle.py` — un hôte simulé : horloge pilotable, verrou en mémoire à trois états, espace
disque paramétrable, readiness pilotable. Il doit savoir jouer :

- un verrou **`indisponible`** — le cas qui doit **bloquer**, pas procéder ;
- un PID recyclé (même pid, heure de démarrage différente) ;
- un disque plein, pour que `journal` et `workspace` soient testés sur le chemin `blocked`.

## 9. Fini quand

- [ ] Deux acquisitions concurrentes du verrou : **une seule** réussit — test par `fork` réel, pas simulé.
- [ ] Un PID recyclé **ne prend pas** le verrou d'un autre — test avec même pid, heure de démarrage
      différente.
- [ ] Un verrou dont l'état est illisible rend **`unavailable`**, et l'appelant **bloque** — jamais
      « procéder ».
- [ ] Un verrou dépassant la durée maximale est réclamé, et la réclamation est journalisée.
- [ ] `kill_group` arrête **tous** les descendants — test avec un petit-enfant de processus.
- [ ] Deux ticks launchd rapprochés sont **coalescés**, pas empilés, et le second ne tue pas la première
      incarnation.
- [ ] `ensure_space` rend une cause `blocked` typée sur disque plein — jamais une `OSError` remontée.
- [ ] `wait_ready` échoue sous deadline si le service ne répond pas, **même s'il a été spawné**.
- [ ] Un échec de bind ferme **tous** les sockets partiellement ouverts et conserve la cause.
- [ ] `tests/boundaries/` confirme : aucun import réseau, aucun import de `broker`.

## 10. Pièges connus, et ce qui a été écarté

| Écarté | Pourquoi |
|---|---|
| **La politique d'exposition réseau** (~120 L) | `observatory` binde `127.0.0.1` en dur ; l'interdiction est dans le type |
| **Le heartbeat et le breaker** — `Reporté` | ils ne détectent qu'un processus vivant mais bloqué, cas déjà couvert |

⚠️ **Le mode d'échec le plus coûteux ici est une ancienne instance qui tue la nouvelle** !
→ Une réconciliation ne réapplique une transition que si **l'état observé n'a pas changé**. Un jeton
d'admission/génération à l'arrêt ferme le reste. C'est le risque exact des deux réveils launchd rapprochés.

---

## Sources — reprises retenues

**122 lignes.** Chaque pointeur se lit dans `resources/`. Le détail complet et le contexte de chaque partie sont dans [`resources/IMPORT_REPORT.md`](../../resources/IMPORT_REPORT.md).
**Lis la source avant de porter.** Une reprise collée sans être relue est un défaut.

#### A — Villani Code · `resources/villani-code-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| A4.7 | `hooks.py:19-59` | `HookRunner` — hooks `shell` ou `http` renvoyant `{allow, reason, input}`, avec réécriture possible de l'entrée. | **Inspirer** |
| A4.7 | `shells.py:15-41` | Commande **normalisée avant exécution et journalisée sous sa forme normalisée**. | **Inspirer** |
| A4.7 | `command_environment.py:32-48` | `CommandEnvironmentDiagnostics` — l'environnement passé à une commande est diagnostiqué et journalisé. | **Adapter** |


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
| C3.7 | `core/src/util/retry.ts:9-24` | Backoff borné réutilisable. | **Traduire** |
| C3.7 | `core/src/util/which.ts:6-16` | Résolution d'exécutable dans le `PATH`, sans shell. | **Traduire** |
| C3.7 | `opencode/src/kilocode/sandbox/network.ts:13-23` | Politique réseau du sandbox : allowlist explicite. | **Adapter** |


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
| E3.7 | `ca/core/orphan-process-journal.ts:53-80` | Le journal est rejoué pour trouver les processus **encore actifs**, appariés par `pid` + `processStartId`. | **Adapter** |
| E3.7 | `ca/core/settings-manager.ts:187,355,523` | Deux couches fusionnées récursivement, **chaque couche gardant son erreur de parsing propre**. | **Traduire** |
| E3.7 | `ca/migrations.ts:1-3,31-60` | Migrations one-shot renommant la source en `<fichier>.migrated` **plutôt que la supprimer**, et sautant si la cible existe. | **Traduire** |


#### F — Unsloth · `resources/unsloth-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| F3.1 | `unsloth/device_type.py:62,100` | Résolution **unique** du backend derrière un prédicat mis en cache ; comptage des devices une seule fois, configuration impossible refusée **avant lancement**. | **Adapter** |
| F3.1 | `unsloth/device_type.py:238` | Snapshot de statistiques matérielles pour diagnostiquer timeout, OOM et absence de progrès — **jamais une preuve de correction**. | **Adapter** |
| F3.1 | `unsloth/device_type.py:257` | Nettoyage explicite du cache entre deux nano-étapes ou après échec, **sous contrôle de `lifecycle`**. | **Adapter** |
| F3.1 | `unsloth/disk_utils.py:83` | Mesurer l'espace libre **avant** écriture ; transformer l'insuffisance en `blocked` mécanique. | **Adapter** |
| F3.1 | `unsloth/disk_utils.py:109` | Estimer la taille logique d'un artefact avant export, pour réserver le budget disque. | **Adapter** |
| F3.1 | `unsloth/disk_utils.py:120` | Rediriger les temporaires vers un emplacement contrôlé quand l'environnement impose un filesystem éphémère. | **Adapter** |
| F3.1 | `unsloth/dataset_num_proc.py:1` | Parallélisme déterminé **à partir des ressources**, avec borne et **repli mono-processus**. | **Adapter** |
| F3.1 | `unsloth/chat_templates.py:1885` | **Choix et normalisation du chat template centralisés** : l'exécuteur ne reçoit jamais un template arbitraire du modèle. Converge avec la contrainte dure n°1. | **Adapter** |
| F3.1 | `unsloth/chat_templates.py:2168` | Retirer les tokens spéciaux d'une vue de prompt **avant comparaison ou archivage**, pour éviter des faux changements. | **Adapter** |
| F3.1 | `unsloth/chat_templates.py:2370` | Déduire les EOS effectifs du tokenizer et **les consigner dans le contrat d'exécution**. | **Adapter** |
| F3.1 | `unsloth/utils/hf_hub.py:27,47` | Résolution de métadonnées par **fonction pure et sérialisable** ; lister sans charger les poids. | **Adapter** |
| F3.1 | `unsloth/models/loader_utils.py:1694,1900` | Détecter explicitement le mode **offline** et l'inscrire dans l'événement de mission ; réinitialiser les sessions après erreur pour qu'**un état global contaminé ne traverse pas les missions**. | **Adapter** |
| F3.1 | `unsloth/models/loader_utils.py:2079,2156` | Retry offline **avec diagnostic typé** ; vérifier la présence locale des fichiers **avant tout appel réseau**. | **Adapter** |
| F3.4 | `unsloth_cli/_tool_policy.py:165` | **Politique unique décidant si des outils peuvent être exposés**, selon l'adresse de bind et le mode sécurisé. | **Adapter** |
| F3.4 | `unsloth_cli/_tool_policy.py:19` | Détection d'adresse externe **incluant résolution DNS et IP littérale**, avant ouverture réseau. | **Adapter** |
| F3.4 | `unsloth_cli/_tool_policy.py:108` | **Normaliser les binds wildcard avant** d'évaluer l'exposition. Un `0.0.0.0` non normalisé qui se lit « local » est la faille type. | **Adapter** |
| F3.4 | `studio/backend/lan_access.py:213` | Prédicat **`is_public_address` partagé** par le bind, l'affichage et la politique d'outils. Trois consommateurs, une définition. | **Adapter** |
| F3.4 | `studio/backend/lan_access.py:72` | Énumérer les adresses LAN **sans inclure aveuglément** loopback ni interfaces hôte-only. | **Adapter** |
| F3.4 | `studio/backend/lan_access.py:370` | Sur échec de bind, **fermer tous les sockets partiellement ouverts et conserver la cause**. | **Adapter** |
| F3.4 | `studio/backend/lan_access.py:350` | Synchroniser l'état de confiance réseau avec **l'état réel du listener**, jamais avec le seul flag CLI. | **Adapter** |
| F3.4 | `studio/backend/lan_access.py:423,497` | Arrêt **idempotent** libérant tous les sockets ; décision d'accès **par requête**, centralisée et testable. | **Adapter** |
| F3.4 | `studio/backend/cloudflare_tunnel.py:507` | **Ne jamais considérer le spawn comme un succès** : attendre une readiness observable sous deadline. | **Adapter** |
| F3.4 | `studio/backend/cloudflare_tunnel.py:354,516` | Vérifier une URL par **probe** avant de l'annoncer prête ; **confirmer l'état de sortie** avant de finaliser. | **Adapter** |
| F3.4 | `studio/backend/cloudflare_tunnel.py:930` | Arrêt avec **jeton d'admission/génération** pour qu'une ancienne instance ne tue pas la nouvelle. Directement applicable à deux réveils launchd rapprochés. | **Adapter** |
| F3.4 | `studio/backend/cloudflare_tunnel.py:217,400` | Téléchargement d'un binaire externe **dans un cache contrôlé uniquement**, avec vérification d'existence ; encapsulation en objet à `start`/`wait_for_ready`/`stop`/`is_running`. | **Adapter** |
| F3.4 | `unsloth_cli/_system_dir_guard.py:1` | **Protéger les répertoires système et les chemins de configuration** contre les écritures de l'agent. Seconde ligne derrière le prédicat `authoritative`. | **Adapter** |
| F3.4 | `unsloth_cli/commands/start.py:1507` | **Écriture texte privée avec permissions restrictives** pour secrets et tokens. | **Adapter** |
| F3.4 | `unsloth_cli/commands/start.py:1498,1569` | Écriture JSON privée atomique ; **tester une clé contre le serveur avant de la mémoriser**. | **Adapter** |
| F3.4 | `unsloth_cli/commands/start.py:1191` | **Ne pas tuer un serveur encore utilisé par une session active** : le propriétaire est explicite. | **Adapter** |
| F3.4 | `unsloth/dataprep/synthetic.py:52,148,162` | **Terminaison récursive d'un arbre de processus** avec timeout de nettoyage ; readiness attendue explicitement ; **deadlines monotoniques partagés** entre subprocess, serveur et nettoyage. | **Adapter** |
| F3.4 | `unsloth/dataprep/raw_text.py:56,98,346` | Détecter le format **avant lecture** ; chunking à longueur et chevauchement explicites ; validation de dataset **avant écriture**. | **Adapter** |
| F3.4 | `unsloth/dataprep/raw_text.py:125` | Chunking préservant les **frontières sémantiques**, avec stride mesuré. | **Adapter** |


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

