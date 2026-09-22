# Learn2Slither — Design

## Contexte

Projet 42 de reinforcement learning : un serpent contrôlé par un agent Q-learning
apprend, par essai-erreur, à survivre et grandir sur un plateau 10x10. Le sujet
(`learn2slither.pdf`) impose : board 10x10, 2 pommes vertes + 1 pomme rouge,
vision du serpent limitée aux 4 directions depuis la tête, Q-function (Q-table
ou réseau de neurones — aucun autre modèle autorisé), export/import de modèles,
mode "exploitation sans apprentissage", et un affichage graphique + un
affichage terminal de la vision/action à chaque tour.

Objectif final : un serpent atteignant une longueur ≥ 10 et une durée de vie
importante, avec au moins 3 modèles sauvegardés entraînés respectivement sur
1, 10 et 100 sessions (le sujet suggère aussi un modèle bien plus entraîné,
ex. 1000 sessions).

Langage : Python, avec conformité à la norme flake8 (`pip install flake8`,
`alias norminette_python=flake8`).

## Architecture

Trois modules séparés, correspondant au schéma Environment / Interpreter /
Agent du sujet, plus une couche d'orchestration CLI et un module d'affichage :

```
CLI (main.py)
   │
   ├─► Environment (environment.py)  — plateau 10x10, règles, collisions, pommes
   │
   ├─► Interpreter (interpreter.py)  — plateau brut → vision texte + état compact
   │
   ├─► Agent (agent.py)              — Q-table, epsilon-greedy, apprentissage, save/load
   │
   └─► Display (display.py)         — rendu Pygame (désactivable via -visual off)
```

