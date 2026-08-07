# Media Smart Lists — Étape 16 : audit de listes inspiré de Kometa

## Pourquoi Kometa est intéressant

Kometa, anciennement Plex Meta Manager, automatise principalement des bibliothèques Plex à partir de fichiers YAML. Son modèle est particulièrement utile :

```text
Builder / Source → Filters → Settings → Preview / Sync
```

Media Smart Lists reste fournisseur-neutre et ne devient pas dépendant de Plex ou de Kometa. Cette étape reprend seulement les bonnes idées : règles déclaratives, aperçu avant action, rapports et distinction entre synchronisation et ajout.

## Nettoyage des listes restauré

La page **Nettoyage des listes** devient un véritable audit local :

- choix indépendant de la Watchlist, de chaque liste statique et de chaque liste dynamique ;
- filtre Films / Séries ;
- recherche locale ;
- combinaison des règles en mode `Au moins un` ou `Tous les signaux` ;
- tris par priorité, ancienneté, note, nombre de conteneurs et titre.

Signaux disponibles :

- contenu déjà vu mais encore présent dans une liste ;
- contenu présent dans plusieurs conteneurs ;
- ajout datant de plus de 6 mois, 1 an ou 2 ans ;
- note communauté inférieure à 5/10.

Les listes dynamiques sont clairement signalées comme informatives : leur contenu est régénéré par MDBList et ne doit pas être traité comme une liste statique.

## Recherche de doublons restaurée

La page **Recherche de doublons** compare localement :

- la Watchlist native ;
- chaque liste statique ;
- chaque liste dynamique.

Les vues agrégées créées par Media Smart Lists sont volontairement exclues afin de ne pas fabriquer de faux doublons.

La correspondance utilise, dans cet ordre, les identifiants TMDb, IMDb, TVDb, Trakt et MDBList, puis un secours titre + année.

Trois classifications sont distinguées :

- doublon entre conteneurs modifiables ;
- chevauchement avec une liste dynamique ;
- chevauchement informatif.

## Rapports

Les deux pages permettent de télécharger :

- un rapport CSV lisible dans Excel ;
- un rapport JSON versionné et fournisseur-neutre.

Les rapports ne contiennent aucun token, cookie ou secret.

## Sécurité

Cette étape est un **dry-run permanent** :

- aucune suppression ;
- aucune écriture MDBList ;
- aucune action sur une liste dynamique ;
- aucune requête API supplémentaire ;
- confirmation impossible puisqu'aucun bouton destructif n'existe encore.

L'écriture pourra être ajoutée plus tard uniquement pour la Watchlist et les listes statiques, avec aperçu conservé et confirmation explicite.

## Installation

Envoyer uniquement ces trois fichiers à la racine du dépôt :

- `app.py`
- `list_audit_engine.py`
- `ETAPE-16.md`

Commit conseillé :

```text
feat: add kometa-inspired local list audit and duplicate reports
```

Aucun secret à modifier et aucun rechargement obligatoire du dataset.
