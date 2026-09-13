# Pithos Reloaded — fiche projet

_Document canonique. Fixé au cadrage du 05:09, figé sauf changement explicite de périmètre._
_Amendé les 05:09 et 06:09 après extraction de neuf sources — Villani Code, Pi, Kilo Code, Ouroboros,
Prime Agent, Unsloth, OpenHands, SWE-agent et Langfuse : seize critères de socle ajoutés, périmètre
inchangé — une seule précision, sur le confinement natif._
_Amendé le 06:09 après **douze arbitrages de frontières** : dix modules au lieu de neuf, un vingt-septième
critère de socle, et l'organisation du dépôt._
_Amendé le 06:09 après la **passe de simplification module par module** : `trace` sort de `kernel` et devient
`journal`, soit **onze modules** ; ~380 reprises sur 1 180 écartées et la cible ramenée à ~5 230 L.
**Le périmètre reste inchangé** — aucun objectif ajouté ni retiré, et aucun critère retiré._

## Vision

Pithos Reloaded reprend l'objectif de Pithos v1 — **une expérience d'autonomie logicielle sur modèle local
souverain** — en déplaçant l'unité de travail. Là où v1 confiait un micro-rush entier à une session, v2
décompose dynamiquement jusqu'à la **nano-étape vérifiable** : un nœud de travail ne s'exécute que lorsqu'il
porte un critère exécutable, sinon il se scinde.

Le harness cesse de posséder le plan. Il garde les règles : contexte borné, session neuve, vérification hors
modèle, transactionnalité, bornes dures. Le modèle ne fait que des actes atomiques.

La campagne construit une **boîte à outils MCP générique pour agents**. Le livrable a une valeur d'usage
propre ; la trajectoire reste l'objet d'étude.

## Questions expérimentales

Les cinq questions de v1 sont conservées. Chacune reçoit un indicateur mesurable, absent en v1.

| Question | Indicateur |
|---|---|
| Le système progresse-t-il sans intervention humaine ? | outils vérifiés livrés / cycles consommés |
| Reprend-il correctement après interruption ? | reprise de l'arbre persistant sans historique conversationnel |
| Diagnostique-t-il ses limitations et ses échecs ? | nœuds `blocked` avec cause mécanique attribuée |
| Crée-t-il un outil utile, puis le réutilise-t-il ? | outils vérifiés effectivement appelés par des étapes ultérieures |
| Converge-t-il et sait-il proposer l'arrêt ? | proposition d'arrêt émise sur épuisement mécanique du backlog |

**Question neuve de v2, la plus importante :** un modèle local faible peut-il produire une **autorité de
validation fiable** quand on lui interdit d'émettre la moindre valeur attendue ?

## Périmètre initial

- Un seul modèle local : `pithos/ling-3.0-tiny:8b-16k` sur Ollama, contrainte assumée, sans re-benchmark.
  Échantillonnage `temperature 0.3` / `top_p 0.95` / `top_k 20`, mesuré par un tiers sur la même famille
  (décision 20). **La fenêtre de 16 k est lue sur `/v1/models`, pas supposée** — « sans re-benchmark » porte
  sur la qualité du modèle, pas sur ses paramètres de service (spike n°4).
- Un seul livrable : un serveur MCP local d'outils atomiques génériques, dans un dépôt Git dédié.
- Décomposition récursive dynamique, bornée par le temps mural de la mission.
- Validation exclusivement par **invariants métamorphiques** exécutés par le harness.
- Backlog ouvert : un `seed` long terme, le système propose lui-même l'outil suivant.
- Auto-merge des incréments validés ; l'humain est portier de la fin de campagne, pas des incréments.
- Réveil périodique, notifications Telegram de cycle de vie, traces JSONL append-only.
- Réemploi explicite de quatre composants v1 : dashboard, broker Git, traces JSONL/`live.log`, launchd+Telegram.

## Hors périmètre initial

- Comparer plusieurs modèles ou re-qualifier la baseline.
- Runtime conteneurisé et egress allowlisté : mesuré inexploitable sur ce matériel en v1. **Le confinement
  natif `sandbox-exec` n'est pas visé par cette exclusion** — voir décision 21, phase P7.
- Projection SQLite : les JSONL sont la source de vérité, le dashboard les lit directement.
- Oracle écrit ou relu par un humain avant un incrément.
- Tout appel à un modèle distant dans la boucle nominale.
- Auto-mutation du harness par un mécanisme dédié : l'auto-extension passe par le registre d'outils.

