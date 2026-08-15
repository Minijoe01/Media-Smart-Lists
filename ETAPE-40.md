# Media Smart Lists — Étape 40 : guide en jaune, recherche par frappe, docs finalisées

## ❓ Guide ZIP Trakt : HTML pur + jaune citron

Le guide pas à pas affichait des balises `**` et des liens markdown non rendus
(le markdown n'est pas interprété à l'intérieur des blocs HTML). Corrigé :
tout le guide est maintenant en **HTML pur** (`<strong>`, `<a>`, `<code>`) et
**entièrement jaune citron** (#CEDC00) avec fond et bordure assortis — plus
aucune balise visible, plus de lien cassé.

## ✍️ « Marquer vu / non-vu » : recherche par frappe

Comme demandé, le sélecteur de contenu utilise maintenant la **même recherche
par frappe que la suppression sécurisée** (multiselect avec saisie filtrante) :
tapez « ra » → vous voyez « Dragon Ball » ET « Rasta Rocket ». Le filtre par
type (Films / Séries) est conservé. Flux : choisir le contenu → choisir
l'action (radio) → cocher la confirmation → « ⚡ Exécuter l'action ».

## 📚 Documentation & dépôt

- **README** : section « Pour qui » corrigée — l'app est pensée **en priorité
  pour les utilisateurs MDBList**, et pour les utilisateurs Trakt qui veulent
  faire le ménage via leur ZIP (contexte : renforcement des règles Trakt,
  connexion directe impossible, ZIP expliqué).
- **Social card** : régénérée sur le modèle de l'ancienne carte Trakt, avec le
  wordmark Media Smart Lists.
- **Article Alkodiques** : réécrit en « nouvel article » — présente Media Smart
  Lists, héritée de Trakt Smart Lists (lien vers l'ancien article, sans
  redire l'histoire de TV Time), explique que Trakt Smart Lists est en stand-by
  (réactivation = compte Trakt VIP, réservé aux VIP), que Trakt reste utilisable
  **via ZIP** (avec la marche à suivre pour l'obtenir) et que la connexion
  directe se fait via MDBList.
- **Excel d'audit** (`docs/audit-fichiers-github.xlsx`) : liste tous les
  fichiers du dépôt (sous-dossiers inclus) avec l'action recommandée
  (GARDER / SUPPRIMER / OPTIONNEL) et la raison.
- **CHANGELOG** : tout l'historique y est résumé → toutes les `ETAPE-*.md`
  peuvent être supprimées pour un dépôt propre.

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py` (modifié)
- `mdblist_oauth.py` (modifié)
- `README.md` (modifié)
- `CHANGELOG.md` (modifié)
- `docs/social_card.png` (régénérée)
- `docs/guide-alkodiques.md` (réécrit)
- `docs/audit-fichiers-github.xlsx` (NOUVEAU)
- `ETAPE-40.md` (NOUVEAU)

+ SUPPRIMER : toutes les `ETAPE-*.md` (ETAPE-2 à ETAPE-39), `SETUP-ETAPE-1.md`,
  `TODO.md`, `legacy_trakt_app.py`, `trakt-logo.svg`,
  `docs/Dashboard.png`, `docs/Doublons.png`, `docs/quoi_regarder.png`,
  `docs/series.png`, `docs/statistiques.png` (voir l'Excel d'audit).
Aucun secret à modifier.
