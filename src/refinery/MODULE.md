# `refinery` — la politique d'auto-amélioration

> **Lis [`AGENTS.md`](../../AGENTS.md) avant de commencer.** Ce fichier est ton contrat complet : tu ne
> devrais pas avoir besoin d'ouvrir `docs/`. Ton point d'entrée exact est la rubrique « Prochaine action » de
> [`STATE.md`](STATE.md), à côté de ce fichier.
>
> **Tu ne commites, ne pousses et ne merges jamais.** Tes commits se *proposent* dans [`git.md`](git.md),
> avec les `ga`/`gcmsg` exacts — voir [`AGENTS.md`](../../AGENTS.md) § 7.

**Cible** : ~100 L · **`enabled: false` au socle** · ratchet **shrink-only**
**Dépend de** : `kernel`, `journal`, `verifier`, `bridge`, `workspace`, `engine`, `campaign`.
**Niveau de dépendance** : 5 — le plus haut.
**Stack** : Pydantic v2. Aucune dépendance nouvelle.

## 1. Autorité — et pourquoi ce module est éteint

`refinery` propose des modifications du harness lui-même — entrées `prompt` et `memory` — et **décide si
elles ont le droit de devenir actives**. Il est `enabled: false` au socle : activation après mesure sur les
dix premières missions.

> **Ce module reste séparé pour une raison précise :** son `MODULE.md` porte **par écrit** pourquoi il est
> éteint et ce qui conditionne son allumage. Une politique invisible dans `campaign` s'allumerait un jour
> sans que personne ne relise sa condition.

⚠️ **N'active rien** !
→ Si tu es l'agent affecté à ce module avant que la condition d'allumage soit remplie, ton travail est de
l'écrire et de **le laisser éteint**.

## 2. Interface publique

```python
def plan_refinement(store: Store, baseline: Baseline) -> list[Edit]:
    "Plan DÉTERMINISTE, zéro appel modèle. L'appel modèle est un dernier recours."

def gate(edit: Edit, before: Baseline, after: Baseline) -> Decision:
    "L'apport propre du projet. Un edit reste en `shadow` tant qu'il n'a pas démontré
     un effet mesurable sur le taux de nœuds verts."
```

## 3. Interdits

- **N'active pas le module.** `enabled: false` est une décision, pas un défaut de configuration.
- **Ne possède aucun magasin.** Le magasin appartient à `campaign` — un fichier, un propriétaire. Rollback
  par reconstruction inverse, application par cas fermés, injection bornée par famille, label mobile : ce
  sont des opérations **du magasin**, donc de `campaign`.
- **L'entrée de base est immuable.** Un edit visant la politique de base est **refusé mécaniquement**. Trois
  lignes qui séparent « s'améliore » de « se détruit ».
- **L'`evidence` d'un raffinement est un identifiant de nœud plus un verdict d'invariant**, jamais une
  rationale générée par le modèle.

## 4. Ce que ce module apporte, et que personne n'a

**Prime Agent est le seul des neuf dépôts à implémenter l'auto-amélioration au fil du cycle de vie de bout en
bout.** Et il le fait **en boucle ouverte** : `expectedOutcome` n'est jamais évalué. L'agent se réécrit sans
jamais vérifier que ça l'améliore.

> **Nous avons l'autorité de validation qui manque exactement là.**
> C'est **la combinaison** qui est neuve, pas la moitié qu'on importe.

La gate d'effet est le mutation-check transposé du code vers le contexte : un edit reste en `shadow` tant
qu'il n'a pas démontré un effet mesurable sur le taux de nœuds verts.

## 5. La baseline, et pourquoi elle est déjà mesurée

**`engine` écrit à chaque fin de mission le triplet qui constitue la baseline** — nœuds verts / nœuds
tentés, temps mural consommé, cause de sortie — **dès la mission 1**, alors que ce module est éteint.

Sans cela, activer la gate au bout de dix missions reviendrait à **comparer un chiffre à rien**. C'est ~5 L
dans une trace qui existe déjà, et c'est la condition qui rend ce module utile un jour.

## 6. Trois réglages inversés par rapport à Prime Agent

| Prime Agent | Nous | Pourquoi |
|---|---|---|
| auto-refine **activé par défaut**, tous les 25 tours | **`enabled: false`**, activation après dix missions | prudence sur un 8B |
| cooldown de **20 minutes** | compté en **nœuds terminés**, pas en minutes | notre borne est murale, pas horaire |
| raffinement **pendant** la session | **en fin de mission**, après finalisation, avant le rapport | la décision 8 exige de finaliser les nœuds verts d'abord |

## 7. Contenu

| Fichier | Contenu | ~L |
|---|---|---:|
| `propose.py` | plan de raffinement déterministe, appel modèle en dernier recours | 50 |
| `gate.py` | la gate d'effet : `shadow` → `active` sur effet mesuré | 50 |

## 8. Conditions d'allumage — à vérifier avant de passer `enabled: true`

- [ ] Dix missions ont tourné et leur triplet de baseline est écrit.
- [ ] Le taux de nœuds verts par mission est **stable ou en progression** — un système qui régresse ne doit
      pas commencer à se réécrire.
