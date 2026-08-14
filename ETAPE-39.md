# Media Smart Lists — Étape 39 : déconnexion stabilisée, UI nettoyage, documentation complète

## 🔴 Déconnexion : retour au comportement « toujours connecté »

Le bug « charger mes données me déconnecte » persistait : il venait de la
mécanique de « déconnexion durable » (marqueur `?msl_logged_out=1` + cookie
écrasé) mise en place précédemment, qui se déclenchait à tort lors du
chargement après un auto-login.

Comme convenu, on **revient au comportement demandé** :
- on reste connecté au rechargement de page (F5) : la session est restaurée
  depuis le cookie OAuth ;
- la déconnexion volontaire ne vaut que pour la **session en cours** (le
  cookie est supprimé ; si la suppression échoue côté navigateur, on reste
  connecté — c'est le comportement « toujours connecté » voulu) ;
- toute la logique de marqueur logout / cookie « expired » a été retirée.

Testé : auto-login après F5 ✓, aucun marqueur posé au chargement ✓,
déconnexion de session ✓.

> ⚠️ Après déploiement, reconnectez-vous **une fois** pour repartir sur un
> cookie sain (si l'ancien cookie « expired » de la V38 traîne encore, il
> sera remplacé par la nouvelle connexion).

## ✍️ Marquer vu / non-vu : panneau repensé

- Titre lié au conteneur : « ✍️ Marquer vu / non-vu — « [Conteneur à auditer] » » ;
- **recherche par nom** + **filtre par type**, comme dans la suppression ;
- flux clair : choisir un contenu → **choisir l'action** (radio : ✅ Marquer vu /
  🔄 Marquer non-vu / 🚫 Marquer abandonnée pour les séries) → **cocher la
  confirmation** → bouton **« ⚡ Exécuter l'action »** ;
- tous les boutons au thème (`type="primary"`) ;
- **note retirée** : les notes MDBList se gèrent côté MDBList (notes entières
  0-10) ; la méthode API `set_rating` reste disponible pour un futur besoin.

## 🗑️ Suppression sécurisée : titre explicite

Le titre devient « 🗑️ Suppression sécurisée — « [Conteneur à auditer] » » avec
une phrase expliquant que cette liste correspond au conteneur choisi en haut
de la page.

## ❓ Guide ZIP Trakt compact

Le guide pas à pas utilise maintenant des cartes compactes (`guide-step`) aux
couleurs du thème : plus lisible, moins de place.

## 📚 Documentation & qualité (pour un beau dépôt)

- **README.md réécrit** : wordmark, présentation, sources (MDBList / ZIP
  Trakt), les 10 pages, démarrage rapide, sécurité, installation locale,
  architecture, liens ;
- **CHANGELOG.md** : synthèse des versions V21 → V39 ;
- **docs/social_card.png** : nouvelle carte sociale aux couleurs de l'app ;
- **docs/guide-alkodiques.md** : article de communauté (remplace l'article
  Trakt Smart Lists, explique le contexte du passage à Media Smart Lists) ;
- **LICENSE** (MIT) ;
- **.github/workflows/ci.yml** : CI compilation + scan de secrets ;
- `AI-HANDOFF.md` et `MEDIA-SMART-LISTS-TODO.md` mis à jour.

### Fichiers à supprimer du dépôt (obsolètes)

Voir `INSTALLATION-V39.txt` pour la liste exacte (ancienne app, anciens
journaux d'étapes, captures de l'ancienne app…).

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py` (modifié)
- `mdblist_oauth.py` (modifié)
- `README.md` (réécrit)
- `CHANGELOG.md` (NOUVEAU)
- `LICENSE` (NOUVEAU)
- `docs/social_card.png` (NOUVEAU)
- `docs/guide-alkodiques.md` (NOUVEAU)
- `.github/workflows/ci.yml` (NOUVEAU)
- `MEDIA-SMART-LISTS-TODO.md` (mis à jour)
- `AI-HANDOFF.md` (mis à jour)
- `ETAPE-39.md` (NOUVEAU)

+ SUPPRIMER les fichiers obsolètes listés dans `INSTALLATION-V39.txt`.
Aucun secret à modifier.
