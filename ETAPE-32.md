# Media Smart Lists — Étape 32 : stats unifiées, cache F5, posters fiables, boutons au thème

## Statistiques : un seul jeu de filtres pour toute la page

La page Statistiques affichait **deux fois** l'historique des vues (un dans
l'expandeur « 📜 Historique des vues », un autre dans « Détail des
visionnages ») avec **deux jeux de filtres indépendants**.

Refonte :
- **une seule série de slicers** (Période · Type · Genre) en haut de page,
  appliquée à toute la page : historique, graphiques, ADN, studios,
  marathons, évolution des goûts ;
- la **vue d'ensemble en haut est marquée « non filtrée »** (toutes périodes
  confondues) — c'est explicite, plus de confusion ;
- une ligne récapitule les filtres appliqués ;
- l'expandeur « 📜 Historique des vues » (recherche, tableau, export CSV/JSON)
  ne contient plus de tableau dupliqué ;
- plus aucun « Détail des visionnages » en double.

## Cache persistant : rechargement après F5 (0 appel API)

- Bug corrigé dans le cache : le hachage forcé de toutes les chaînes rendait
  la clé de cache constante (partagée entre utilisateurs). Le hachage est
  normal : clé dérivée du token (SHA-256), jamais le token en clair.
- Nouveau : un **cookie marqueur** est posé quand les données MDBList sont
  chargées. Après un F5 (ou un retour sur l'application), si le cookie est
  présent et la connexion active, les données sont **rechargées
  automatiquement depuis le cache** — instantané, zéro appel API si le cache
  est encore chaud (1 h). Sinon, un rechargement réel est fait (l'utilisateur
  avait déjà chargé, c'est cohérent).

## Posters fiables (The Middle ↔ The Departed)

Quand un identifiant du ZIP Trakt est erroné (ex. un imdb_id qui pointe vers
un autre film), l'application vérifie désormais la **cohérence du titre** avant
d'appliquer poster/genres/durée : si le titre de la fiche MDBList ne partage
aucun mot significatif avec le titre attendu, la fiche est refusée. Fini les
posters « The Departed » sur « The Middle ». Un contenu dont l'identifiant est
faux reste simplement sans métadonnées (honnête).

## Boutons au thème

Les boutons « 📥 Charger mes données MDBList », « ✨ Enrichir avec MDBList »,
« 🚪 Quitter les données ZIP Trakt » et « 🔐 Gérer la connexion MDBList »
utilisent maintenant le même style « verre vert » que « Se déconnecter » et
« Actualiser les compteurs » (plus de dégradé « primary » distinct).

Le bouton « Gérer la connexion MDBList » a été réparé (clé Streamlit
dupliquée) et ouvre bien le panneau de connexion : compte, quota, liste des
listes, « Actualiser les compteurs » et « Se déconnecter ».

## Installation

Envoyer ce fichier à la racine du dépôt :

- `app.py` (modifié)
- `ETAPE-32.md` (NOUVEAU)

Aucun fichier à supprimer. Ne pas retoucher les autres fichiers (déjà à jour
en ligne). Aucun secret à modifier.

Commit conseillé :

```text
fix: unified stats filters, F5 cache restore, title-safe posters, themed buttons
```