Chaque module est testable isolément : l'Environment ne connaît rien de
l'agent, l'Agent ne connaît rien du plateau — il ne reçoit que l'état que lui
fournit l'Interpreter. Cette séparation répond à l'exigence explicite du sujet
("Please ensure that your program is modular ... to easily evaluate each
part").

**Alternative écartée** : fusionner Environment/Interpreter/Agent dans une
seule classe `Game`. Plus rapide à écrire mais viole l'exigence de modularité
et complique les tests unitaires par partie — écarté.

## Règles du plateau (Environment)

- Board 10x10.
- 2 pommes vertes + 1 pomme rouge, placées aléatoirement (cases libres).
- Serpent de longueur initiale 3, placé aléatoirement et de façon contiguë.
- Collision mur → game over.
- Collision avec sa propre queue → game over.
- Pomme verte mangée → longueur +1, nouvelle pomme verte apparaît.
- Pomme rouge mangée → longueur -1, nouvelle pomme rouge apparaît.
- Longueur tombant à 0 → game over.

## État et action

- **Action** : UP / DOWN / LEFT / RIGHT (absolu), 4 choix possibles.
- **Vision terminal complète** (affichée à chaque tour, format du sujet
  `W000000000HW` par direction avec lettres W/H/S/G/R/0) : calculée par
  l'Interpreter uniquement pour l'affichage humain (terminal), séparément de
  l'état interne de l'agent.
- **État compact fourni à la Q-table** : pour chacune des 4 directions, on
  scanne depuis la tête jusqu'au premier objet non-vide rencontré, parmi
  `{WALL, BODY, GREEN, RED}`, et la distance à cet objet est regroupée en
  3 paliers (1, 2, 3+). Chaque direction est encodée comme une chaîne
  `symbole + palier` (ex. `"G1"` = pomme verte adjacente, `"G3"` = pomme
  verte à 3 cases ou plus). L'état est un tuple de 4 chaînes.
  Espace d'états = (4×3)⁴ = 20736 combinaisons possibles au maximum, mais
  seul un petit sous-ensemble est réellement visité en pratique (ex. ~125
  états après 1000 sessions d'entraînement sur un plateau 10x10).
  *Révision post-implémentation* : la première version n'encodait pas la
  distance (4⁴ = 256 états), ce qui empêchait l'agent de distinguer une
  pomme proche d'une pomme lointaine dans la même direction et entraînait
  des oscillations stériles en mode glouton. Le palier de distance reste
  strictement dérivé de la vision du serpent (aucune information hors
  champ n'est ajoutée).
- Aucune information non visible par le serpent n'est fournie à l'agent
  (contrainte du sujet, pénalité -42 sinon).

## Récompenses

Constantes ajustables dans `config.py` :

| Événement                                   | Récompense |
|----------------------------------------------|-----------:|
| Pomme verte mangée                            |       +10  |
| Pomme rouge mangée                            |       -10  |
| Déplacement sans manger                       |        -1  |
| Game over (mur / soi-même / longueur 0)       |       -50  |

## Q-learning

- Modèle : Q-table (`dict[state_tuple][action] -> float`), valeur par défaut
  0.0 pour tout état/action inconnu.
- Mise à jour standard :
  `Q(s,a) ← Q(s,a) + α · [r + γ · max_a' Q(s',a') − Q(s,a)]`
- Hyperparamètres par défaut : α (learning rate) = 0.1, γ (discount) = 0.9.
- Exploration : epsilon-greedy avec décroissance exponentielle, ε passant de
  1.0 à 0.01 au fil des sessions d'entraînement.
- Mode exploitation sans apprentissage (`-dontlearn`) : l'agent choisit
  toujours l'action de plus haute Q-valeur (pas d'exploration, pas de mise à
  jour de la Q-table), pour évaluer un modèle sans l'altérer.
- Sauvegarde/chargement : fichier **JSON** contenant la Q-table sérialisée et
  des métadonnées (nombre de sessions d'entraînement, hyperparamètres
  utilisés). Choisi pour la lisibilité/débogage et l'absence de dépendance
  supplémentaire (vs pickle, binaire et spécifique à Python).

## CLI

Flags alignés sur les exemples du sujet :

```
./snake -sessions 10 -save models/10sess.json -visual off
./snake -visual on -load models/100sess.json -sessions 10 -dontlearn -step-by-step
./snake -visual on -load models/1000sess.json
```

- `-sessions N` : nombre de sessions d'entraînement/jeu (défaut 1).
- `-save PATH` : chemin de sauvegarde du modèle en fin d'exécution.
- `-load PATH` : chemin de chargement d'un modèle existant.
- `-visual {on,off}` : active/désactive l'affichage Pygame (défaut on).
- `-dontlearn` : désactive l'apprentissage (mode exploitation).
- `-step-by-step` : mode pas-à-pas.
- `-speed N` : vitesse d'affichage (au moins une vitesse "humainement
  lisible" doit exister, exigence du sujet).
- `-board-size N` (bonus) : taille du plateau paramétrable. L'état compact
  choisi ne dépend pas de la taille du plateau (on scanne juste jusqu'au
  premier objet), donc un modèle entraîné en 10x10 est directement rejouable
  sur une autre taille — ce choix de conception valide ce bonus sans coût
  supplémentaire.

## Structure de projet

```
learn2slither/
├── Makefile
├── requirements.txt
├── .flake8
├── snake                # point d'entrée exécutable (wrapper vers srcs/main.py)
├── srcs/
│   ├── main.py           # parsing CLI + boucle d'entraînement/jeu (orchestrateur)
│   ├── environment.py    # Board : grille, serpent, pommes, règles
│   ├── interpreter.py    # plateau brut -> vision texte + état compact
│   ├── agent.py           # QLearningAgent : choix d'action, apprentissage, save/load
│   ├── display.py         # rendu Pygame
│   └── config.py          # constantes : board size, rewards, hyperparams
├── models/                # 1sess.json, 10sess.json, 100sess.json, 1000sess.json...
└── tests/
    ├── test_environment.py
    ├── test_interpreter.py
    └── test_agent.py
```

## Environnement de dev (venv + Makefile)

- `requirements.txt` : `pygame`, `pytest`, `flake8`.
- Cibles Makefile :
  - `venv` : crée `.venv`
  - `install` : installe les dépendances dans le venv
  - `train` : lance un entraînement d'exemple
  - `play` : lance une session en mode exploitation (`-dontlearn -load ...`)
  - `test` : lance `pytest`
  - `norm` : lance `flake8` (alias `norminette_python`)
  - `clean` : supprime `.venv`, caches Python, etc.

## Tests

- **Environment** : collisions mur/soi-même, apparition/consommation des
  pommes vertes et rouges, variation de longueur, game over à longueur 0.
- **Interpreter** : encodage correct de la vision compacte (4 directions)
  et de la vision texte complète sur des plateaux de test connus.
- **Agent** : formule de mise à jour Q, comportement epsilon-greedy vs
  greedy (`-dontlearn`), round-trip sauvegarde/chargement JSON.
- Script d'évaluation manuel (via `-dontlearn -load`) pour mesurer longueur
  moyenne / durée moyenne / taux de succès sur N sessions, sans passer par
  des tests automatisés.

## Livrables

- Code source modulaire tel que décrit ci-dessus, conforme flake8.
- Dossier `models/` avec au moins les modèles entraînés à 1, 10 et 100
  sessions (exigence explicite du sujet), plus un modèle plus long
  (ex. 1000 sessions) pour viser l'objectif longueur ≥ 10.
- Ce document de design, commité dans `docs/superpowers/specs/`.

## Hors scope (pistes bonus, non traitées dans ce plan initial)

- Longueur cible plus élevée (15/20/25/30/35).
- Interface graphique enrichie (lobby, panneau de config, statistiques).
- Entraînement de plusieurs modèles avec des stratégies de mise à jour Q
  alternatives (mentionné par le sujet comme possible, pas requis).
