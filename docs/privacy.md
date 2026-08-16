# 🔒 Politique de confidentialité — Media Smart Lists

*Dernière mise à jour : 15 août 2026*

Media Smart Lists est une application web **gratuite et open source** qui vous
aide à gérer vos listes, votre historique et vos recommandations de films et
séries. Cette page explique simplement **quelles données sont utilisées, où
elles vont, et ce que nous ne faisons jamais avec**.

## En résumé

- **Nous ne stockons aucune de vos données sur un serveur.**
- **Nous ne créons aucun compte, aucune base de données.**
- **Vos identifiants ne sont jamais demandés ni transmis.**
- **Rien n'est partagé avec des tiers** (pas de publicité, pas de tracking).

## Quelles données sont utilisées ?

| Donnée | Usage | Où elle va |
|---|---|---|
| Données de votre compte **MDBList** (historique, listes, notes, progression) | Affichées et analysées dans l'application (statistiques, recommandations, nettoyage) | Lues **directement** depuis MDBList via OAuth, dans votre session |
| Votre **ZIP Trakt** (export local) | Importé **en lecture seule** pour l'analyse locale et la migration éventuelle | Parsé dans votre navigateur/session ; **le fichier n'est pas conservé** |
| Jetons OAuth MDBList | Authentification | Chiffrés (Fernet) dans un **cookie local de votre navigateur** ; jamais envoyés ailleurs |

## Ce que nous ne faisons jamais

- ❌ **Aucun mot de passe** : la connexion MDBList se fait par OAuth (device
  flow), sans jamais demander vos identifiants ;
- ❌ **Aucun serveur de stockage** : aucune base de données, aucun dossier
  de fichiers personnels sur un serveur ;
- ❌ **Aucun partage** : vos données ne sont jamais vendues, cédées ou
  transmises à des tiers ;
- ❌ **Aucun tracking publicitaire** : pas de cookies publicitaires, pas de
  mesure d'audience ;
- ❌ **Aucun secret dans les exports** : les sauvegardes JSON et les rapports
  Excel ne contiennent **jamais** vos jetons ni vos clés.

## Cache et session

- Un **cache temporaire** (cloisonné par utilisateur) accélère vos visites
  (les données MDBList sont rechargées depuis le cache plutôt que depuis
  l'API). Ce cache ne contient pas de mot de passe.
- Vos données de session disparaissent à la fermeture de l'onglet / à la fin
  de la session Streamlit.

## Écritures sur MDBList

L'application peut **écrire** sur votre compte MDBList, mais **uniquement**
quand vous le demandez explicitement et avec confirmation :

- suppression d'un contenu d'une liste / Watchlist ;
- marquer vu / non-vu ;
- marquer une série abandonnée ;
- **migration ZIP Trakt → MDBList** (historique, notes, Watchlist, listes).

Chaque écriture passe par : **aperçu → sauvegarde de sécurité → confirmation
explicite → écriture par lots → vérification**. Aucune écriture n'est faite
sans votre clic.

## Liens externes

L'application propose des liens vers des sites tiers (JustWatch, TMDB,
MDBList, Trakt). Ces sites ont leurs propres politiques de confidentialité ;
nous ne contrôlons pas leur contenu.

## Contact

Pour toute question relative à cette politique : ouvrez une issue sur le
[dépôt GitHub](https://github.com/Minijoe01/Media-Smart-Lists) (ou le canal
Discussions).
