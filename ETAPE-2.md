# Media Smart Lists — Étape 2

Cette étape remplace temporairement le point d'entrée par une page d'accueil indépendante de Trakt.

## Fichiers à envoyer sur GitHub

- `app.py` : nouveau point d'entrée Media Smart Lists ; aucun secret requis.
- `legacy_trakt_app.py` : copie de sécurité de l'ancien monolithe Trakt, non exécutée.
- `ETAPE-2.md` : cette notice.

## Installation

1. Dans `Minijoe01/Media-Smart-Lists`, cliquer **Add file → Upload files**.
2. Déposer ces trois fichiers.
3. GitHub doit indiquer que `app.py` sera modifié et que les deux autres fichiers seront ajoutés.
4. Commit message : `feat: add provider-neutral Media Smart Lists landing page`.
5. Ne saisir encore aucun secret.
6. Après vérification du commit, l'app pourra être déployée pour le premier test visuel.

L'ancien code n'est pas perdu : il est conservé dans `legacy_trakt_app.py` et reste dans l'ancien dépôt Trakt Smart Lists.
