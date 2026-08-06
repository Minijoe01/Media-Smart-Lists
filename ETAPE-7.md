# Media Smart Lists — Étape 7 : OAuth Device Code MDBList

Cette étape remplace entièrement la saisie de clé API par :

- bouton OAuth MDBList ;
- URL `verification_uri_complete` préremplie ;
- code utilisateur ;
- QR code généré localement ;
- polling automatique comme dans Trakt Smart Lists ;
- access token en session ;
- refresh token chiffré par Fernet avant cookie ;
- reconnexion automatique et rotation du refresh token ;
- révocation + suppression locale lors de la déconnexion.

## Fichiers

- `app.py` : interface OAuth et thème uniformisé ;
- `mdblist_oauth.py` : logique OAuth isolée ;
- `requirements.txt` : ajout de `cryptography` ;
- `ETAPE-7.md` : notice.

## Installation

1. GitHub : **Add file → Upload files**.
2. Envoyer les quatre fichiers à la racine.
3. Commit : `feat: replace API key login with persistent MDBList device OAuth`.
4. Attendre le redéploiement complet (les dépendances changent).
5. Tester connexion, F5, fermeture/réouverture du navigateur, puis déconnexion.

## Limites normales

La reconnexion persiste sur le même navigateur. Elle est perdue si les cookies sont effacés, si MDBList révoque le refresh token ou si `TOKEN_ENCRYPTION_KEY` est remplacée.
