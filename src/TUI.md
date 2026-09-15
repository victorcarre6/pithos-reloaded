# TUI — entrée Pithos

**Mise à jour** : 15:09
**État** : livré pour les commandes du banc audio ; une nano-étape par `trial`.

[`main.py`](main.py) lance Pithos avec quatre panneaux fixes. Il partage le parseur et
l'exécuteur de [`experiments/visualizer/run.py`](../experiments/visualizer/run.py).
[`tui.py`](tui.py) assure uniquement l'affichage, avec la bibliothèque standard Python.

## Lancer un run

Depuis la racine du dépôt, dans le virtualenv pyenv **pithos / Python 3.12.9** :

```sh
# environnement
pyenv activate pithos
python -V

# régressions locales : modèle scénarisé et Git simulé
PYTHONDONTWRITEBYTECODE=1 python src/main.py selftest --case green
PYTHONDONTWRITEBYTECODE=1 python src/main.py selftest --case rejected
PYTHONDONTWRITEBYTECODE=1 python src/main.py selftest --case receipt_refused

# admission du modèle Ollama local
PITHOS_CONTEXT_WINDOW=16384 PYTHONDONTWRITEBYTECODE=1 python src/main.py probe

# nano-étape avec modèle et observations Git réels
PITHOS_CONTEXT_WINDOW=16384 PYTHONDONTWRITEBYTECODE=1 python src/main.py trial \
  --repo experiments/visualizer/workspace --seconds 180

# sortie JSON sans affichage dynamique
PYTHONDONTWRITEBYTECODE=1 python src/main.py selftest --no-tui
```

`trial` exige un dépôt Git dédié, propre, avec un HEAD et le seed inchangé. Il refuse le dépôt
du harness comme cible. La fenêtre `16384` est une configuration précédemment vérifiée pour
le modèle local, transmise avec provenance **asserted**. Les prérequis et les commandes de
préparation sont dans le [README du banc](../experiments/visualizer/README.md).

| Commande / option | Comportement |
|---|---|
| `selftest --case green` | Vérifie un candidat accepté, un fichier modifié et un reçu durable ; cas par défaut |
| `selftest --case rejected` | Vérifie le rejet par invariant et la restauration des octets |
| `selftest --case receipt_refused` | Vérifie la restauration quand le reçu n'est pas acquitté |
| `probe` | Éprouve la capacité du modèle local à rendre un critère conforme |
| `trial --repo CHEMIN` | Exécute une tentative sur le dépôt dédié |
| `--seconds N` | Budget de la tentative, par défaut 180 s, après la sonde d'admission |
| `--no-tui` | Désactive le TUI ; accepté avant ou après la sous-commande |

L'ancien lanceur `python experiments/visualizer/run.py …` reste disponible avec sa sortie JSON.

Le banc utilise désormais `unit_projection` pour les nouveaux essais. Le panneau Projet
affiche « projection [0, 1] » ; le rapport JSON expose le critère exact. Les résultats de
validation du 13:09 ci-dessous restent historiques.

## Lire les panneaux

```text
┌ Projet ─────────────────────┐┌ Inférence ──────────────────┐
│ mode, dépôt, cible, run      ││ modèle, appels, tokens      │
│ preuves, budget de tentative ││ tours candidats reçus/lancés│
└─────────────────────────────┘└─────────────────────────────┘
┌ Travail actuel ───────────────────────────────────────────┐
│ phase, nœud, motif, activités outils, invariants, reçus     │
└───────────────────────────────────────────────────────────┘
┌ Activité récente ─────────────────────────────────────────┐
│ derniers événements durables : running, splice, write…    │
└───────────────────────────────────────────────────────────┘
```

| Indicateur | Source et sens |
|---|---|
| Appels modèle | Événements de transport portant `endpoint`, sonde comprise |
| Tokens entrée / sortie / total | Champs `usage` rendus par la route ; la copie du candidat dans engine n'est pas recomptée |
| Tours reçus / lancés | Événements engine `candidate_response` / `running` ; une réponse reçue n'est pas nécessairement acceptée |
| Activités outils | Événements `tool_activity` du harness, notamment `splice` et `write` |
| Invariants exécutés | Rapports `invariant-*/result.json` présents ; le compteur ne distingue pas leur verdict |
| Reçus | Événements `validation` effectivement journalisés |
| Temps affiché | Temps écoulé depuis la création de l'affichage, admission comprise |

