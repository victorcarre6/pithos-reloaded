# STATE — `broker`

**Statut** : bloqué
**Mise à jour** : 12:09
**Lignes** : 414 code / 550 cible · 749 physiques
**Empreinte** : 22cfa7cdd5549e3a4dfd3b7cda77068ef6875377fbf81824ae8000b8952a9f9f

## Prochaine action

RepoFact canonique et complétude sont livrés. Définir le propriétaire de la boucle de polling Telegram (campaign est le candidat compatible avec les dépendances) avant de raccorder poll/saved_offset/remember_offset ; ne pas importer lifecycle ici.

## Avancement

- [x] `repo_fact` rend les **deux côtés** d'un rename, et une ligne malformée de `--porcelain` est une
      erreur, pas un silence.
- [x] Un rejeu après échec de transport ne compte **pas deux fois** — test explicite sur l'identité de
      résultat.
- [x] Une reprise trouvant l'intention sans le résultat **interroge** l'état distant avant de rejouer.
- [x] `commit` ne publie **que** les chemins explicitement désignés — test qui salit le dépôt et vérifie que
      les fichiers non désignés ne sont pas commités.
- [x] Le préflight refuse de démarrer sur un dépôt sale, avec la liste des fichiers en cause.
- [x] Les arguments Git sont validés avant passage à la CLI — test d'injection.
- [x] Les offsets Telegram sont **persistants** : un redémarrage ne rejoue pas les commandes déjà traitées.
- [x] Une commande d'un utilisateur hors allowlist est **ignorée et journalisée**.
- [x] `/pause` et `/stop` atteignent l'`InterruptController` sans que `broker` touche l'arbre.
- [ ] La boucle de polling s'arrête proprement sur signal, avec état de sortie confirmé par `lifecycle`.
      **Bloqué** — la boucle appartient à `lifecycle` ; `broker` en publie les trois unités.
- [x] Le backoff est **monotone et partagé** entre le poller et le notifier.
- [x] `tests/boundaries/` confirme que **seul** `broker` ouvre un socket sortant — **écrit et vert**,
      mais dans `src/broker/test_import_boundaries.py` : l'emplacement demandé est hors périmètre.

## Journal

_Append-only. Une entrée par unité de travail terminée. **Les résultats négatifs restent** — un timeout, une
incompatibilité ou une mesure défavorable sont des preuves. Chaque entrée porte son **niveau de preuve**
(`AGENTS.md` § 10), jamais plus haut que ce qui a été observé._

### 07:09 — `git.py` : fait de dépôt, préflight, commit borné, PR

Écrit `src/broker/git.py` (246 L) et `src/broker/test_git.py` (39 cas, tous verts dans le venv `pithos`,
`python -V` = 3.12.9).

Ce qui a été **mesuré**, sur un vrai dépôt Git créé en `tmp_path` (donc pas sur un double) :
- `repo_fact` rend les deux côtés d'un `git mv` (`R  moved.py\0kept.py`), les chemins non suivis via `-uall`,
  et un chemin contenant des espaces reste intact grâce à `-z` ;
- six formes malformées de `--porcelain` lèvent `Cause.invalid_schema` — dont un rename sans son chemin
  d'origine, qui est le silence le plus facile à commettre ;
- `commit(repo, [wanted.py], msg)` sur un dépôt sali de trois fichiers laisse `git show --name-only` à
  `["wanted.py"]` seul, les deux autres restant sales après le commit ;
- le préflight lève en **nommant** `kept.py` et `extra.py`, pas en les comptant ;
- un dépôt sans commit rend `head=""` et `diff=""` sans lever : un dépôt de campagne neuf n'est pas une panne.

