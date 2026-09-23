# Learn2Slither

Un serpent qui apprend à jouer par renforcement (Q-learning), pour le sujet
42 *Learn2Slither*. L'agent ne voit que 4 lignes de vision depuis sa tête
(haut/bas/gauche/droite) et doit apprendre, par essai-erreur, à manger des
pommes vertes, éviter les pommes rouges et ne pas mourir.

## Installation

```bash
make install
```

Crée un environnement virtuel Python (`.venv/`) et installe les dépendances
(`pygame`, `pytest`, `flake8`).

## Utilisation

```bash
./snake [options]
```

(ou `.venv/bin/python3 ./snake [options]` si le venv n'est pas activé)

| Option | Description | Défaut |
|---|---|---|
| `-sessions N` | Nombre de sessions à jouer/entraîner | `1` |
| `-save PATH` | Sauvegarde le modèle (Q-table) à la fin | — |
| `-load PATH` | Charge un modèle existant au démarrage | — |
| `-visual {on,off}` | Affichage graphique Pygame + vision/action en terminal | `on` |
| `-dontlearn` | Mode exploitation : pas d'apprentissage, le modèle chargé n'est pas modifié | désactivé |
| `-step-by-step` | Avance case par case (ESPACE / flèche droite / Entrée) | désactivé |
| `-speed N` | Vitesse d'affichage (déplacements/seconde) hors mode pas-à-pas | `10` |
| `-board-size N` | Taille du plateau (min. 3) — un modèle entraîné en 10x10 rejoue tel quel sur une autre taille | `10` |

### Exemples

Entraîner un modèle sur 100 sessions, sans affichage (rapide) :
```bash
.venv/bin/python3 ./snake -sessions 100 -visual off -save models/100sess.json
```

Regarder jouer un modèle déjà entraîné, en continu, sans apprentissage :
```bash
.venv/bin/python3 ./snake -visual on -load models/40000sess.json -sessions 5 -dontlearn -speed 8
```

Évaluer rapidement un modèle sur plusieurs sessions, sans fenêtre :
```bash
.venv/bin/python3 ./snake -visual off -load models/40000sess.json -sessions 20 -dontlearn
```

Raccourcis Makefile : `make train` (entraînement d'exemple), `make play`
(ouvre le lobby graphique).

### Lobby graphique (bonus)

```bash
./snake            # sans aucun argument
./snake -lobby      # ou explicitement, même combiné à d'autres usages
make play           # raccourci équivalent
```

Ouvre un panneau de configuration graphique (sessions, taille du plateau,
vitesse — chiffre entre les boutons `-`/`+` —, apprentissage on/off,
pas-à-pas, chemin de sauvegarde). Le modèle chargé par défaut est
`models/40000sess.json` (le plus performant) ; son chemin est affiché à
l'écran. À la fin des sessions, un écran de résultats affiche longueur
moyenne/max, durée moyenne, % de sessions plafonnées, et un graphique de
progression, avec les boutons Rejouer / Menu / Quitter.

N'importe quel autre appel (avec au moins un flag existant) utilise le
flux CLI classique ci-dessus, inchangé.

## Modèles fournis

Le dossier `models/` contient des modèles entraînés à différents stades pour
montrer la progression de l'apprentissage :

| Fichier | Sessions | États appris |
|---|---:|---:|
| `1sess.json` | 1 | ~5 |
| `10sess.json` | 10 | ~15 |
| `100sess.json` | 100 | ~150 |
| `1000sess.json` | 1 000 | ~1 100 |
| `5000sess.json` | 5 000 | ~3 800 |
| `20000sess.json` | 20 000 | ~5 640 |
| `40000sess.json` | 40 000 | ~6 045 |

Le modèle à 40 000 sessions (retenu comme modèle par défaut du lobby)
atteint, sur 300 parties en mode exploitation (`-dontlearn` — échantillon
large pour une estimation stable, les lots de 100 parties font varier
chaque pourcentage de quelques points d'un tirage à l'autre) : longueur
≥ 15 dans 90% des parties, ≥ 20 dans 70%, ≥ 25 dans 50%, ≥ 30 dans 30%,
**≥ 35 dans 20%** (record observé : 53), et 2% de parties bloquées par le
plafond de sécurité.

Il a été obtenu en comparant 3 approches en parallèle (30 graines
aléatoires sur l'algorithme standard, un taux d'apprentissage décroissant,
et un *reward shaping* basé sur la distance à la pomme verte la plus
proche) — le reward shaping a donné le meilleur gain, net et cohérent sur
la quasi-totalité des graines testées, pas juste un coup de chance isolé.

⚠️ **Nuance de conformité** : le reward shaping calcule un bonus/malus à
partir de la position réelle de la pomme sur le plateau, même quand elle
n'est pas dans le champ de vision à 4 directions du serpent. L'**état**
donné à l'agent pour décider reste strictement limité à sa vision (aucun
changement là-dessus) — seule la **récompense** d'entraînement utilise
cette info supplémentaire, ce qui est une technique standard (*reward
shaping*) distincte de l'observation de l'agent. Mais c'est une
interprétation du texte du sujet, pas une certitude absolue.

Au-delà de 40 000 sessions (testé jusqu'à 100 000, algorithme standard),
la couverture d'états progresse très peu (rendement décroissant) et les
performances stagnent sans amélioration claire — c'est ce qui a motivé la
recherche multi-graines et le reward shaping plutôt que "juste entraîner
plus longtemps".

## Tests

```bash
make test    # suite de tests (pytest)
make norm    # vérification de la norme (flake8)
```

59 tests couvrant chaque module indépendamment (règles du plateau, vision,
apprentissage, affichage, CLI, lobby).

## Bonus implémentés

- **Longueur élevée en fin de session** : voir le tableau ci-dessus
  (`models/40000sess.json`, jusqu'à 35+ de façon reproductible).
- **Affichage soigné** : lobby graphique avec panneau de configuration et
  écran de résultats/statistiques (voir ci-dessus).
- **Taille de plateau variable** : `-board-size N` (min. 3), un modèle
  entraîné en 10x10 rejoue sans problème sur une autre taille — validé
  manuellement (3, 5, 10, 20 ; longueur 43 atteinte en 20x20) et par un
  test automatisé
  (`tests/test_main.py::test_model_trained_on_default_board_plays_on_different_size`).

Détails et preuves complètes dans
`docs/superpowers/specs/2026-09-22-bonus-features-design.md`.

## Structure du projet

```
srcs/
├── config.py        # constantes : taille du plateau, récompenses, hyperparamètres
├── environment.py    # Board : grille, serpent, pommes, règles de collision
├── interpreter.py    # plateau → vision terminale + état compact pour la Q-table
├── agent.py           # Q-learning : choix d'action, apprentissage, sauvegarde/chargement
├── display.py         # affichage graphique du jeu (Pygame)
├── lobby.py            # lobby graphique : config + résultats (bonus)
└── main.py             # ligne de commande + routage lobby + boucle de sessions

tests/        # tests unitaires et d'intégration, un fichier par module
models/       # modèles Q-table entraînés (JSON)
snake         # point d'entrée exécutable
```

## Choix de conception

- **Vision** : à chaque tour, le serpent scanne les 4 directions depuis sa
  tête jusqu'au premier objet rencontré (mur, corps, pomme verte ou rouge) ;
  la distance est regroupée en 3 paliers (1, 2, 3+). La dernière action
  jouée est aussi mémorisée (mémoire propre de l'agent, pas une info du
  plateau) pour éviter les oscillations. L'agent ne reçoit jamais
  d'information hors de son champ de vision.
- **Modèle** : Q-table (dictionnaire état → valeurs par action), pas de
  réseau de neurones.
- **Récompenses** : pomme verte `+10`, pomme rouge `-10`, déplacement `-1`,
  game over `-50`.
- **Sécurité** : un plafond de pas par session (`MAX_STEPS_PER_SESSION`)
  évite qu'une politique gloutonne reste bloquée indéfiniment ; les erreurs
  d'entrée (`-load` invalide, `-board-size` trop petit, `-save` vers un
  dossier inexistant) sont signalées proprement plutôt que de faire planter
  le programme.

Détails complets du design et de l'implémentation dans
`docs/superpowers/specs/` et `docs/superpowers/plans/`.