**Les tokens ne sont pas streamés.** Ils apparaissent à réception de la réponse. `n/d` signifie
qu'aucune mesure n'est disponible ; les sommes partielles sont signalées. `selftest` utilise un
modèle scénarisé et ne fournit pas d'usage réel. Le banc demande du JSON strict : les opérations
du harness ne sont pas des `tool_calls` émis par le modèle.

## Terminal et sorties

- Rafraîchissement toutes les **0,2 s**, avec relecture de la taille du terminal.
- Les quatre panneaux nécessitent au moins **61 colonnes × 22 lignes** physiques : une colonne
  reste réservée pour éviter le retour automatique. En dessous, une vue compacte prend le relais.
- Les chemins et l'activité récente sont bornés à la place disponible ; les preuves complètes restent sur disque.
- Une sortie non TTY, `TERM=dumb`, un `TERM` absent ou `--no-tui` désactivent les séquences ANSI.
- À la fermeture, l'écran principal et le curseur sont restaurés. En mode interactif, un résumé
  des compteurs reste sur **stderr**, y compris si la dernière réponse arrive entre deux frames.
- Le rapport final est écrit dans **result.json**, puis imprimé sur **stdout**.

Chaque invocation crée un nouveau répertoire sous `experiments/visualizer/runs/`. Les preuves
comprennent, selon l'avancement, `events.jsonl`, `live.log`, `tree.json`, les rapports d'invariant
et `result.json`. Une dernière ligne JSONL incomplète est signalée et exclue des compteurs.

| Code de sortie | Signification |
|---|---|
| `0` | Scénario selftest conforme, sonde utilisable ou trial accepté |
| `1` | Échec du scénario, sonde inutilisable, trial refusé ou erreur du banc |
| `2` | Arguments refusés par argparse |
| `130` | Interruption `Ctrl+C` capturée pendant l'exécution |

Un selftest négatif conforme rend donc **0**, même si le nœud est `blocked`.

## Architecture et interruption

Le run reste dans le **thread principal**. Un thread de présentation relit les traces et
construit les panneaux : `snapshot()` projette les preuves, `frame()` compose l'écran,
`Dashboard` gère le rafraîchissement et la fermeture du terminal.

Sur `Ctrl+C` pendant le run, les context managers transactionnels se ferment avant la capture
de `KeyboardInterrupt`. Une modification encore sous transaction est restaurée ; le rapport
porte `status: interrupted`. Les preuves antérieures restent conservées.

Ce lanceur n'ajoute ni boucle de mission, ni streaming, ni reprise automatique d'un nœud `running`.
Le marcheur et sa réconciliation restent suivis dans [engine/STATE.md](engine/STATE.md).

## Validation observée

Mesures de livraison du **13:09**, dans Python **3.12.9 / pithos** :

- **23 tests ciblés**, en **6,21 s** : compatibilité CLI, effets disque, compteurs, rendu,
  interruption et usage reçu entre deux frames.
- **1 444 tests de suite complète**, **3 skipped**, **7 warnings**, en **44,62 s**.
- Contrôle des onze `STATE.md` et `git diff --check` verts.
- Vrai `SIGINT` envoyé après splice dans un **pseudo-terminal** : octets du seed retrouvés,
  rapport durable, code 130 et curseur restauré. Le modèle de cet essai reste scénarisé.

Ces résultats sont ceux de la livraison, pas d'une nouvelle exécution pour rédiger ce document.
Les preuves positives et négatives sont dans le [STATE du banc](../experiments/visualizer/STATE.md).
Les commandes proposées pour l'historique sont dans [GIT.md](GIT.md).

```sh
# rejouer les contrôles depuis la racine
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  tests/test_main.py tests/test_visualizer_trial.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -rs -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 python -m tests.state_check
git diff --check
```