`open_pr` et `automerge` sont testés sur un **runner injecté** (`gh` n'est jamais lancé) : la commande
construite est vérifiée argument par argument, l'auto-merge ne lance `gh pr merge` que sur un rollup
entièrement `SUCCESS`, et refuse sur `FAILURE`, `PENDING`, rollup vide ou absent.

**Niveau de preuve** : 4 pour tout ce qui touche `git` — la fonction métier est constatée sur le vrai
binaire, dans un dépôt réel, avec effet mesuré (niveau 3) puis assertions métier. **2 pour `gh`** : seule la
forme des commandes et le décodage de leur sortie sont prouvés ; aucun appel réseau n'a eu lieu, donc rien
n'est su de la réponse réelle de GitHub. Le niveau 6 pour `gh` appartient au jalon « premier vert ».

### 07:09 — ordre test/implémentation, résultat négatif de méthode

`git.py` a été écrit **avant** son test, contrairement à la boucle d'`AGENTS.md` § 5. Les 39 cas sont
passés du premier coup, ce qui est précisément le signe que le test n'a pas eu l'occasion d'être rouge :
il documente le comportement au lieu de l'avoir contraint. Consigné comme tel — les unités suivantes
(`identity`, `intent`, `telegram`) sont écrites test d'abord.

### 07:09 — `identity.py` et `intent.py` : ce qui ne compte qu'une fois

Écrit test d'abord, cette fois : les 15 cas ont été **rouges** (module absent) avant implémentation.

- `result_key(mission, nœud, tentative, effet)` est déterministe et sépare ses quatre axes : le
  séparateur nul empêche `("mission", "1node-7")` de produire l'empreinte de `("mission-1", "node-7")` —
  mesuré, c'est le cas qui tombe sans séparateur.
- Deux tentatives du même effet portent la **même** identité de résultat et **deux** identités de
  transport ; une tentative suivante (`attempt` 3) est un autre résultat.
- Les trois états de reprise sont distingués sur le double du journal : rien d'écrit → `unstarted`,
  intention seule → `unknown_effect`, résultat écrit → `recorded`. Un test observe l'état **pendant**
  l'effet et mesure `unknown_effect` : l'ordre d'écriture est donc bien intention → effet → résultat.
- `resume` n'interroge l'hôte **que** dans l'état `unknown_effect` : le test compte les appels au probe
  (0 sur `unstarted`, 0 sur `recorded`, 1 sur `unknown_effect`) et vérifie qu'un résultat trouvé chez
  l'hôte est enregistré sans rejeu.
- Le rejeu complet d'un effet déjà enregistré laisse **une seule** entrée au registre, avec l'identité de
  transport de la dernière tentative — l'identité de transport est renouvelée, jamais comparée.

**Niveau de preuve** : 5 — validé sur le double du journal, jamais sur son implémentation.

### 07:09 — `telegram.py` : deux erreurs typées, un backoff partagé, cinq commandes

Écrit test d'abord ; les 28 cas étaient rouges avant implémentation, et **trois sont restés rouges après**
— deux attentes de cadence fausses de ma part (je supposais un doublement dès la première panne, la
mesure dit : première panne = délai initial) et une assertion de rédaction mal posée (voir plus bas). Les
attentes ont été corrigées sur la mesure, pas l'inverse.

Testé contre une **vraie route HTTP locale** scriptée (`http.server` sur port libre, `PITHOS_TELEGRAM_API`
la désigne), donc du vrai trafic `httpx` — pas un client simulé.

- **UTF-16** : `"🙂" * 2049` fait 2049 caractères mais 4098 unités ; la découpe rend 2 messages, aucun
  point de code n'est coupé en deux, et `"".join(pieces) == text` (aucune perte, contrairement à la
  découpe d'Ouroboros qui `lstrip` ses espaces).
- **Backoff monotone partagé** : 5 → 10 → 20 → 40 → 60 → 60, remis à l'initial par tout tour réussi. Le
  test le mesure **à travers les deux chemins** : un envoi qui échoue en 500 pose 5, un polling qui échoue
  ensuite pose 10. Un seul état de module, donc pas de désynchronisation possible.
- **Deux erreurs typées** : 429 et 500 → `TelegramRequestRejected.transient is True` ; 400 et 403 → même
  classe, `transient is False` ; corps illisible ou route injoignable → `TelegramTransportError`. Seules
  les issues transitoires font avancer le backoff.
- **Idempotence** : deux `notify` de même clé n'envoient qu'une fois ; un envoi **échoué** n'est pas
  mémorisé comme envoyé, donc la reprise renvoie réellement.
- **Allowlist** : une commande de l'expéditeur 99 hors allowlist est ignorée **et journalisée** (le fait
  porte `sender: 99`), et l'update est tout de même consommée — l'offset avance, sinon elle reviendrait
  indéfiniment.
