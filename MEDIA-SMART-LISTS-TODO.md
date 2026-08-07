# Media Smart Lists — TODO actif

> Dernière mise à jour : 7 août 2026  
> Dépôt : https://github.com/Minijoe01/Media-Smart-Lists  
> Application : https://media-smart-lists.streamlit.app  
> Ancienne application conservée : https://github.com/Minijoe01/Trakt-Smart-Lists

Ce fichier est la feuille de route active. Les anciens documents `Trakt-Smart-Lists-TODO-Migration.md` et `Smart-Lists-Hub-Guide.md` restent des archives de conception mais contiennent des décisions dépassées.

---

## Règles permanentes

- [x] Application fournisseur-neutre : `MDBListProvider` et futur `TraktZipProvider` produisent le même `NormalizedDataset`.
- [x] Aucun accès API Trakt requis.
- [x] OAuth Device Code MDBList : URL, QR, code, polling, refresh et déconnexion.
- [x] Tokens chiffrés dans un cookie Fernet ; aucune vraie clé dans GitHub.
- [x] Ne jamais demander à l'utilisateur ses secrets dans une conversation.
- [x] Quota MDBList Free pris en compte : 1000 appels/jour, reset à minuit UTC.
- [x] Calculs, filtres, tris, recommandations et audits locaux dès que possible.
- [x] Aucune suppression distante sans aperçu, sauvegarde et confirmation explicite.
- [x] Thème legacy conservé : fond radial Aston Martin, boutons legacy, menu latéral et badges validés.

---

## Fonctionnalités terminées

### Migration personnelle Trakt → MDBList

- [x] ZIP analysé et sauvegardé localement.
- [x] 308 films vus importés.
- [x] 6276 épisodes finalement représentés, dont les incompatibilités corrigées manuellement.
- [x] 127 notes films, 89 séries, 2 saisons et 6 épisodes.
- [x] Watchlist native MDBList : films uniquement.
- [x] Liste statique `Séries`.
- [x] Liste statique `Films familiaux`.
- [x] Audit exclusif sans doublon entre conteneurs : PASS.
- [x] Historique complet et dates de revisionnage conservés dans les sauvegardes locales.

### Application Media Smart Lists

- [x] Nouveau dépôt autonome et déploiement Streamlit.
- [x] Sécurité initiale : `.gitignore`, CORS/XSRF par défaut, exemple de secrets.
- [x] OAuth MDBList persistant et déconnexion avec révocation.
- [x] Compteur de quota et nombre d'appels d'un chargement.
- [x] Chargement MDBList : watched, ratings, Watchlist, listes, playback, Up Next, dropped et genres.
- [x] Watchlist et chaque liste statique/dynamique séparément.
- [x] Agrégats : toutes statiques, toutes dynamiques, toutes personnelles, Watchlist + toutes listes.
- [x] `En cours` : posters, épisodes suivants, temps vu/restant, progression, genres et tris locaux.
- [x] `Que regarder ?` : profil de goûts, score explicable, friction, infobulles, presets, filtres, tris et roulettes.
- [x] `Progression Fantôme` : reprises en pause, filtres, temps restant et tentative ciblée Now Playing.
- [x] `Nettoyage des listes` : audit local, doublons fusionnés, conteneurs exacts, rapports CSV/JSON.
- [x] Types MDBList affichés clairement : Watchlist, liste statique, dynamique, IA et flux.
- [x] Enrichissement facultatif de posters par lot de 200 maximum.
- [x] `Calendrier` : requête ciblée, cache, filtres, export CSV/ICS et calendrier local de secours.
- [x] `Statistiques` : historique repliable, filtres, durées corrigées, genres et exports CSV/JSON.
- [x] Historique des ajouts aux listes avec horodatage, conteneur, tri et export.

---

## Priorité immédiate — vérifier l'étape 21

- [ ] Vérifier qu'un épisode DBZ affiche environ 20 minutes et non la durée cumulée de la série.
- [ ] Vérifier que le temps global est exprimé intelligemment en heures, jours, mois ou années.
- [ ] Vérifier que l'historique des vues est fermé par défaut dans un menu déroulant.
- [ ] Vérifier le calendrier de secours lorsque `/calendar/events` MDBList échoue.
- [ ] Vérifier l'historique des ajouts : date/heure, liste et tri décroissant.

---

## Prochaines fonctionnalités legacy

### Statistiques

- [ ] Restaurer les graphiques mensuels et annuels.
- [ ] Restaurer la répartition jour de semaine / heure de journée.
- [ ] Restaurer l'évolution des goûts par année.
- [ ] Restaurer les marathons de séries.
- [ ] Restaurer les records personnels.
- [ ] Vérifier toutes les conversions de runtime sur de gros comptes.

### Rendez-vous annuel / Wrapped

- [ ] Reconnecter la page `Rendez-vous annuel` au modèle normalisé.
- [ ] Générer les indicateurs annuels films, épisodes, heures, genres et records.
- [ ] Restaurer l'image PNG partageable legacy.
- [ ] Préserver les dates complètes du ZIP Trakt lorsqu'il est utilisé.

### Succès

- [ ] Reconnecter les badges legacy.
- [ ] Films, épisodes, diversité, marathons, nocturne et rewatches.
- [ ] Ne pas attribuer de badge sur une donnée absente du fournisseur.

### Sauvegarde

