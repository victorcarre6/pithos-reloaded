# Noyau audio — banc d'essai Pithos Reloaded

Mise à jour : **15:09**.

## But

Éprouver une nano-étape de développement sur un petit noyau de visualiseur audio local :
le modèle propose une fonction Python, le harness la vérifie et conserve ou restaure le fichier.
La trajectoire et ses preuves sont le résultat de l'essai.

L'idée vient de `pithos/experiments/visualizer-dry-run/PROJECT.md` : niveaux de bandes,
lissage, puis magnitudes depuis un signal. On ne reprend ni son application, ni son harness,
ni les cases déjà cochées dans cet ancien projet.

## Premier essai : stabiliser un niveau audio

La cible existante `audio_visualizer.py::clamp_level(level)` reçoit un flottant fini.
L'objectif produit est une projection dans l'intervalle [0, 1]. Le seed contient délibérément
une fonction fausse ; le modèle doit en proposer le remplacement, avec la même signature.

**Extension approuvée le 15:09** : les nouveaux essais utilisent
**unit_projection / clamp_level / floats_finite**. Le harness impose les relations suivantes :

- La sortie est numérique, finie, dans [0, 1] ; les booléens sont refusés.
- Les valeurs déjà dans [0, 1] restent identiques, sans tolérance d'arrondi.
- Sous 0, la sortie égale `f(0)` ; au-dessus de 1, elle égale `f(1)`.
- La seconde application ne change pas la sortie.

Les points fixes 0 et 1, leurs voisins flottants immédiats, 0,5, -1, 2 et les extrêmes finis
sont des exemples imposés par le harness, complétés par Hypothesis seedé. Le modèle ne fournit
ni bornes, ni tolérance, ni entrées, ni valeurs attendues. Ce contrat caractérise la projection
exacte ; son exécution reste une vérification sur un ensemble fini, pas une preuve universelle.
Il ne valide pas un visualiseur audio complet.

Le premier banc utilisait seulement **idempotent**, ce qui laissait passer une projection [0, 2].
Les anciens arbres et reçus gardent ce critère. Une reprise les affiche comme tels ; pour éprouver
la projection exacte, créer un nouvel essai ou un nouveau `--run`, sans effacer les preuves.

## Protocole d'essai

1. Créer une copie neuve du seed, garder les preuves hors du dépôt cible.
2. Vérifier le critère avant tout changement ; refuser une relation ou un symbole inexécutable.
3. Demander un objet structuré avec le seul code candidat, pour une fonction choisie par le harness.
4. Revalider la réponse et effectuer un splice atomique de cette fonction existante.
5. Croiser FileFact, SourceFact et RepoFact ; exiger rouge avant, vert après et mutant tué.
6. Compter vert seulement si le reçu lié aux faits a été effectivement écrit.
7. Restaurer les octets sur rejet, erreur, timeout ou absence de reçu ; garder toutes les traces.

## Deux niveaux de banc

- **Régression du harness** : réponse modèle et observations de dépendances scénarisées,
  contrôles verts et négatifs reproductibles. Ne prouve rien sur Ollama.
- **Essai local** : modèle Ollama configuré, dépôt Git de campagne dédié et fichiers réellement
  relus. Sa preuve doit nommer les composants réels et les éventuels substituts.

Aucune initialisation, aucun commit ni publication Git ne sont exécutés par l'agent de développement.
Le banc réel requiert un dépôt dédié déjà initialisé par l'opérateur ; sa commande sera documentée
avec les préconditions effectives. Le dépôt du harness et l'ancien projet ne servent jamais de cible.

## Contraintes

- Python 3.12.9 dans le venv `pithos`, sans dépendance nouvelle.
- Une fonction existante et un fichier cible par tentative ; aucun test modifiable par le modèle.
- Sources, réponses et échecs conservés ; aucune réinitialisation qui efface un essai antérieur.
- Pas d'audio réel, de FFT temps réel, de Canvas, de capture micro ou de thèmes graphiques à ce stade.
- Aucun service distant, credential, socket ou log hôte copié dans le workspace d'essai.
- Deadline monotone propagée, avec réserve pour la restauration et la finalisation.

## Suite envisagée

- [DONE] Première nano-étape avec reçu, rejet d'invariant et refus du reçu : restauration mesurée sur disque, bridge/Git simulés.
- [DONE] Sonde structurée du modèle local : critère conforme, fenêtre 16 384 lue via ollama show puis fournie avec provenance asserted.
- [DONE] Essai local initial conservé : candidat conforme, refus tautology, restauration exacte, aucun reçu.
- [DONE] Étendre le contrat à la projection exacte [0, 1] ; rejouer le candidat archivé sous ce nouveau critère.
- [DONE] Nouvel essai Ollama trial-25ugxn94 : unit_projection, reçu durable, effet confirmé et fichier conservé (15:09).
- [TODO] Projection par bandes bass/mid/treble, après définition d'un domaine de tableaux et de relations adaptées.
- [TODO] Lissage temporel, après définition de son critère multi-entrée compatible avec le catalogue.
- [TODO] Magnitudes depuis un signal synthétique, sans capture audio.

Les essais ultérieurs ne justifient ni une stratégie Hypothesis libre émise par le modèle,
ni un élargissement silencieux du catalogue.
