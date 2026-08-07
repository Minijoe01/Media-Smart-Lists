# Media Smart Lists — dossier de reprise pour une autre IA

> À transmettre avec `MEDIA-SMART-LISTS-TODO.md` et `migrate_trakt_zip_to_mdblist.py` si la conversation Arena arrive à sa limite.

## Mission

Continuer **Media Smart Lists**, clone fournisseur-neutre de l'ancienne application **Trakt Smart Lists**, sans repartir de zéro et sans réinventer l'interface.

L'utilisateur veut conserver :

- le fond radial Aston Martin legacy ;
- les boutons legacy ;
- le menu latéral ;
- les calculs, statistiques, Wrapped, succès et recommandations historiques ;
- les mêmes widgets quel que soit le fournisseur ;
- une expérience simple avec des ZIP/fichiers prêts à envoyer dans GitHub.

Toujours communiquer en français et avancer une étape à la fois.

## Liens

```text
Dépôt actuel : https://github.com/Minijoe01/Media-Smart-Lists
App actuelle : https://media-smart-lists.streamlit.app
Ancien dépôt  : https://github.com/Minijoe01/Trakt-Smart-Lists
Ancienne app  : https://trakt-smart-lists.streamlit.app
```

## Date et localisation de référence

```text
7 août 2026
Europe/Paris — Dunkerque, France
```

## Architecture actuelle

```text
MDBListProvider ──┐
                  ├── NormalizedDataset ── UI commune
TraktZipProvider ─┘   (à intégrer)
```

Principaux fichiers :

```text
app.py
mdblist_oauth.py
mdblist_provider.py
normalized_model.py
recommendation_engine.py
progress_engine.py
playback_engine.py
list_audit_engine.py
calendar_engine.py
history_engine.py
```

## État de l'application

Fonctionnel :

- OAuth Device Code MDBList persistant ;
- dashboard et quota ;
- Watchlist et listes individuelles/agrégées ;
- En cours / Up Next ;
- Progression Fantôme pour les pauses ;
- Nettoyage des listes et doublons ;
- Que regarder : score, friction, infobulles, presets et roulettes ;
- calendrier avec fallback local ;
- historique des vues repliable ;
- historique des ajouts aux listes ;
- exports CSV, JSON et ICS selon les pages.

Encore placeholders ou incomplet :

- graphiques statistiques legacy ;
- Rendez-vous annuel / Wrapped ;
- Succès ;
- Sauvegarde neutre/restauration ;
- TraktZipProvider dans l'app ;
- écritures MDBList ;
- Now Playing MDBList non fiable avec l'installation Kodi actuelle.

Consulter `MEDIA-SMART-LISTS-TODO.md` pour la liste exhaustive et à jour.

## Secrets — interdictions absolues

Ne jamais demander, recevoir, afficher ou commiter :

```text
clé API MDBList
MDBLIST_CLIENT_ID réel
TOKEN_ENCRYPTION_KEY réelle
access_token / refresh_token OAuth
secret GitHub / token GitHub
```

Les vrais secrets sont dans Streamlit Settings. Ils ne doivent jamais être modifiés sans raison.

`TOKEN_ENCRYPTION_KEY` est une clé Fernet normale et obligatoire. La changer rend les cookies existants illisibles.

## OAuth MDBList

Endpoints :

```text
POST https://api.mdblist.com/oauth/device-authorization/
POST https://api.mdblist.com/oauth/token/
POST https://api.mdblist.com/oauth/revoke_token/
```

Scope utilisé : `write`.

L'expérience validée comprend URL, QR, user code, polling automatique, cookie chiffré v2, refresh et déconnexion.

## Quota MDBList

Compte Free : 1000 appels par jour, reset à `00:00 UTC`.

Règles :

- afficher le coût quand une action consomme réellement un appel ;
- reformuler les calculs gratuits en `quota MDBList préservé`, pas en note technique développeur ;
- utiliser le cache de session ;
- batch maximum 200 quand disponible ;
- ne jamais appeler une API par carte ;
- recommandations, tris, filtres et roulette doivent rester locaux.