- [ ] La gate d'effet a été testée contre les données **réelles** de ces dix missions, pas contre des
      données simulées.
- [ ] Le versionnement à label mobile est en place dans `campaign` : le contenu est **versionné et jamais
      modifié**, et **seul le déplacement du label `active` est l'acte que la gate contrôle**.
- [ ] Un humain a relu la liste des edits que `plan_refinement` proposerait sur ces dix missions.

## 9. Le double

`tests/doubles/refinery.py` — trivial, `refinery` étant en bout de chaîne et éteint. L'essentiel du test est
l'inverse : `gate` se teste contre des baselines fabriquées, avec au minimum un cas d'**amélioration**, un
cas de **régression**, et un cas de **variation dans le bruit** — ce dernier devant laisser l'edit en
`shadow`.

## 10. Fini quand

- [ ] `plan_refinement` est **déterministe** : deux appels sur le même magasin rendent le même plan, et
      aucun appel modèle n'est fait — test qui échoue si un client de modèle est instancié.
- [ ] Un edit visant l'entrée de base est **refusé mécaniquement**.
- [ ] La gate laisse en `shadow` un edit dont l'effet est dans le bruit.
- [ ] La gate promeut un edit dont l'effet sur le taux de nœuds verts est mesurable, et **seulement** en
      déplaçant le label `active` — le contenu versionné n'est jamais modifié.
- [ ] Un edit invalide est **enregistré et non fatal**.
- [ ] Le module reste **`enabled: false`** : un test vérifie qu'aucun chemin d'exécution du socle ne
      l'appelle.
- [ ] L'`evidence` d'un événement de raffinement est un identifiant de nœud + un verdict d'invariant, jamais
      une rationale générée.
- [ ] `tests/boundaries/` confirme que `refinery` n'est importé par aucun autre module.

## 11. Pièges connus

- **`serializeConversation(...).slice(-80_000)` de Prime Agent est inapplicable** : nous n'avons pas de
  trajectoire, et 80 Ko ne rentrent pas dans 16 k.
- **Le raffinement tourne en fin de mission**, après finalisation des nœuds verts, avant le rapport. Jamais
  pendant.
- **Une entrée de magasin atteint le *prompt*, jamais l'*exécution*.** C'est la frontière qui rend ce module
  compatible avec la contrainte dure n°1 — elle porte sur les littéraux exécutés, pas sur ce que le modèle
  lit. Énonce-la dans le code, ne la laisse pas implicite.

---

## Sources — reprises retenues

**35 lignes.** Chaque pointeur se lit dans `resources/`. Le détail complet et le contexte de chaque partie sont dans [`resources/IMPORT_REPORT.md`](../../resources/IMPORT_REPORT.md).
**Lis la source avant de porter.** Une reprise collée sans être relue est un défaut.

#### E — Prime Agent · `resources/prime-agent-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| E3.6 | `refinery/store` | `HarnessEntry` / `RefinementEvent` en dataclass. À passer en Pydantic v2 — la structure est la bonne. | **Copier** |
| E3.6 | `refinery/store` | `load()` **défensif champ par champ** : type faux ⇒ défaut, `title`/`content` non-`str` ⇒ entrée sautée, fichier corrompu ⇒ état vide. **Un magasin écrit par un modèle doit se relire sans jamais lever.** | **Copier** |
| E3.6 | `refinery/store` | `_sync_from_disk` — relit si le `st_mtime_ns` a bougé. **Le kernel garde l'état en mémoire pendant que le host réécrit le même fichier** ; chez nous, dashboard, broker Git et mission concourent. | **Copier** |
| E3.6 | `refinery/store` | Une entrée `skill` **doit** porter un import et un callable. **Une capacité non appelable n'entre pas au registre.** | **Copier** |
| E3.6 | `refinery/store` | `_strip_scope_prefix` — accepte verbatim les ids affichés `local:`/`global:`. **Le modèle recopie ce qu'il a lu ; le harness le tolère au lieu de le refuser.** | **Copier** |
| E3.6 | `refinery/store` | `overview()` — rendu texte compact borné par famille, `args=`/`ref=` tronqués. C'est ce qui entre dans le prompt. | **Copier** |
| E3.6 | `refinery/propose` | `plan_refinement` — plan **déterministe en trois étapes, zéro appel modèle** : diagnostiquer / modifier la plus petite entrée utile / rejouer et enregistrer. | **Copier** |
| E3.6 | `refinery/store` | Mode `in_memory` comme **repli sûr quand la résolution de chemin échoue** : construire le repli ne peut pas relever l'erreur d'origine. | **Copier** |
| E3.6 | `ca/core/refinement/refinement.ts:680-682` | **Immuabilité du prompt de base** — trois lignes qui séparent « s'améliore » de « se détruit ». | **Traduire** |
| E3.6 | `refinery` | Application pure sur l'état passé ; edit invalide **enregistré et non fatal** ; conflit détecté par état de base capturé avant l'appel. | **Adapter** |
| E3.6 | `refinery` | **Rollback par reconstruction inverse** depuis les `before`/`after`, en ordre inverse. | **Adapter** |
| E3.6 | `refinery` | Rendu **borné par famille** (6 entrées), compteur de débordement `+N more`, et les **cinq derniers raffinements visibles dans le prompt** — l'agent voit son propre historique d'amélioration. | **Adapter** |
| E3.6 | `refinery` | Politique de portée (local par défaut) et **table de routage vers la plus petite famille pertinente** : délégation récurrente ⇒ subagent, procédure récurrente ⇒ skill, fait ⇒ memory. | **Traduire** |
| E3.6 | `refinery` | `loadHarnessState` s'exécute **à chaque construction de prompt** ; corrompu ⇒ état vide. `mergeHarnessStates` superpose avec préfixage **seulement en cas de collision**. | **Adapter** |
| E3.6 | `ca/core/goals.ts:125-181` | **Le modèle voit son budget restant**, il ne le devine pas. Un objectif persistant se réinjecte par un message de contexte, pas par mutation du prompt. | **Traduire** |
| E3.6 | `ca/core/goals.ts:75-94` | Objectif borné à 4 000 caractères, budget entier positif. **Validation à l'entrée, pas à l'usage.** | **Traduire** |


