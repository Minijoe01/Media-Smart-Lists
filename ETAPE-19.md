# Media Smart Lists — Étape 19 : libellés MDBList, posters groupés et textes publics

## Libellés conformes aux types MDBList

La documentation officielle distingue notamment :

- **Watchlist** : conteneur natif du compte ;
- **liste statique** : liste organisée manuellement, dont l'utilisateur ajoute, retire et réordonne les éléments ;
- **liste dynamique** : liste construite depuis des filtres de recherche et actualisée automatiquement ;
- **liste IA** ;
- **liste flux**.

Les libellés deviennent donc :

```text
Watchlist MDBList
Liste statique : Séries
Liste dynamique : Nouveautés
Liste IA : Choix IA
Liste flux : Découvertes
```

Cette convention est utilisée dans **Que regarder ?**, **Nettoyage des listes**, les rapports et la colonne `Présent dans`.

La colonne sépare les conteneurs avec `|` pour supprimer l'ambiguïté :

```text
Watchlist MDBList | Liste statique : Séries
```

Les listes IA et flux sont conservées dans les vues regroupant toutes les listes personnelles, sans être classées à tort comme statiques.

## Posters de Progression Fantôme

La recherche locale reste prioritaire et gratuite. Si des posters sont encore absents mais que les identifiants TMDb sont disponibles, un bouton apparaît :

```text
Compléter X poster(s) · 1 appel groupé
```

MDBList permet de demander jusqu'à 200 médias dans une seule requête batch. Les posters récupérés sont mis en cache pour la session : aucun appel par contenu.

Cette action reste facultative et n'est jamais lancée automatiquement.

## Messages destinés au public

Les messages techniques ont été reformulés :

- `0 appel API supplémentaire` devient `quota MDBList préservé` ;
- `dry-run` devient `aperçu uniquement` ;
- les noms d'endpoints disparaissent des explications courantes ;
- le nombre d'appels reste visible uniquement lorsqu'il aide réellement l'utilisateur à protéger son quota.

Les informations de quota ne sont donc pas supprimées, mais présentées comme une fonctionnalité du produit plutôt qu'une note du développeur.

## Lecture active

Aucun nouvel essai automatique n'est ajouté dans cette étape. Le problème de lecture active est probablement situé dans la chaîne de scrobbling MDBList et sera réexaminé séparément.

## Sécurité et quota

- posters : zéro appel si le cache local suffit ;
- enrichissement facultatif : un appel groupé pour 200 identifiants maximum ;
- aucune requête par contenu ;
- aucune écriture ou suppression ;
- cache supprimé lors de la déconnexion.

## Installation

Envoyer uniquement ces cinq fichiers à la racine du dépôt :

- `app.py`
- `mdblist_provider.py`
- `normalized_model.py`
- `list_audit_engine.py`
- `ETAPE-19.md`

Commit conseillé :

```text
feat: clarify mdblist list types and add grouped poster enrichment
```

Aucun secret à modifier. Aucun rechargement complet n'est nécessaire pour tester les nouveaux libellés et les posters groupés.
