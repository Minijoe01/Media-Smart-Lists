# Media Smart Lists — Étape 14 : filtres et tris « En cours »

## Résultat

La page **En cours de lecture** conserve les cartes et la barre de progression legacy, avec maintenant :

- recherche locale par titre ;
- filtre local par genre ;
- nombre de cartes à afficher : 30, 60, 100 ou toutes ;
- compteur des résultats filtrés.

## Tris disponibles

- dernier visionnage récent → ancien (**tri par défaut**, identique à MDBList Up Next) ;
- dernier visionnage ancien → récent ;
- progression élevée → faible ;
- progression faible → élevée ;
- temps restant court → long ;
- temps restant long → court ;
- temps déjà vu élevé → faible ;
- temps déjà vu faible → élevé ;
- nouveauté : épisode disponible récent → ancien ;
- nouveauté : épisode disponible ancien → récent ;
- titre A → Z et Z → A.

## Aucun appel API supplémentaire

Les filtres et les tris sont exécutés uniquement dans `progress_engine.py` sur le dataset déjà présent dans la session Streamlit.

Les genres viennent de `/sync/watched`, déjà chargé à l'étape précédente, puis sont rapprochés localement des séries `/upnext` grâce aux identifiants MDBList/TMDb/TVDb/IMDb/Trakt. Aucun appel par série et aucun appel lors d'un changement de filtre ou de tri.

Pour le tri **Nouveauté**, Media Smart Lists utilise en priorité la vraie date `last_air_date` lorsqu'elle est présente dans les données déjà chargées. Sinon, il utilise la date de sortie de l'épisode suivant à voir fournie par `/upnext`. Cette solution reste volontairement sans nouvelle requête.

## Affichage enrichi

Chaque carte peut maintenant montrer, si les données sont disponibles :

- les genres ;
- la date du dernier visionnage ;
- la date du dernier épisode disponible ou de l'épisode suivant à voir.

## Sécurité/documentation

`.streamlit/secrets.example.toml` est corrigé :

- suppression de `MDBLIST_CLIENT_SECRET`, inutile pour le Device Code ;
- ajout de `TOKEN_ENCRYPTION_KEY` vide ;
- aucune vraie valeur secrète dans le dépôt.

Ne jamais remplacer la vraie `TOKEN_ENCRYPTION_KEY` déjà enregistrée dans Streamlit.

## Installation

Envoyer le contenu de ce paquet dans la branche `main` en conservant le dossier `.streamlit` :

- `app.py`
- `mdblist_oauth.py`
- `mdblist_provider.py`
- `normalized_model.py`
- `recommendation_engine.py`
- `progress_engine.py`
- `.streamlit/secrets.example.toml`
- `ETAPE-14.md`

Commit conseillé :

```text
feat: add local progress filters sorting and metadata merge
```

Après redéploiement, cliquer une seule fois sur **Actualiser mes données MDBList**. Le passage au schéma normalisé v4 invalide automatiquement l'ancien dataset de session afin d'ajouter les genres et les dates, puis tous les tris restent locaux.
