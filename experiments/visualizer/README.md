# Banc audio local

État au **13:09** : trois scénarios passent avec engine, workspace, verifier et journal réels.
Le modèle est scénarisé et les observations Git simulées dans `selftest`. La sonde Ollama réelle passe.
Le dépôt dédié a été initialisé par l'opérateur (HEAD `57e47c5`). Le trial réel `trial-44kcg6ig`
est bloqué sur **tautology** : candidat conforme, invariant vert, trois variantes survivantes,
aucun reçu et fichier restauré à l'octet près après 35,021 s. Ce rejet est une preuve conservée.

Le [cadrage](PROJECT.md) adapte l'idée du précédent visualiseur audio. Le premier exercice porte sur
`clamp_level`, avec l'invariant d'idempotence. Un vert ne démontre pas les bornes exactes [0, 1].

## Rejouer les régressions locales

Depuis la racine du harness, dans le venv pyenv `pithos` :

```sh
python -V  # Python 3.12.9
PYTHONDONTWRITEBYTECODE=1 python src/main.py selftest --case green
PYTHONDONTWRITEBYTECODE=1 python src/main.py selftest --case rejected
PYTHONDONTWRITEBYTECODE=1 python src/main.py selftest --case receipt_refused
```

Chaque commande crée un répertoire neuf dans `runs/`, conservé même sur échec. `result.json` donne
statut, cause, empreintes avant/après, présence du reçu et composants réels/simulés. `events.jsonl`,
`tree.json` et les répertoires `invariant-*` conservent les preuves détaillées. Les scénarios négatifs
rendent 0 quand le rejet et la restauration attendus sont constatés ; un essai réel rouge rend 1.

## Préparation du dépôt dédié — réalisée le 13:09

`workspace/audio_visualizer.py` contient une copie exacte du seed après rollback ; son dépôt est propre.
L'opérateur a exécuté l'initialisation ci-dessous. **Ne pas la relancer pour le dépôt actif.**
Ces commandes restent une référence pour une nouvelle copie ; aucun agent ne les a exécutées,
conformément à [AGENTS.md § 7](../../AGENTS.md#7-git--tu-ne-commites-jamais) :

```sh
git -C /Users/victorcarre/code/pithos_reloaded/experiments/visualizer/workspace init -b main
git -C /Users/victorcarre/code/pithos_reloaded/experiments/visualizer/workspace add audio_visualizer.py
git -C /Users/victorcarre/code/pithos_reloaded/experiments/visualizer/workspace commit -m "visualizer: seed du premier essai"
```

Le banc exige un HEAD, un dépôt propre et le seed inchangé. Il refuse le dépôt du harness comme cible.
Le résultat vert reste une modification locale à examiner ; le banc ne commite pas.

## Sonde et essai avec Ollama

La route `/v1/models` expose le modèle mais pas sa fenêtre. `ollama show` a rendu `num_ctx 16384`
pour `pithos/ling-3.0-tiny:8b-16k`. La variable suivante transmet cette configuration vérifiée ;
la capacité reste étiquetée **asserted**, jamais `confirmed` par la route.

```sh
ollama show pithos/ling-3.0-tiny:8b-16k --parameters
PYTHONDONTWRITEBYTECODE=1 PITHOS_CONTEXT_WINDOW=16384 python src/main.py probe
PYTHONDONTWRITEBYTECODE=1 PITHOS_CONTEXT_WINDOW=16384 python src/main.py trial \
  --repo /Users/victorcarre/code/pithos_reloaded/experiments/visualizer/workspace \
  --seconds 180
```

`trial` sonde à nouveau la capacité avant d'ouvrir la tentative. `--seconds` porte sur la tentative,
après cette admission ; le contrôle du schéma de sonde possède sa propre limite de 60 secondes.
La réserve de finalisation vaut 5 secondes. Le marcheur complet, sa reprise après interruption et sa
borne murale globale restent à livrer ; ce script exerce une seule tentative.

Après un essai vert, préparer une nouvelle copie et un nouveau dépôt pour une autre trajectoire.
Ne pas effacer les résultats précédents pour réutiliser un identifiant. Les fichiers de reprise et
les mesures observées sont dans [STATE.md](STATE.md).

## Observer les essais — 13:09

Le [dashboard local](../../README.md#observatoire-local) indexe directement `runs/`.
Ouvrir `trial-44kcg6ig` pour lire l'arbre, les cinq gates, les sources candidates, la chronologie
et la capacité asserted. Les prochains essais ajoutent un rapport de vérification durable et
la durée de chaque appel ; les anciennes traces ne sont jamais réécrites pour combler ces champs.


## Affichage terminal — 13:09

`src/main.py` est l'entrée recommandée. `experiments/visualizer/run.py` reste compatible et utilise
le même parseur et le même exécuteur. Aucun deuxième moteur ni nouvelle dépendance n'est ajouté.

- **Projet** : mode/scénario, dépôt, fonction cible, identifiant du run, preuves et budget de tentative.
- **Inférence** : modèle observé, appels journalisés, tokens d'entrée/sortie/total et tours candidats.
  Les tokens viennent de l'usage rendu par la route, disponible à réception car bridge ne streame pas.
  Les compteurs incluent la sonde ; la répétition du candidat par engine ne recompte pas ses tokens.
  `n/d` signale une mesure absente, notamment dans `selftest` ; une somme incomplète est signalée.
- **Travail actuel** : phase, nœud, motif, activités du harness, exécutions d'invariants et reçus.
  Ce banc n'utilise pas les `tool_calls` du modèle : il demande du JSON strict. `splice` et `write`
  sont donc présentés comme opérations du harness, avec leur nom dans l'activité récente.
- **Activité récente** : derniers événements durables, bornés à la place disponible ; les traces
  complètes restent dans `events.jsonl`. Les chemins longs peuvent être coupés à l'écran.

Les panneaux se rafraîchissent cinq fois par seconde et suivent la taille du terminal. En dessous
de 60 colonnes × 22 lignes, une vue compacte garde la phase et les compteurs. `TERM=dumb`, une sortie
redirigée ou `--no-tui` désactivent les séquences terminal. Le JSON final reste identique et exploitable.
En terminal interactif, un résumé des compteurs reste sur stderr après fermeture des panneaux,
y compris quand la dernière réponse arrive entre deux rafraîchissements.

`Ctrl+C` interrompt le run dans son thread principal : une transaction modifiée restaure ses octets
avant la capture de `KeyboardInterrupt`. Le rapport conserve `status: interrupted`, le processus rend
**130** et le curseur est restauré. Ce comportement ne fournit pas la réconciliation du marcheur ni une
reprise automatique des nœuds `running`. Les preuves précédentes ne sont jamais effacées.