#### I — Langfuse · `resources/langfuse-main/`

| § | Source | Notion | Verdict |
|---|---|---|---|
| I4.6 | `web/src/features/mcp/core/define-tool.ts:112` | **Définition d'outil et validation runtime au même endroit** ; Pydantic reste la source unique, l'accord schéma/handler est testé. | **Adapter** |
| I4.6 | LF046 | Profil de schéma MCP **explicitement restreint** — rejette unions et intersections, exige un objet. Choix de serveur, pas interdiction du protocole. | **Adapter** |
| I4.6 | `web/src/features/mcp/server/registry.ts:82` | **Registre explicite, collisions détectées avant publication**, y compris à l'intérieur d'un même lot. | **Adapter** |
| I4.6 | LF048 | **La gate de disponibilité s'applique à l'appel direct**, pas seulement à la découverte. Masquer n'est pas interdire. | **Adapter** |
| I4.6 | LF049 | Permission de lecture ou allowlist — **ne pas faire confiance à un `readOnlyHint` fourni par du code généré**. | **Adapter** |
| I4.6 | `web/src/features/mcp/core/run-mcp-tool.ts:13` | Instrumentation par outil et **classe de faute** : requête invalide distincte de panne serveur. | **Adapter** |
| I4.6 | `packages/shared/src/server/repositories/dataset-items.ts:285` | **Valider l'état fusionné après un update partiel** ; distinguer champ absent et `null` explicite. | **Adapter** |
| I4.6 | LF052 | **Lecture à version temporelle figée** — comparer deux configurations sur le même corpus. | **Adapter** |
| I4.6 | `worker/src/features/experiments/experimentServiceClickhouse.ts:73` | Identité d'item et tentative **reliées au run**, items existants retrouvés au redémarrage. | **Adapter** |
| I4.6 | `worker/src/features/experiments/scheduleExperimentEvals.ts:37` | **Planification best-effort** : l'erreur est loggée sans invalider l'appelant. À écarter pour une gate de livraison. | **Adapter** |
| I4.6 | `web/src/features/prompts/server/actions/createPrompt.ts:93` | **Version créée avec ses dépendances, publiées ensemble.** | **Adapter** |
| I4.6 | LF056 | **Label mobile séparé d'une version immuable** — notre paire `shadow`/`active`, où seul le déplacement du label passe la gate. | **Adapter** |
| I4.6 | `packages/shared/src/server/services/PromptService/index.ts:242` | Graphe de dépendances **borné en cycles et profondeur** ; tracer **les versions réellement résolues**, pas le nom de la racine. | **Adapter** |
| I4.6 | LF058 | Génération de cache invalidant un ensemble **sans supprimer toutes les clés** ; résolution des créations concurrentes par « premier gagnant ». | **Adapter** |
| I4.6 | LF059 | **Clé de cache distinguant label et version** — sinon la version `2` et le label `"2"` collisionnent. Décision 22 appliquée au cache. | **Adapter** |
| I4.6 | LF060 | **Un échec secondaire après commit ne doit pas faire croire à un échec de la création durable** — ni provoquer un doublon. | **Adapter** |
| I4.6 | `worker/src/features/evaluation/deterministicSampling.ts:6` | **Cohorte déterministe par hash** : SHA-256, 53 premiers bits, seuil demi-ouvert. Une cible garde sa cohorte. | **Adapter** |
| I4.6 | `web/src/features/score-analytics/server/buildScoreComparisonQuery.ts:50` | Comparer candidat et base **sur les mêmes missions, corpus et versions**, en affichant appariés, manquants et dénominateur. | **Adapter** |
| I4.6 | LF093-098 | Vecteur de référence de hash, **cohortes emboîtées quand le taux augmente**, export multichunk **décompressé à l'octet près**, champ nommé `anyOf` restant légal comme donnée, résistance aux IDs dupliqués, **enfant asynchrone terminant après son parent**. | **Adapter** |

