# Banc audio local

Historique du **13:09** : trois scénarios passent avec engine, workspace, verifier et journal réels.
Le modèle est scénarisé et les observations Git simulées dans `selftest`. La sonde Ollama réelle passe.
Le dépôt dédié a été initialisé par l'opérateur (HEAD `57e47c5`). Le trial réel `trial-44kcg6ig`
est bloqué sur **tautology** : candidat conforme, invariant vert, trois variantes survivantes,
aucun reçu et fichier restauré à l'octet près après 35,021 s. Ce rejet est une preuve conservée.

**Depuis le 15:09**, le [cadrage](PROJECT.md) impose `unit_projection` aux nouveaux essais :
identité dans [0, 1], saturation aux extrémités, sortie numérique bornée et idempotence, avec
comparaisons exactes. Les bornes et les entrées appartiennent au harness. Hypothesis est complété
par des exemples fixes aux frontières ; un vert reste une vérification finie du contrat.
Le candidat archivé passe sous ce nouveau critère ; ce rejeu n'émet pas de reçu et ne rappelle pas Ollama.

**Premier vert réel le 15:09** : `trial-25ugxn94`, **44,898 s** pour la tentative, deux appels
Ollama et 3 350 tokens rapportés, trois gates (rouge avant, vert après, mutant tué), un reçu durable
avec `effect: confirmed`. Le fichier corrigé est conservé dans `workspace/`, sans commit.
Cette nano-étape réelle ne constitue pas une mission Prefect finalisée : `tree.finalized` reste vide.
L'ancien trial refusé et ses 44 fichiers sont inchangés.

## Rejouer les régressions locales

Depuis la racine du harness, dans le venv pyenv `pithos` :

```sh
python -V  # Python 3.12.9
PYTHONDONTWRITEBYTECODE=1 python src/main.py selftest --case green
PYTHONDONTWRITEBYTECODE=1 python src/main.py selftest --case rejected
PYTHONDONTWRITEBYTECODE=1 python src/main.py selftest --case receipt_refused
```

Chaque commande crée un répertoire neuf dans `runs/`, conservé même sur échec. `result.json` donne
statut, cause, critère exact, portée de preuve, empreintes avant/après, présence du reçu et composants réels/simulés. `events.jsonl`,
`tree.json` et les répertoires `invariant-*` conservent les preuves détaillées. Les scénarios négatifs
rendent 0 quand le rejet et la restauration attendus sont constatés ; un essai réel rouge rend 1.
Le vert propose `max(0.0, min(1.0, level))` ; le rejet propose une projection fautive sur [0, 2].

## Préparation du dépôt dédié — réalisée le 13:09

Au 13:09, `workspace/audio_visualizer.py` était identique au seed après rollback.
**Depuis le vert du 15:09, ce fichier contient la correction non commitée.** Conserver ce résultat
pour examen ; les commandes de nouveaux trial/mission ci-dessous exigent un autre dépôt initialisé
contenant le seed intact. Les lancer sur le workspace vert échouerait à l'admission.
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
La réserve de finalisation vaut 5 secondes. Ce script trial exerce une seule tentative ;
le marcheur et sa reprise sous borne de processus sont disponibles via mission.py, documenté plus bas.

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


## Mission reprenable et finalisation locale — 14:09

`mission.py` compose désormais walk/flow, GreenFinalizer et lifecycle. Ce mode **commite les seuls
changements verts attestés dans le dépôt d'essai**, sans push. Le dépôt doit être initialisé par
l'opérateur, posséder un HEAD et une identité Git locale ; une nouvelle mission exige le seed intact.
`trial` et son affichage historique restent des essais à une tentative sans finalisation Git.

Dans un premier terminal, lancer le serveur Prefect local déjà installé dans `pithos` :

```sh
# serveur explicite, administré par l'opérateur ; aucune analytics serveur
PREFECT_SERVER_ANALYTICS_ENABLED=false \
PREFECT_CLOUD_ENABLE_ORCHESTRATION_TELEMETRY=false \
prefect server start --host 127.0.0.1 --port 4200
```

Dans un second terminal, avec Ollama disponible :

```sh
# même --run lors de chaque reprise ; aucun reset ni effacement
# retirer les variables de proxy, y compris leurs variantes minuscules
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
PYTHONDONTWRITEBYTECODE=1 \
PREFECT_API_URL=http://127.0.0.1:4200/api \
PITHOS_CONTEXT_WINDOW=16384 \
python experiments/visualizer/mission.py \
  --repo experiments/visualizer/workspace \
  --run experiments/visualizer/runs/mission-unit-projection-01 \
  --seconds 180
```

La fenêtre 16 384 reste une déclaration de l'opérateur à confirmer avec `ollama show`, comme pour
trial. Le serveur Prefect existant reste sous sa responsabilité ; le worker ne le démarre ni ne
l'arrête implicitement. Un proxy système actif reste refusé par flow.

`--seconds` inclut le spawn, la sonde et l'enveloppe SDK. Budget conserve une réserve de 5 s ;
le superviseur coupe le groupe au plus tard à la deadline métier + marge de 60 s, hors délais de
confirmation OS. `Ctrl+C`/SIGTERM demandent une interruption douce sous cette borne. Après coupure
dure, le prochain lancement réconcilie les octets et les reçus ; aucun candidat n'est rejoué à l'aveugle.
Un nœud blocked reste bloqué : la reprise n'autorise pas une nouvelle tentative métier implicite.

**Le critère d'une mission est immuable à la reprise.** Un ancien `--run` portant `idempotent`
reste limité à cette propriété ; il peut réconcilier et finaliser son reçu sans devenir une preuve
de projection exacte. Le JSON final expose son champ `criterion`. Pour `unit_projection`, utiliser
un nouveau `--run` avec un seed intact ; le chemin ci-dessus est celui du nouveau jalon.

Les preuves de mission restent dans `--run` (`tree.json`, `events.jsonl`, `effects.json`, gates et
CONTEXT.md). Le verrou et la custody communs au dépôt restent dans son voisin `.workspace.pithos/`
(pour un dépôt nommé workspace). Ne pas supprimer ce répertoire entre deux reprises : il porte les
identités des processus et les archives de verrou. Les noms suivent le dépôt réel, pas le run.
Les attributs Git sur la cible, un index.lock résiduel ou une custody inconnue ferment l'admission.

Validation intégrée : Git, Prefect, verifier, workspace, journal et lifecycle réels sur copies
jetables ; **modèle seul simulé**. Un commit vert est retrouvé après acquittement perdu sans second
commit ni nouvel appel modèle. Rejet et coupure avant reçu restaurent les octets à la reprise.
Depuis le 15:09, le cas vert utilise `unit_projection` et le cas rouge rejette [0, 2] avec rollback exact.
Un cas historique distinct garde un reçu `idempotent` après reprise et l'affiche dans la CLI.
Le trial-25ugxn94 complète ces résultats avec le modèle réel, sans exercer la finalisation Git de mission.


**Custody corrigée le 14:09 — commande réouverte.** La contre-preuve du groupe détaché reste
archivée dans STATE.md. Chaque gate réelle (baseline, candidat, mutants) passe désormais par un
gardien enregistré avant admission, sous le même propriétaire que le worker. Coupure dure pendant
un invariant, arrêt de son descendant et sweep après mort du superviseur sont vérifiés. La reprise
via la CLI constate le commit existant sans nouvel appel modèle. Ces groupes ne constituent pas
une sandbox contre du code hostile créant lui-même d'autres sessions.