## Design figé

Fond exact — ne pas modifier :

```css
background: radial-gradient(
    ellipse 100% 85% at 50% 0%,
    #006B62 0%,
    #005951 28%,
    #00443E 55%,
    #002B28 80%,
    #011715 100%
)
```

Boutons : verre vert sombre, primaire `#00A392 → #00524B`, sans ombre, rayon 16 px.

Badges figés :

```text
TEMPS RÉEL · LECTURE/ÉCRITURE
IMPORT LOCAL · LECTURE SEULE
```

Wordmark : `SMART LISTS / MEDIA` depuis `static/wordmark.png`.

Ne pas ajouter de vert olive Streamlit natif.

## Migration personnelle déjà terminée

```text
Archive SHA-256 : 25feb749dc33a3c4bf0183eb1560bc3cf4a36dbfb0b4ee0b62624f0c40ec077b
Événements Trakt : 6903
Films uniques vus : 308
Épisodes uniques vus : 6276
Rewatch supplémentaires : 319
Notes : 127 films, 89 séries, 2 saisons, 6 épisodes
Watchlist MDBList : 266 films, 0 série
Liste Séries : 261 séries
Liste Films familiaux : 23 films
Audit conteneurs exclusifs : PASS, 0 doublon
```

Les épisodes incompatibles MDBList ont été corrigés manuellement. Ne jamais relancer aveuglément l'import complet.

## Script communautaire à préserver

Fichier :

```text
migrate_trakt_zip_to_mdblist.py
```

Ce script est le candidat principal au futur dépôt :

```text
Minijoe01/Trakt-ZIP-to-MDBList
```

Propriétés obligatoires à conserver :

- bibliothèque standard uniquement ;
- dry-run par défaut ;
- aucune suppression distante ;
- clé masquée et jamais enregistrée ;
- protections ZIP ;
- préflight GET ;
- confirmation exacte `IMPORTER` avant écriture ;
- sauvegarde locale de toutes les dates et données non représentables ;
- rapports JSON/CSV ;
- clés jamais journalisées.

Ne pas réécrire ce script depuis zéro : il a déjà importé efficacement le compte de l'utilisateur.

## Méthode de travail demandée

À chaque étape :

1. vérifier directement le dernier commit GitHub ;
2. modifier le minimum de fichiers ;
3. compiler et exécuter des tests locaux ;
4. scanner les nouveaux fichiers pour détecter d'éventuels secrets ;
5. créer un ZIP contenant uniquement les fichiers à remplacer ;
6. donner le SHA-256 du ZIP ;
7. attendre l'upload utilisateur ;
8. revérifier les fichiers GitHub avant de poursuivre.

Ne pas demander à l'utilisateur d'exécuter des manipulations abstraites si un ZIP prêt à envoyer peut être fourni.

## Priorité de reprise recommandée

1. Lire `MEDIA-SMART-LISTS-TODO.md`.
2. Vérifier la dernière étape déployée et les retours utilisateur.
3. Restaurer les graphiques Statistiques legacy.
4. Restaurer Rendez-vous annuel / Wrapped.
5. Restaurer Succès.
6. Ajouter Sauvegarde neutre.
7. Intégrer `TraktZipProvider` en réutilisant les parseurs du script de migration.
8. N'ajouter les écritures MDBList qu'après stabilisation et avec aperçu/confirmation.

## Références locales historiques

Si elles sont encore disponibles dans l'espace de travail Arena :

```text
/home/user/trakt-smart-lists-research/app.py
/home/user/migrate_trakt_zip_to_mdblist.py
/home/user/Trakt-Smart-Lists-TODO-Migration.md
/home/user/Smart-Lists-Hub-Guide.md
```

Si elles ne sont plus disponibles, utiliser l'ancien dépôt GitHub et les fichiers fournis avec ce handoff.
