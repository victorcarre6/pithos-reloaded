# Pithos Reloaded

Expérience d'autonomie logicielle sur modèle local souverain. Un harness décompose dynamiquement le travail
jusqu'à la **nano-étape vérifiable**, et un modèle 8B local n'exécute que des actes atomiques. La campagne
construit une boîte à outils MCP générique pour agents.

Reprise de [Pithos v1](../pithos) après audit : même objectif, unité de travail et autorité de validation
différentes.

**Le développement se fait module par module, par des agents successifs.**
Point d'entrée d'un agent : [`AGENTS.md`](AGENTS.md) → `src/<module>/STATE.md` → `src/<module>/MODULE.md`.

```text
AGENTS.md                protocole de développement — à lire en premier
src/<module>/MODULE.md   le contrat complet d'un module : autorité, interface, interdits,
                         cible, reprises avec leurs sources, critères, double, « fini quand »
src/<module>/STATE.md    l'état de reprise, maintenu par l'agent — jamais supprimé

docs/QUICK_CATCH.md      où en est le projet, prochaines étapes, commandes utiles — à lire en 2 min
docs/PROJECT.md          périmètre, contraintes, 27 critères de socle — canonique, figé
docs/EXPLANATIONS.md     33 décisions et leur raisonnement, puis le journal de laboratoire
docs/ARCHITECTURE.md     les 11 modules, la méthode de développement, la stack
docs/ROADMAP.md          spikes, jalon « premier vert », puis P0 à P9

resources/MANIFEST.md    les 9 dépôts de référence : taille, licence, fiabilité d'extraction
resources/IMPORT_REPORT.md  ~800 reprises retenues sur ~1 180 : Villani (A), Pi (B), Kilo (C), Ouroboros (D),
                            Prime Agent (E), Unsloth (F), OpenHands (G), SWE-agent (H), Langfuse (I)
```

**Onze modules, dépendances strictement descendantes.** Trois règles portent la découpe, et chacune est un
test de graphe d'imports :

```text
verifier   n'importe jamais le modèle, et n'a d'I/O que sur ce qu'il a produit
bridge     n'importe jamais la boucle
broker     est le seul module par lequel une donnée quitte la machine
```

```sh
pyenv activate pithos                    # Python 3.12.9, figé dans pyproject.toml
pip install -r requirements.txt
```

**État : cadrage terminé, aucune implémentation.** Voir `docs/ROADMAP.md` § S — sept spikes conditionnent
l'architecture — puis § M, le scaffold et le jalon « premier vert ».

Cible : **~5 230 lignes de harness Python**, dont une part majoritaire portée plutôt qu'écrite.