## Contraintes dures

1. **Le modèle ne produit ni valeur attendue, ni entrée de validation, ni commande d'exécution.**
   Pour les critères, il choisit uniquement des symboles existants et des énumérations fermées.
   **Amendement approuvé le 12:09** : il peut proposer le code candidat d'une fonction existante,
   via `new_source` revalidé ; workspace applique le splice et verifier exécute les copies sous les
   invariants du harness. Le code candidat ne peut modifier ni le critère ni les entrées de validation. C'est la correction directe de la cause d'échec n°1
   de v1, mesurée sur six micro-rushes.
2. **Un nœud non vérifiable ne s'exécute jamais.** Il se scinde, ou il est marqué `blocked`.
3. **Une nano-étape non verte restaure son fichier cible à l'octet près.**
4. **Une mission a un temps mural dur.** À l'expiration, elle finalise ce qui est vert et laisse l'arbre
   reprenable ; elle n'échoue pas globalement.
5. **Souveraineté totale.** Aucune donnée ne quitte la machine, hors Git et Telegram déjà brokerisés.
6. **Les données brutes sont append-only et ne sont jamais supprimées**, échecs compris.

## Organisation

```text
~/code/pithos_reloaded/
├── docs/               # PROJECT, EXPLANATIONS (décisions + journal), ARCHITECTURE, ROADMAP
├── src/                # les onze modules, un répertoire chacun, MODULE.md colocalisé
├── tests/              # doubles/, contracts/, boundaries/
├── resources/          # MANIFEST.md + IMPORT_REPORT.md ; les neuf dépôts sont hors dépôt Git
└── journals/           # snapshots des mutations de registre

~/code/pithos_campaign/ # dépôt Git du serveur MCP construit par le système
~/logs/pithos2/         # état mutable hors Git : missions, arbres, JSONL, live.log
```

**Quatre documents dans `docs/`, pas six.** `ELN.md` a fusionné dans `EXPLANATIONS.md` — décisions puis
journal — et `SUCCUBUS.md` est devenu `resources/IMPORT_REPORT.md`, à côté des sources qu'il indexe
(décision 33).

## Critères de succès du socle

Ces critères qualifient le harness. Ils doivent être verts **avant** le premier réveil autonome.

**Un jalon les précède, et il n'est pas un critère.** Le *premier vert* : une nano-étape, un invariant, un
mutation-check, un reçu, un fichier réellement modifié — de bout en bout, à la main, avant tout
durcissement. Il ne qualifie rien ; il prouve que les onze frontières s'emboîtent, pendant qu'une erreur de
découpe coûte encore peu.

- [ ] Un nœud sans critère exécutable est toujours scindé ou bloqué, jamais exécuté.
- [ ] Le modèle ne fournit aucune valeur attendue, entrée de validation ou commande ; seul le code candidat revalidé rejoint la transaction et les copies de verifier (amendement du 12:09).
- [ ] Un invariant qui survit à toutes les mutations de l'implémentation est rejeté comme tautologique.
- [ ] Un invariant doit être rouge avant l'implémentation et vert après, sinon il est rejeté.
- [ ] Une mission qui atteint sa borne murale finalise ses nœuds verts et reste reprenable.
- [ ] Une nano-étape échouée restaure son fichier cible à l'identique.
- [ ] Un changement `.py` qui ne compile pas, ou qui perd toutes ses `def` de module, est refusé avant écriture.
- [ ] Une proposition d'outil redondante est rejetée mécaniquement, sans appel au modèle.
- [ ] Un outil vérifié devient appelable par les sessions suivantes sans intervention humaine.
- [ ] Le système propose son arrêt quand il ne trouve plus de proposition non redondante.
- [ ] **Un nœud dont la cible n'a pas effectivement changé ne peut pas être compté vert.** Preuve par
      comparaison au contenu antérieur croisée avec `git diff`, et artefact d'exécution littéral pour toute
      validation (décision 13). **Écrire n'échoue jamais ; compter vert exige le reçu effectivement écrit** —
      un reçu absent retire l'attestation et le nœud passe `blocked` avec la cause `receipt_not_written`.
- [ ] **Un chemin non-`authoritative` n'est jamais proposé, écrit, projeté au modèle, ni compté comme
      changement.** Un seul prédicat partagé décide (décision 12).
