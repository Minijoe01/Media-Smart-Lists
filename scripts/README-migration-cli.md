# 🧰 Script CLI : Migration ZIP Trakt → MDBList

> **Pour les utilisateurs avancés** qui veulent migrer leur export Trakt vers
> MDBList **en local, sans passer par l'application web** (la page
> « 📦 Migration Trakt → MDBList » de Media Smart Lists fait la même chose
> en ligne, sans Python).

Ce script analyse un export ZIP Trakt et l'importe dans MDBList, en
**simulation (dry-run) par défaut** : rien n'est écrit tant que vous ne
passez pas `--apply`.

## Prérequis

- **Python 3.9+** (bibliothèque standard uniquement, aucune dépendance) ;
- une **clé API MDBList** (gratuite) : [mdblist.com/preferences/#api](https://mdblist.com/preferences/#api) ;
- un **export ZIP Trakt** : [app.trakt.tv/settings/data?mode=media](https://app.trakt.tv/settings/data?mode=media) → Export → Exporter maintenant (quelques minutes) → télécharger `export-trakt-*.zip`.

## Démarrage rapide (Windows)

Double-cliquez sur **`start_windows.bat`** (il lance le script en mode
simulation sur le ZIP du dossier courant, ou affiche l'aide si aucun ZIP
n'est trouvé).

## Usage

```bash
# 1) Analyser le ZIP SANS toucher à MDBList (dry-run)
python migrate_trakt_zip_to_mdblist.py trakt-export.zip

# 2) Vérifier le compte et les quotas MDBList (GET uniquement)
python migrate_trakt_zip_to_mdblist.py trakt-export.zip --check-api

# 3) Importer réellement (avec confirmation explicite)
#    PowerShell :
$env:MDBLIST_API_KEY="votre-cle"
python migrate_trakt_zip_to_mdblist.py trakt-export.zip --apply
#    Linux/macOS :
MDBLIST_API_KEY="votre-cle" python3 migrate_trakt_zip_to_mdblist.py trakt-export.zip --apply
```

### Options

| Option | Description |
|---|---|
| `--apply` | Écrit réellement dans MDBList (sinon simulation locale) |
| `--check-api` | Teste la clé, les quotas et l'état MDBList (aucune écriture) |
| `--sections watched,ratings,watchlist,collection,lists` | Import partiel |
| `--list-layout original\|compact-3\|exclusive-watchlist\|hybrid-watchlist` | Organisation des listes (voir ci-dessous) |
| `--output-dir DOSSIER` | Dossier des rapports locaux (défaut : `trakt_mdblist_migration/`) |

## Organisation des listes (`--list-layout`)

- `original` : conserve les listes Trakt telles quelles ;
- `compact-3` : regroupe tout en 3 listes (Séries, Films familiaux, autres) ;
- `exclusive-watchlist` (recommandé) : les séries vont dans la liste
  « Séries », les films familiaux dans « Films familiaux », les autres films
  uniquement dans la **Watchlist** — aucune duplication de conteneur.

## Sécurité

- **dry-run par défaut** : aucun appel réseau sans `--apply` ;
- **aucune suppression distante** ;
- la **clé API** est lue depuis `MDBLIST_API_KEY` ou demandée de façon masquée
  (jamais affichée) ;
- protections ZIP (zip-slip, bombes, tailles) ;
- **confirmation explicite** (`IMPORTER`) avant toute écriture ;
- sauvegarde neutre locale de l'historique complet et des éléments non
  importables.

## Limitations MDBList (importantes)

- MDBList conserve un état vu et une **dernière date par média**, pas
  l'ensemble des événements de rewatch Trakt (tous les événements restent
  archivés localement dans le rapport) ;
- les listes statiques MDBList acceptent surtout films et séries : les
  saisons, épisodes et personnes sont archivés dans le rapport mais non
  ajoutés ;
- l'API de création de liste ne permet pas de restaurer la description ni les
  dates d'ajout/rangs Trakt de façon garantie.

## Exemple complet

```bash
# Vérifier l'organisation recommandée (aucun doublon de conteneur)
python migrate_trakt_zip_to_mdblist.py trakt-export.zip --check-api \
    --list-layout exclusive-watchlist

# Import partiel (historique + notes + watchlist seulement)
python migrate_trakt_zip_to_mdblist.py trakt-export.zip --apply \
    --sections watched,ratings,watchlist
```
