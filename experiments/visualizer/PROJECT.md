# Noyau audio — banc d'essai Pithos Reloaded

Mise à jour : **13:09**.

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

Le premier critère exécutable est **idempotent / clamp_level / floats_finite** :
normaliser deux fois donne le même résultat qu'une fois. Les entrées sont générées par Hypothesis,
le critère est fixé par le banc et aucune valeur attendue n'est demandée au modèle.

**Portée de la preuve** : ce critère teste la stabilité de la projection. À lui seul, il ne démontre
pas que les bornes choisies sont exactement 0 et 1. Un vert de ce banc n'est donc pas la validation
complète du contrat produit, ni celle d'un visualiseur audio fonctionnel.

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
- [TODO] Essai avec modèle local ; mesurer rejet du schéma, durée, verdict et reçu.
- [TODO] Projection par bandes bass/mid/treble, après définition d'un domaine de tableaux et de relations adaptées.
- [TODO] Lissage temporel, après définition de son critère multi-entrée compatible avec le catalogue.
- [TODO] Magnitudes depuis un signal synthétique, sans capture audio.

Les essais ultérieurs ne justifient ni une stratégie Hypothesis libre émise par le modèle,
ni un élargissement silencieux du catalogue.
