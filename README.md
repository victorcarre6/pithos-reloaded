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

resources/MANIFEST.md    les 11 dépôts de référence : taille, licence, fiabilité d'extraction
resources/IMPORT_REPORT.md  ~800 reprises retenues sur ~1 180 : Villani (A), Pi (B), Kilo (C), Ouroboros (D),
                            Prime Agent (E), Unsloth (F), OpenHands (G), SWE-agent (H), Langfuse (I),
                            GVS5H (J), Graphify (K) — intégrations sélectives
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

**État au 15:09 : les onze modules contiennent du code ; aucun n'est déclaré fini.** La suite complète
a passé **1 602 tests** dans Python 3.12.9 / pithos ; voir [QUICK_CATCH.md](docs/QUICK_CATCH.md)
pour les mesures, skips et limites. Le dashboard est déclaré terminé pour le moment.

**Premier vert avec Ollama local** : le [banc audio](experiments/visualizer/README.md) utilise désormais
`unit_projection` pour vérifier la projection exacte sur [0, 1]. `trial-25ugxn94` passe en **44,898 s**
avec trois gates, un reçu durable, un effet confirmé et le fichier corrigé conservé sans commit.
L'ancien refus `trial-44kcg6ig` reste intact. Walk, flow, GreenFinalizer et custody sont composés
et testés sur runtime local avec modèle simulé ; le nouveau trial ne finalise pas de commit Git.

## Observatoire local

Deux terminaux depuis la racine, dans `pithos` et avec **Node 26+** :

```sh
# API de lecture, 127.0.0.1:8823
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m observatory --runs-root experiments/visualizer/runs
```

```sh
# dépendances web verrouillées, puis build servi sur 127.0.0.1:5173
npm --prefix src/observatory/web ci
npm --prefix src/observatory/web run build
npm --prefix src/observatory/web run preview
```

Ouvrir [le dashboard](http://127.0.0.1:5173). Lecture seule, actualisation toutes les 10 secondes,
essais réels séparés des selftests/probes et des refus d'admission. Artefacts et chronologie paginés ;
tokens mesurés séparés des estimations, capacité avec provenance. Aucun collecteur ni service externe.
Tests et proxy HTTP vérifiés ; validation visuelle encore à faire, aucun navigateur accessible à l'agent.

Cible : **~5 230 lignes de harness Python**, dont une part majoritaire portée plutôt qu'écrite.


## Lancer Pithos avec le TUI

Depuis la racine, dans le venv `pithos` :

```sh
PYTHONDONTWRITEBYTECODE=1 python src/main.py selftest --case green
PITHOS_CONTEXT_WINDOW=16384 PYTHONDONTWRITEBYTECODE=1 python src/main.py probe
PITHOS_CONTEXT_WINDOW=16384 PYTHONDONTWRITEBYTECODE=1 python src/main.py trial \
  --repo experiments/visualizer/workspace --seconds 180
```

L'entrée unique affiche quatre panneaux fixes : **Projet**, **Inférence**, **Travail actuel** et
**Activité récente**. Les arguments du banc restent disponibles. `--no-tui` désactive le suivi ;
une sortie redirigée conserve automatiquement le JSON seul. Les prérequis du dépôt cible et les
limites de cette nano-étape sont décrits dans le [README du banc](experiments/visualizer/README.md).
