# 🔒 Politique de sécurité — Media Smart Lists

Merci de prendre le temps de sécuriser Media Smart Lists. Cette page décrit
comment signaler une vulnérabilité de façon **responsable**.

## 🔐 Principes de sécurité du projet

- **Aucun secret dans le dépôt** : `.streamlit/secrets.toml` est ignoré par
  git ; le dépôt ne contient que `.streamlit/secrets.example.toml` (modèle).
- **Aucune base de données** : aucune donnée personnelle n'est stockée sur un
  serveur. Tout est calculé dans la session du navigateur.
- **OAuth sans mot de passe** : la connexion MDBList se fait par OAuth
  (device flow) ; vos identifiants ne sont jamais demandés ni transmis.
- **Jetons chiffrés** : les jetons OAuth sont chiffrés (Fernet) dans un cookie
  local au navigateur, et jamais inclus dans les exports.
- **Import ZIP sécurisé** : protections anti zip-slip, zip bomb, chemins
  absolus et fichiers trop volumineux.
- **Écritures contrôlées** : les écritures MDBList (suppression, vu/non-vu,
  notes, migration) exigent toujours aperçu, sauvegarde et confirmation
  explicite — jamais de suppression en masse silencieuse.

## 🐛 Signaler une vulnérabilité

**Ne publiez jamais une faille dans une issue publique avant sa correction.**

Pour signaler une vulnérabilité de sécurité :

1. Ouvrez une **issue privée** en sélectionnant le modèle
   « Security vulnerability » (si disponible) ;
2. OU envoyez un e-mail à l'adresse indiquée dans le profil du mainteneur
   sur GitHub ;
3. Décrivez :
   - le composant / fichier concerné ;
   - les étapes pour reproduire (sans données sensibles) ;
   - l'impact potentiel ;
   - une éventuelle suggestion de correctif.

## 🔄 Processus

- Vous recevrez un accusé de réception sous **72 h** ;
- une analyse sera menée et un correctif préparé ;
- une fois corrigé, la faille sera documentée (le cas échéant) dans le
  [CHANGELOG](CHANGELOG.md) ;
- un **délai de divulgation** de 90 jours est demandé avant toute
  publication publique.

## ✅ Bonnes pratiques pour les contributeurs

- Ne committez **jamais** de clé, jeton, secret ou données personnelles ;
- exécutez la CI (compilation + scan de secrets) avant de proposer une PR ;
- vérifiez que `.streamlit/secrets.toml` et `.env` restent ignorés par git.