- **Cinq commandes** exactement, `/answer` portant son argument ; `/deploy now` et un texte libre sont
  écartés.
- **`/pause` et `/stop`** passent par `register_interrupt()` d'un contrôleur injecté : `/pause` émet un
  signal (`interrupt`), `/stop` va jusqu'à `exit`. `broker` ne touche jamais l'arbre.
- **Commande tardive** : `is_stale(command, mission_started_at)` — un `/stop` daté d'avant le début de la
  mission courante ne la vise pas. C'est la reprise `pi/protocol.ts:40`.

**Résultat négatif conservé** : la rédaction par `journal.redact` ne scrute que les **noms de champ**. Un
secret collé dans un texte libre — typiquement la description d'erreur de Telegram, qui peut renvoyer
l'URL portant le jeton du bot — lui échappe entièrement. Ma première assertion de test le supposait, à
tort. Corrigé par un retrait **par valeur** du jeton (`_scrubbed`) appliqué avant que la description
n'atteigne la trace, en plus de la passe `journal.redact`. Mesuré : la description journalisée contient
`***REDACTED***` et plus le jeton. La limite de `journal.redact` est consignée en blocage.

**Niveau de preuve** : 4 — la fonction est correcte sur une vraie route HTTP locale, avec le vrai client
`httpx`. **Pas 6** : l'API de Telegram n'a jamais été appelée, aucun message n'a quitté la machine, et
rien n'est su ici de ses réponses réelles ni de ses limites de débit.

### 07:09 — frontière : `Protocol`, double, graphe d'imports

`src/broker/__init__.py` publie le `Protocol` `Broker` (7 membres) ; `tests/doubles/broker.py` (126 L) est
un dépôt simulé plus un Telegram en mémoire. Le double sait jouer les trois scénarios exigés par
`MODULE.md` § 9, et chacun est testé : un `RepoFact` **cohérent** avec un `FileFact` donné, un `RepoFact`
qui le **contredit** (c'est ce cas-là qui testera la preuve d'effet croisée de `verifier`), un dépôt sale
au préflight, et un échec de transport suivi d'un rejeu qui ne compte qu'une fois.

Implémentation et double satisfont le même `Protocol` et partagent leurs signatures publiques — les
paramètres d'injection (`runner`, `trace`) sont keyword-only et exclus du contrat, sinon le double
devrait porter un `runner` qu'il n'exécute jamais.

Graphe d'imports mesuré sur tout `src/` :
- `broker` n'importe rien au-dessus de lui — l'intersection avec les huit modules interdits est vide, et
  le test se vérifie lui-même sur douze violations injectées ;
- **les seuls modules qui parlent HTTP sont `bridge` et `broker`** ; `bridge` est borné au loopback par
  son propre client (`normalize_base_url`), ce que ses tests gardent. La contrainte dure n°5 est donc
  mécaniquement close ;
- **aucun module n'importe `socket` ni `socketserver`** dans son code livré.

Suite complète du dépôt : **738 tests verts**, dont 106 pour `broker`, en 34 s, venv `pithos`, Python
3.12.9. Aucun test d'un autre module n'a été touché.

**Niveau de preuve** : 5 — contrat de frontière validé sur double ; le graphe d'imports est une preuve
statique de niveau 4 sur le code livré.

### 10:09 — passe transverse : `tests/boundaries/` et `tests/contracts/` sont peuplés

Écrite par l'agent d'intégration, pas par un agent de module. Ce module n'a **pas** été modifié : seuls
ses deux tests transverses ont été déplacés à l'emplacement qu'`AGENTS.md` § 11 leur assigne.

**Découvert au passage, et mesuré** : la suite complète du dépôt **n'était pas collectable**. Chaque
agent ne lançait que `pytest src/<son module>`, vert en isolation ; à l'échelle du dépôt, huit
`test_import_boundaries.py` et sept `test_double_contract.py` entraient en collision de nom de module
pytest, parce que `kernel`, `engine` et `lifecycle` n'avaient pas de `__init__.py`. Les trois ont été
ajoutés, et les quinze fichiers renommés à un nom unique en migrant.

