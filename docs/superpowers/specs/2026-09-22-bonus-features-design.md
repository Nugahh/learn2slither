# Bonus Features — Design

## Contexte

Le sujet Learn2Slither liste 3 bonus possibles (Chapitre VI), à ne
considérer que si la partie obligatoire est correcte (déjà le cas : 34
tests passent, flake8 propre) :

1. Atteindre une longueur plus élevée en fin de session (15, 20, 25, 30, 35).
2. Un affichage visuellement soigné : lobby, panneau de configuration,
   résultats et statistiques.
3. Permettre de changer la taille du plateau en argument, un modèle
   entraîné devant pouvoir rejouer sur une autre taille sans problème.

Ce document couvre l'état des 3 bonus et le design du bonus 2 (le seul qui
nécessite une vraie conception, les deux autres étant déjà acquis).

## Bonus 3 — Taille de plateau variable (déjà acquis)

`-board-size N` existe déjà depuis la partie obligatoire (Task 5 du plan
initial). L'encodage d'état (objet le plus proche + palier de distance +
dernière action, tous relatifs à la tête du serpent) ne dépend jamais de la
taille absolue du plateau, donc un modèle entraîné en 10x10 se comporte
normalement sur une autre taille.

Vérifié empiriquement (`models/20000sess.json`) : tailles 3, 5, 10, 20 —
aucun crash, aucun blocage. Sur plateau 20x20, longueur maximale observée :
43. Un test automatisé (`tests/test_main.py`) sera ajouté pour formaliser
cette validation (charger un modèle, jouer sur une taille différente,
vérifier l'absence de crash).

## Bonus 1 — Longueur ≥ 15/20/25/30/35 (déjà acquis)

Un modèle `models/20000sess.json` a été entraîné spécifiquement pour ce
bonus (hyperparamètres inchangés — une tentative d'epsilon-decay plus lent
n'a pas montré d'amélioration nette sur un seul essai, pas assez de signal
pour justifier un changement). Résultat sur 100 sessions en mode
exploitation (`-dontlearn`) :

| Palier | Taux de réussite |
|---|---:|
| ≥ 15 | 90 % |
| ≥ 20 | 80 % |
| ≥ 25 | 55 % |
| ≥ 30 | 38 % |
| ≥ 35 | 15 % (record observé : 43) |

0 % de sessions bloquées par le plafond de sécurité (`MAX_STEPS_PER_SESSION`).

## Bonus 2 — Lobby, panneau de configuration, statistiques

### Contrainte principale

La partie obligatoire (CLI avec les flags exacts du sujet : `-sessions`,
`-save`, `-load`, `-visual`, `-dontlearn`, `-step-by-step`, `-speed`,
`-board-size`) **ne doit pas changer de comportement**. Le lobby est un
chemin d'entrée *additionnel*, jamais un remplacement.

### Déclenchement

- `./snake` sans aucun argument → ouvre le lobby.
- `./snake -lobby` → ouvre le lobby explicitement (nouveau flag,
  utilisable même avec d'autres flags ignorés dans ce cas).
- Tout autre appel avec au moins un flag existant → comportement CLI
  actuel, inchangé, exactement comme documenté dans le sujet.

### Architecture

Nouveau module `srcs/lobby.py`, responsable uniquement de l'affichage des
écrans de configuration et de résultats (widgets Pygame maison : pas de
dépendance externe). Aucune logique de jeu n'y est dupliquée :

```
main.py
   │
   ├─► (arguments CLI fournis) → flux actuel inchangé
   │
   └─► (aucun argument, ou -lobby) → lobby.run_lobby()
          │
          ├─ Écran configuration → renvoie un objet "Settings"
          │  avec les mêmes attributs que le Namespace d'argparse
          │  (sessions, save, load, visual, dontlearn, step_by_step,
          │  speed, board_size)
          │
          ├─ main.py exécute la boucle de sessions EXACTEMENT comme
          │  pour le flux CLI (réutilise run_session, Board, Display,
          │  QLearningAgent, agent.save/load) — aucune logique dupliquée
          │  — et collecte (max_length, steps, done) par session
          │
          └─ Écran résultats → lobby.show_results(stats) affiche le
             bilan, puis propose Rejouer / Menu / Quitter
```

### Écran 1 — Configuration

Widgets maison (pas de bibliothèque GUI externe) :

- **Stepper** (boutons `-`/`+`) pour : nombre de sessions, taille du
  plateau (min 3), vitesse d'affichage.
- **Toggle** (clic pour basculer) pour : apprentissage activé/désactivé
  (`-dontlearn`), mode pas-à-pas.
- **Sélecteur de modèle** : liste cliquable des fichiers `models/*.json`
  détectés automatiquement (remplit le champ "charger"), plus un champ
  texte éditable pour saisir un chemin manuellement.
- **Champ de sauvegarde** : champ texte éditable, pré-rempli avec un nom
  par défaut (`models/lobby_<timestamp>.json`), désactivable (case à
  cocher "ne pas sauvegarder").
- Bouton **JOUER**.

`-visual` n'est pas proposé comme option dans le lobby : puisqu'on est déjà
dans une interface graphique, le jeu se joue nécessairement avec
l'affichage activé (le mode sans affichage reste accessible via le flux
CLI classique).

### Écran 2 — Jeu

Inchangé : réutilise `Display` et `run_session` tels quels.

### Écran 3 — Résultats

Affiché une fois les N sessions terminées :

- Nombre de sessions jouées, longueur moyenne, longueur max, durée
  moyenne, pourcentage de sessions bloquées par le plafond de sécurité.
- Petit graphique en barres (longueur atteinte par session, dans l'ordre)
  pour visualiser la progression sur la série.
- Boutons : **Rejouer** (mêmes réglages), **Menu** (retour à l'écran de
  configuration), **Quitter**.

### Style visuel

Thème sombre cohérent avec `srcs/display.py` (mêmes teintes de fond),
boutons avec effet visuel au survol de la souris, typographie lisible.
Entièrement en primitives Pygame (`pygame.draw`, `pygame.font`) — pas de
nouvelle dépendance.

### Tests

- Tests unitaires sur les widgets (Stepper : incrémente/décrémente et
  respecte les bornes min/max ; Toggle : bascule son état).
- Test que `main.py` route bien vers le lobby quand `sys.argv` est vide ou
  contient `-lobby`, et vers le flux CLI classique sinon (sans lancer de
  vraie fenêtre — on vérifie juste l'aiguillage, en substituant une
  fonction `run_lobby` factice).
- Test que l'objet `Settings` renvoyé par l'écran de configuration a bien
  tous les attributs attendus par `main()`.
- Pas de test end-to-end pilotant réellement la souris/clavier Pygame
  (hors de portée raisonnable) — cohérent avec l'approche déjà retenue
  pour `srcs/display.py` (tests de fumée uniquement).

## Hors scope

- Pas de sélecteur de fichier natif de l'OS (juste une liste des modèles
  détectés + un champ texte).
- Pas de stats "en direct" pendant la partie (l'utilisateur a choisi le
  bilan de fin de session uniquement).
- Pas de personnalisation graphique poussée (thèmes, animations) au-delà
  d'un style sombre cohérent et de boutons avec effet de survol.