- [ ] Export JSON neutre et versionné du `NormalizedDataset`.
- [ ] Exports CSV par catégorie.
- [ ] Ne jamais inclure token, cookie, clé, e-mail ou secret.
- [ ] Ajouter une restauration testée avant toute écriture distante.

---

## TraktZipProvider — priorité produit

- [ ] Intégrer le bouton `Importer un ZIP Trakt` actuellement présent mais non fonctionnel.
- [ ] Réutiliser les parseurs sécurisés du script de migration.
- [ ] Protéger contre zip-slip, zip bomb, liens et tailles excessives.
- [ ] Produire exactement le même modèle que MDBList.
- [ ] Conserver chaque événement de visionnage et chaque rewatch.
- [ ] Afficher la date de l'export et le badge `IMPORT LOCAL · LECTURE SEULE`.
- [ ] Faire fonctionner Dashboard, recommandations, calendrier, historique, statistiques, Wrapped et succès.
- [ ] Ne conserver aucun ZIP côté serveur après la session.

Architecture cible :

```text
MDBListProvider ──┐
                  ├── NormalizedDataset ── mêmes pages/widgets
TraktZipProvider ─┘
```

---

## Écritures MDBList — uniquement après stabilisation lecture

- [ ] Ajouter/retirer de la Watchlist.
- [ ] Ajouter/retirer d'une liste statique.
- [ ] Marquer vu/non vu.
- [ ] Notes personnelles.
- [ ] Dropped.
- [ ] Ne jamais écrire dans une liste dynamique/IA/flux.
- [ ] Chaque opération : aperçu → export de sauvegarde → confirmation explicite → écriture → vérification GET.
- [ ] Aucun delete en lot par défaut.
- [ ] Journal local nettoyé de tous les secrets.

---

## Métadonnées et quota

- [ ] Construire un cache générique de métadonnées par identifiants canoniques.
- [ ] Enrichissement MDBList batch, maximum 200 médias par appel.
- [ ] Ne jamais faire un appel par carte.
- [ ] Studios et acteurs : activer seulement lorsque le fournisseur les fournit ou via une source groupée sûre.
- [ ] Vérifier la qualité de `calendar/events` et de `sync/now-playing` avec de futures versions MDBList.
- [ ] Étudier `last_activities` pour actualiser uniquement les sections réellement modifiées.
- [ ] Passer progressivement de pagination offset à cursor lorsque nécessaire.

---

## Outil communautaire Trakt ZIP → MDBList

Dépôt prévu :

```text
Minijoe01/Trakt-ZIP-to-MDBList
```

Fichier principal déjà fonctionnel :

```text
migrate_trakt_zip_to_mdblist.py
```

État du script :

- [x] bibliothèque standard Python uniquement ;
- [x] dry-run par défaut ;
- [x] aucune suppression ;
- [x] clé MDBList demandée de façon masquée ou via variable d'environnement ;
- [x] protections ZIP ;
- [x] sauvegarde des rewatches et données non représentables ;
- [x] préflight GET ;
- [x] confirmation exacte `IMPORTER` avant écriture ;
- [x] import watched, ratings, Watchlist, collection et listes statiques ;
- [x] organisation exclusive Watchlist/Séries/Films familiaux ;
- [ ] créer le dépôt séparé ;
- [ ] ajouter `README.md`, `SECURITY.md` et `requirements.txt` ;
- [ ] ajouter `start_windows.bat` ;
- [ ] publier une première Release ZIP avec SHA-256 ;
- [ ] ajouter des fixtures anonymisées et tests automatiques ;
- [ ] ne jamais accepter ni enregistrer les clés d'un utilisateur sur un serveur public.

Utilisation sûre :

```text
python migrate_trakt_zip_to_mdblist.py export-trakt.zip
python migrate_trakt_zip_to_mdblist.py export-trakt.zip --check-api
python migrate_trakt_zip_to_mdblist.py export-trakt.zip --apply
```

---

## Kodi

- [ ] Reprendre plus tard les tests du MDBList Scrobbler avec journal DEBUG ciblé.
- [ ] Vérifier les versions réellement distribuées par les dépôts Kodi.
- [ ] Identifier un seul auteur principal de scrobble par lecture pour éviter les doublons.
- [ ] Garder Media Smart Lists indépendant de Plex et Kometa ; seules leurs bonnes idées d'architecture sont réutilisées.

---

## Documentation et qualité

- [ ] Mettre à jour le README du nouveau dépôt et toutes les anciennes mentions Trakt Smart Lists.
- [ ] Corriger définitivement `.streamlit/secrets.example.toml` si l'ancienne version est encore en ligne.
- [ ] Ajouter licence, politique de confidentialité et `SECURITY.md`.
- [ ] Ajouter tests unitaires au dépôt, pas uniquement dans l'espace de travail Arena.
- [ ] Ajouter CI : compilation, tests, scan de secrets et dépendances.
- [ ] Ajouter changelog synthétique plutôt qu'accumuler uniquement `ETAPE-*.md`.
- [ ] Revoir les messages encore trop techniques dans les pages non restaurées.

---

## Définition de la prochaine version stable

- [ ] Toutes les pages du menu legacy sont fonctionnelles ou clairement marquées indisponibles.
- [ ] MDBList lecture stable avec cache et budget de quota.
- [ ] ZIP Trakt lecture seule fonctionnel.
- [ ] Sauvegarde neutre téléchargeable.
- [ ] Tests reproductibles dans GitHub Actions.
- [ ] Aucun secret dans le dépôt ou les exports.
- [ ] Écritures MDBList derrière aperçu et confirmation.