**Mesuré, après la passe** : `pytest -q` à la racine, venv `pithos`, Python 3.12.9 →
**1215 passed, 3 skipped**. Les onze tests de frontière et les neuf corpus de contrat ont été
**prouvés mordants** par injection : une violation d'import réelle dans le code livré de chaque module
rend son test de frontière rouge, et une signature de double divergente rend son contrat rouge.

**Niveau de preuve** : 5 — validé sur double, à l'échelle du dépôt cette fois.

## Blocages

| Quoi | Pourquoi | Ce qui débloquerait | Résolu le |
|---|---|---|---|
| Boucle de polling Telegram | `MODULE.md` § 4.1 la confie à `lifecycle` (custody, arrêt confirmé, journal des orphelins), mais **les deux modules se l'interdisent mutuellement** : `broker` ne dépend que de `kernel` et `journal`, et `lifecycle/MODULE.md:21,49` lui interdit tout réseau et tout import de `broker`. Aucun `tests/doubles/lifecycle.py` n'existe par ailleurs. | Nommer le module de niveau ≥ 3 qui tient la boucle — `campaign` est le premier à pouvoir importer `broker` **et** `lifecycle`. Il appellerait `poll` / `saved_offset` / `remember_offset` sous la custody de `lifecycle`. Si la décision range malgré tout la boucle dans `broker`, il faut d'abord un double de `lifecycle` et une révision de sa carte de dépendances. | — |
| Emplacement des tests de frontière | `test_import_boundaries.py` et `test_double_contract.py` vivent dans `src/broker/`. `AGENTS.md` § 11 les attend dans `tests/boundaries/` et `tests/contracts/`, hors périmètre d'un agent de module. | Une autorisation d'écrire ces deux fichiers, ou un agent transverse qui les déplace. Ils sont écrits pour être déplacés sans modification (chemins dérivés de `parents[1]`). | **Résolu le 10:09** — déplacés par la passe transverse ; suite complète verte. |
| `journal.redact` ne rédige que par **nom de champ** | Un secret dans un texte libre lui échappe. C'est exactement le cas de la description d'erreur de Telegram, qui peut renvoyer l'URL portant le jeton du bot. | Un motif de rédaction **par valeur** dans `journal.redact` (la source `kilocode/kilo-memory/src/capture/redact.ts:2-42` en porte un). En attendant, `telegram._scrubbed` retire le jeton par valeur, avant la trace — protection locale, non généralisée. | — |
| Écart de lignes : 755 pour ~550 L | Le budget de `MODULE.md` § 7 (230 + 220 + 60 + 40) ne comptait ni `__init__.py` (53 L de `Protocol`, exigé par `ARCHITECTURE.md`), ni les deux classes d'erreur typées, ni le backoff partagé, ni la découpe UTF-16 (~90 L à eux trois) — tous exigés par § 11 *Pièges connus* et par la table des reprises. Détail : `git` 246 (+16), `telegram` 320 (+100), `intent` 83 (+43), `identity` 53 (−7). | Rien à débloquer, mais le ratchet est désormais **shrink-only à partir de 755**. Aucune ligne n'est spéculative : chaque fonction est rattachée à un item de « Fini quand » ou à un piège de § 11. Toute réduction retirera du comportement testé. | — |
| `RepoFact` ne porte pas les lignes ± | `verifier/STATE.md` et `ARCHITECTURE.md:751` parlent de « lignes ajoutées et retirées » ; `MODULE.md` § 2 ne demande que `git diff` + `git status`. Le diff complet est présent, mais non chiffré par fichier. | Un besoin écrit côté `verifier` : s'il croise des empreintes et des chemins, le diff suffit ; s'il croise des volumes, ajouter `git diff --numstat -z` et deux champs à `Change`. | — |

## Décisions locales

- **`RepoFact` vit dans `broker`, pas dans `kernel`.** `kernel/MODULE.md:29` l'exclut explicitement du socle
  (« `RepoFact` arrive avec `broker` »). Il hérite de `kernel.contracts.Contract`, donc `extra="forbid"` et
  `frozen=True` s'appliquent comme partout ailleurs.
- **`Cause` d'un échec de commande** : `Cause.unverifiable` quand `git`/`gh` rend un code non nul — l'effet
  n'a pas pu être établi ; `invalid_path` / `invalid_symbol` / `invalid_schema` restent pour les refus de
  validation, **avant** toute exécution. La hiérarchie de `kernel.errors` est fermée, aucun code nouveau.