- [ ] **La satisfaction d'un outil vérifié est invalidée dès que l'empreinte de ses fichiers change**, sans
      intervention humaine (décision 5 amendée).
- [ ] **Le contexte de chaque nœud est un inventaire typé** : raison d'inclusion ou d'exclusion par élément,
      pression mesurée, évictions comptées, dérive détectée (décision 14).
- [ ] **Aucune ligne JSONL n'est jamais réécrite ni supprimée**, y compris une fin de fichier tronquée : le
      fragment est diagnostiqué et la reprise ouvre un nouveau segment lié (décision 10 amendée).
- [ ] **Une reprise distingue non commencé / effet inconnu / résultat enregistré** et n'exécute jamais un
      effet externe deux fois sans interrogation préalable (décision 16).
- [ ] **Les frontières d'import sont testées comme contrats d'architecture**, les trois : `verifier`
      n'importe jamais le bridge ni le modèle, `bridge` n'importe jamais `engine`, et **`broker` est le seul
      module par lequel une donnée quitte la machine** — ce qui rend la contrainte dure n°5 vérifiable.
      Test de graphe d'imports, pas discipline.
- [ ] **Une écriture concurrente est détectée au moment d'écrire**, pas seulement réparée après : un
      compare-and-swap sur le contenu snapshoté échoue en `StaleContentError` typé (décision 9 amendée).
- [ ] **Le schéma envoyé au modèle est normalisé et testé** : `$defs`/`$ref` résolus, bornes explicites,
      vérifié contre le backend réel avant toute campagne (décision 17 amendée).
- [ ] **La sortie du modèle est revalidée localement contre le schéma exact envoyé** avant toute exécution.
      L'acceptation par le transport n'autorise rien : `response_format` est une intention que la route peut
      ignorer et que le retry peut retirer (décision 17 amendée).
- [ ] **Toute identité d'enregistrement est une clé typée, jamais une chaîne de repli**, et la relation de
      réconciliation est vérifiée réflexive, symétrique et transitive par test (décision 22).
- [ ] **Aucun service local n'est déclaré prêt sur la base de son spawn** : une readiness observable est
      attendue sous deadline, et un arrêt confirme son état de sortie (décision 27).
- [ ] **L'espace disque est vérifié avant écriture** d'un snapshot, d'une trace ou d'un artefact ;
      l'insuffisance est un `blocked` mécanique avec cause, jamais une exception d'écriture.
- [ ] **Une proposition mal formée reçoit toutes ses violations en une fois**, chacune avec le chemin exact
      du champ fautif — jamais seulement la première rencontrée (décision 28).
- [ ] **Toute projection partielle d'un fichier déclare ce qu'elle omet** : chemin, nombre total de lignes,
      et nombre de lignes au-dessus et en dessous de la fenêtre (décision 29).
- [ ] **Republier un résultat déjà calculé ne le compte jamais deux fois** : l'identité logique du résultat
      est déterministe, l'identité de transport est renouvelée à chaque tentative (décision 30).
- [ ] **La famille `memory` est alimentée dès le socle** : tout nœud `blocked` avec sa cause mécanique, tout
      invariant rejeté comme tautologique et toute proposition récurrente y laissent une entrée indexée par
      empreinte de contrat, projetée dans le contexte de nœud. Écrire la mémoire ne dépend pas de
      `refinery`, qui reste éteint (décision 31).

## Critères de succès de la campagne

- [ ] Au moins **cinq outils MCP** livrés, tous verts sur leurs invariants et leur schéma.
- [ ] Le serveur MCP démarre et répond au protocole sans correction manuelle.
- [ ] Au moins un outil construit par le système est **réutilisé** par une étape ultérieure.
- [ ] Le taux de missions atteignant la borne murale sans produire un seul nœud vert reste sous **20 %**.
- [ ] Aucune régression du produit n'atteint `main` sans être détectée par la gate de régression.

## Décisions différées

- Contenu exact du `seed` et des premiers outils du noyau.
- Valeur définitive de la borne murale et de l'intervalle de réveil, après mesure des dix premières missions.
- Ouverture du dashboard au LAN — **la politique existe désormais** (décision 27), seule la décision
  d'ouvrir reste différée.
- Passage éventuel d'une nano-étape en mode agentique (exécuteur de feuille LangGraph) si le mode direct plafonne.
