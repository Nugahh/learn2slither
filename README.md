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
(`pygame`, `tqdm`, `pytest`, `flake8`).

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
| `-reward-shaping` | Entraînement : bonus/malus basé sur la distance à la pomme verte la plus proche (voir *Modèles fournis*) | désactivé |

### Exemples

Entraîner un modèle sur 100 sessions, sans affichage (rapide) :
```bash
.venv/bin/python3 ./snake -sessions 100 -visual off -save models/mon_modele.json
```
En mode `-visual off`, une barre de progression (`tqdm`) s'affiche pendant
l'entraînement, suivie d'un résumé (longueur moyenne/max, durée moyenne,
% de sessions plafonnées) une fois terminé.

Entraîner le modèle flagship (40 000 sessions, avec reward shaping) :
```bash
.venv/bin/python3 ./snake -sessions 40000 -visual off -reward-shaping -save models/40000sess.json
```

Regarder jouer un modèle déjà entraîné, en continu, sans apprentissage :
```bash
.venv/bin/python3 ./snake -visual on -load models/40000sess.json -sessions 5 -dontlearn -speed 8
```

Évaluer un modèle sur de nombreuses sessions et voir les paliers de
longueur atteints :
```bash
make benchmark                                    # 1000 sessions, modèle flagship
make benchmark MODEL=models/x.json SESSIONS=300    # autre modèle / échantillon
```

Raccourcis Makefile : `make train` (entraîne le modèle flagship), `make
play` (ouvre le lobby graphique), `make benchmark` (statistiques sur N
sessions).

### Lobby graphique (bonus)

```bash
./snake            # sans aucun argument
./snake -lobby      # ou explicitement, même combiné à d'autres usages
make play           # raccourci équivalent
```

Panneau de configuration graphique en deux écrans : Accueil (vitesse,
taille du plateau, bouton PLAY) et Paramètres (nombre de sessions,
pas-à-pas). Le lobby ne fait que **jouer** un modèle déjà entraîné —
aucun apprentissage, aucune sauvegarde depuis cet écran ; l'entraînement
se fait via la ligne de commande (`make train` ou `./snake -sessions
...`). Le modèle chargé par défaut est `models/40000sess.json` (le plus
performant) ; son chemin est affiché à l'écran.

À la fin de chaque partie, un écran affiche la longueur atteinte et la
durée : Espace/Entrée pour rejouer, Échap pour revenir à l'accueil. Une
fois toutes les sessions jouées, un écran de résultats affiche longueur
moyenne/max, durée moyenne, % de sessions plafonnées et un graphique de
progression, avec les boutons Rejouer / Menu / Quitter.

N'importe quel autre appel (avec au moins un flag existant) utilise le
flux CLI classique ci-dessus, inchangé.

## Modèles fournis

Le dossier `models/` contient le modèle flagship, `40000sess.json` (40 000
sessions, ~6 100 états appris), utilisé par défaut par le lobby et par
`make benchmark`. Il se reproduit avec `make train` (voir *Exemples*).

Sur 1000 parties en mode exploitation (`-dontlearn`, via `make
benchmark` — échantillon large pour une estimation stable, un lot de 100
parties fait varier chaque pourcentage de quelques points d'un tirage à
l'autre) : longueur moyenne 28.4, ≥ 15 dans 93% des parties, ≥ 20 dans
82%, ≥ 25 dans 65%, ≥ 30 dans 43%, **≥ 35 dans 25%** (record observé :
64), et 0.6% de parties bloquées par le plafond de sécurité.

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

70 tests couvrant chaque module indépendamment (règles du plateau, vision,
apprentissage, affichage, CLI, lobby, statistiques).

## Bonus implémentés

- **Longueur élevée en fin de session** : voir les statistiques ci-dessus
  (`models/40000sess.json`, jusqu'à 35+ de façon reproductible).
- **Affichage soigné** : lobby graphique avec panneau de configuration et
  écran de résultats/statistiques (voir ci-dessus).
- **Taille de plateau variable** : `-board-size N` (min. 3), un modèle
  entraîné en 10x10 rejoue sans problème sur une autre taille — validé
  manuellement (3, 5, 10, 20 ; longueur 43 atteinte en 20x20) et par un
  test automatisé
  (`tests/test_main.py::test_model_trained_on_default_board_plays_on_different_size`).

## Structure du projet

```
srcs/
├── config.py        # constantes : taille du plateau, récompenses, hyperparamètres
├── environment.py    # Board : grille, serpent, pommes, règles de collision
├── interpreter.py    # plateau → vision terminale + état compact pour la Q-table
├── agent.py           # Q-learning : choix d'action, apprentissage, sauvegarde/chargement
├── display.py         # affichage graphique du jeu (Pygame)
├── stats.py            # statistiques agrégées sur un lot de sessions
├── lobby.py            # lobby graphique : config + résultats (bonus)
└── main.py             # ligne de commande + routage lobby + boucle de sessions

tests/        # tests unitaires et d'intégration, un fichier par module
scripts/      # scripts autonomes (benchmark.py : évaluation par paliers)
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