- **Le prélude Git est fixe** (`--no-optional-locks`, `core.autocrlf=false`, `core.fsmonitor=false`,
  `core.quotepath=false`), porté de `kilocode-main/packages/opencode/src/git/index.ts:6-18`. `core.longpaths`
  et `core.symlinks` sont écartés : ils ne concernent que Windows.
- **L'exécution est injectable** (`runner=subprocess.run`), avec `cwd` et `env` explicites — reprise de
  `pi-main/.../core/tools/bash.ts:80`. `_environment()` ne laisse passer que `PATH`, `HOME`, `GH_TOKEN`,
  `GITHUB_TOKEN`, plus `GIT_TERMINAL_PROMPT=0` et `LC_ALL=C` : pas de prompt interactif, sortie stable.
- **`automerge` relit la gate chez l'hôte** au lieu de croire un verdict passé en argument. `broker` ne peut
  pas importer `verifier` (§ 3 des règles d'import) ; un booléen d'appelant ne prouverait rien. La condition
  est : rollup non vide et toutes les conclusions à `SUCCESS`, sinon `Cause.invariant_failed`.
- **`open_pr` relit l'identité de la PR** via `gh pr view --json` après création, plutôt que de parser l'URL
  imprimée par `gh pr create`. L'identité vient de l'hôte, jamais de ce qu'on espérait obtenir.
- **Un dépôt sans commit n'est pas une erreur** : `_head` tolère un code non nul et rend `""`, et le diff est
  vide dans ce cas. C'est le seul endroit où un code de retour non nul est toléré.
- **L'identité de résultat est une empreinte, pas un tuple sérialisé.** `result_key` hache
  `(mission, nœud, tentative, effet)` séparés par un octet nul, ce qui rend impossible la collision par
  concaténation d'axes. `Effect` est une énumération fermée de quatre effets sortants — aucun littéral
  d'appelant ne devient une identité.
- **`intent` écrit dans un registre JSON par `journal.update_json_locked`**, pas dans un fichier à lui.
  La lecture passe par le même verrou (`read_ledger` capture l'état sous la fonction de mutation) :
  `broker` ne relit jamais un fichier que le journal est en train d'écrire.
- **`resume` ne rend pas un booléen.** Il rend le résultat déjà acquis, ou `None` quand l'effet reste à
  exécuter. L'appelant ne peut donc pas confondre « déjà fait » et « rien trouvé chez l'hôte ».
- **L'état partagé de `telegram` est au module, assumé** : `delay` (la cadence dégradée) et `sent` (les
  clés d'idempotence de ce processus). C'est ce qui rend le backoff **partagé** entre poller et notifier ;
  deux instances d'objet se désynchroniseraient. `note_success()` et `sent.clear()` sont l'API de remise
  à neuf, pas un point d'entrée réservé aux tests.
- **`notify` rend `bool`, mais ne fond pas les deux erreurs typées.** Elles sont levées par `_call`,
  distinguées dans la trace, et seule leur transitivité fait avancer le backoff. `poll`, lui, les
  **propage** : son appelant est la boucle, qui doit savoir ce qui s'est passé.
- **La persistance de l'offset n'est pas dans `poll`.** Confirmer un offset signifie « ces commandes sont
  traitées » ; le confirmer avant de les rendre perdrait celles qu'un arrêt interromprait. `poll` rend
  l'offset suivant, l'appelant appelle `remember_offset` après traitement.
- **Une allowlist vide n'autorise personne.** Le repli est fermé, jamais ouvert. Une commande écartée
  fait tout de même avancer l'offset, sinon elle reviendrait à chaque tour.
- **`relay` n'interprète pas l'arbre.** `/pause` émet un signal, `/stop` émet jusqu'à `exit`, tout le
  reste n'émet rien. Le contrôleur est passé en argument et typé par son seul `register_interrupt()` :
  `broker` n'importe pas `engine`.

## Reprises traitées

| Source | Verdict | Fait ? | Note |
|---|---|---|---|
| `kilocode/opencode/src/git/index.ts:6-18` | Traduire | oui | Prélude fixe, moins les deux options Windows. |
| `pi/.../core/tools/bash.ts:80` | Adapter | oui | `runner` injectable, `cwd` et `env` explicites. |
| `pi/.../utils/git.ts:84` | Adapter | oui | `checked_repo_path` / `checked_ref` / `checked_text` avant la CLI. |
| `pi/.../extensions/dirty-repo-guard.ts:10` | Adapter | oui | `preflight` lève au lieu de demander à un humain — le harness n'a pas d'UI. |
| `pi/.../extensions/auto-commit-on-exit.ts:42` | Adapter | oui | Inversé : la source fait `git add -A`, `commit` ne prend que des chemins désignés. |
| `pi/.../extensions/git-checkpoint.ts:22` | Adapter | non | Aucun checkpoint n'est écrit ici ; le rollback à l'octet près appartient à `workspace`. |
| `ouroboros/sk/telegram/lib/telegram_api.py:39-75` | Copier | oui | Deux erreurs typées, `transient` = 429/5xx. |
| `ouroboros/sk/telegram/lib/telegram_api.py:61-75` | Copier | oui | Backoff 5 s → doublement → 60 s, remis à l'initial par tout tour réussi. |
| `ouroboros/sk/telegram/lib/telegram_api.py:24-36,82-113` | Copier | oui | Découpe en unités UTF-16. La découpe d'origine `lstrip` ses espaces : réécrite sans perte. |
| `ouroboros/sk/telegram/lib/telegram_state.py:37-70` | Copier | non | Le tail borné qui déclare son omission est déjà rendu par `journal.tail` ; rien à porter ici. |
| `kilocode/kilo-memory/src/capture/redact.ts:2-42` | Traduire | partiel | `journal.redact` porte les motifs par nom ; le retrait **par valeur** du jeton est local à `telegram`. Voir blocage. |
| `pi/packages/protocol/src/protocol.ts:49` | Adapter | oui | `Command` est l'enveloppe : id d'update, cible (chat, expéditeur), type discriminé. |
| `pi/packages/protocol/src/protocol.ts:40` | Adapter | oui | `is_stale` — un `/stop` antérieur au début de la mission ne vise pas celle-ci. |
| `ouroboros/sup/state.py:772-917` | Copier | non | `status_text` — une vue, trois transports : appartient à `observatory`, qui l'a déjà écrit. |
| `langfuse/.../inFlightExports.ts:30` | Adapter | non | Registre des opérations en cours pour l'arrêt : relève de la boucle, donc de `lifecycle`. Voir blocage. |


### 11:09 — mesure de production et en-tête courant

Passe transverse demandée via TEMPO.md. Aucun code métier ni case de livraison modifié.
Mesure AST/tokenize : **412 lignes de code**, **755 physiques**, cible globale **550**. Sous-paquets et __init__.py inclus ; tests et doubles exclus.
L’empreinte de l’en-tête couvre les chemins et octets de toute la production.
La nouvelle métrique ne valide aucun item métier et ne relève aucune cible numérique.

**En-tête antérieur conservé** :

```text
**Statut** : bloqué
**Mise à jour** : 07:09
**Lignes** : 755 livrées (246 `git` · 320 `telegram` · 83 `intent` · 53 `identity` · 53 `__init__`)
+ 126 de double / ~550 L — **écart justifié plus bas**
```

**Niveau de preuve : 2** pour la mesure documentaire ; la suite initiale complète du 11:09 a rendu 1 215 passed et 3 skipped hors sandbox. Le détail des nouvelles validations vit dans tests/STATE.md.

### 12:09 — RepoFact au niveau partagé

Huit assertions rouges avant correction (**8 failed, 36 passed en 1,31 s**) : anciens types locaux,
champ complete absent et statuts tronqués/traversants acceptés. Après raccordement : **69 passed
en 1,44 s** (Git broker, contrat partagé, frontière). Les tests Git utilisent les dépôts temporaires
existants du corpus, aucune écriture Git dans le worktree de développement ni sortie réseau.

Change devient l’alias de kernel.RepoChange ; RepoFact est importé de kernel.facts. `complete` est
vrai seulement avec HEAD et sans fichiers non suivis, car diff HEAD ne transporte pas leur contenu.
Le transport Git est entier ; les extensions diff/textconv sont désactivées pour conserver les
observations brutes. Troncature porcelain et chemins hors dépôt deviennent invalid_schema.
Le double expose complete, faux au reset. L’ancien choix « RepoFact vit dans broker » est remplacé,
son producteur existe désormais et verifier ne doit jamais importer broker.

Mesure : **414 code / 550**, **749 physiques**. Aucun périmètre Telegram modifié.
**Niveau de preuve : 4** sur Git local réel ; contrat du double niveau 5. Pas de GitHub ni campagne.

**Prochaine action historique remplacée** :

```text
Faire trancher les **deux blocages de périmètre** ci-dessous, dans cet ordre :
1. la boucle de polling Telegram — **aucun des deux modules nommés ne peut l'écrire.** `broker` ne
   dépend que de `kernel` et `journal`, donc n'importe pas `lifecycle` ; et `lifecycle/MODULE.md:49`
   lui interdit explicitement d'importer `broker` (« il ne possède rien de réseau »). Question exacte :
   *quel module de niveau ≥ 3 tient la boucle ?* — `campaign` est le premier qui peut importer les deux.
   `broker` publie déjà les trois unités qu'elle cadence : `poll`, `saved_offset`, `remember_offset`.
2. l'emplacement du test de graphe d'imports et du test de conformité du double — écrits dans
   `src/broker/`, `AGENTS.md` § 11 les attend dans `tests/boundaries/` et `tests/contracts/`, hors
   périmètre. Même blocage que `journal` et `observatory`.

Tant qu'ils ne sont pas tranchés, **aucun code n'est en attente** : les dix autres items de « Fini quand »
sont verts.
```

### 12:09 — validation transverse des faits broker

Suite complète dans pithos Python 3.12.9 : **1 325 passed, 3 skipped, 7 warnings en 34,92 s**.
Les trois skips et sept warnings préexistants sont conservés. Aucun accès GitHub ni modèle.
**Niveau de preuve : 5** pour la chaîne de contrats ; pas de premier vert réel.

### 12:09 — raccord des chemins absolus dans le double

La revue trouve que `agree_with(FileFact)` ne pouvait plus accepter les chemins absolus de workspace sous le contrat canonique `RepoChange` (toujours relatif). Deux tests rouges (**2 failed, 44 deselected en 0,11 s**) précèdent la correction : `agree_with(fact, repo=...)` relativise sans I/O et rejette une cible extérieure ; sans racine explicite, une cible absolue est refusée. Les appelants utilisant déjà un chemin relatif restent compatibles. La complétude et le diff restent à scripter explicitement, aucun faux fait complet n'est fabriqué.
**Niveau de preuve : 5** attendu sur double, validation finale consignée ci-dessous.

### 12:09 — résultat négatif conservé : sockets locales interdites

La dernière commande ciblant **tout broker**, plutôt que Git seul, a donné **93 passed, 21 erreurs en 1,88 s** dans la sandbox. Les 21 erreurs viennent de `ThreadingHTTPServer(...).socket.bind` : `PermissionError: [Errno 1] Operation not permitted`. Les tests des faits et du double passent ; cette commande ne valide pas Telegram. Relance demandée hors sandbox, sans skip ni changement des tests. La suite globale précédente était **1 365 passed, 3 skipped, 7 warnings en 38,19 s** avant ces deux nouveaux tests de chemin.
**Niveau de preuve : 5** pour les scénarios de faits/double effectivement passés ; transport non validé par la commande refusée.

### 12:09 — preuve finale de la chaîne de faits et de la sélection

Suite complète finale dans **pithos / Python 3.12.9** : **1 367 passed, 3 skipped, 7 warnings en 37,10 s**. Relance broker hors sandbox : **114 passed en 1,99 s** ; les 21 erreurs de bind sont résolues sans skip.
Les contrôles d'en-têtes STATE et `git diff --check` passent. Aucune dépendance installée, aucun Git d'écriture, aucun bytecode suivi modifié. Les propositions sont dans les git.md ; les contrats transverses ont leur lot dans tests/git.md.
**Niveau de preuve : 5**, avec subprocess et fichiers de test effectivement exercés. Le marcheur complet et le premier vert avec modèle local restent à démontrer. La source candidate attend l'arbitrage utilisateur.
