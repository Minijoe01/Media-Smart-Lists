# Media Smart Lists — Étape 15 : « Que regarder ? » legacy enrichi

## Infobulles restaurées

Les pastilles n'affichent plus directement `+10`, `−6`, etc.

- la carte montre uniquement un libellé court : `❤️ Tes genres`, `⏱️ Durée idéale`, `📥 Ajout récent`… ;
- le détail du calcul et le nombre exact de points apparaissent au survol ;
- les pastilles sont aussi accessibles au clavier avec Tab puis focus ;
- les avertissements conservent leur couleur distincte.

Le score global `/100` et l'indice de friction restent visibles.

## Signaux legacy rétablis sans appel API

Le moteur personnel v2 utilise uniquement le dataset déjà chargé :

- goûts récents avec décroissance temporelle, demi-vie de deux ans ;
- genres regardés et genres bien ou mal notés personnellement ;
- déceptions personnelles récurrentes ;
- saturation des six dernières vues et petit bonus de variété ;
- pays de production habituels ;
- décennies favorites et classiques ;
- durée personnelle fondée sur les percentiles de l'historique ;
- note communauté, popularité et pépites confidentielles ;
- récence de sortie et ancienneté dans la liste ;
- séries courtes, commencées, presque terminées, terminées ou annulées ;
- certification familiale ;
- friction et adaptation à une fin de soirée.

## Navigation et tris legacy

Ajouts dans **Que regarder ?** :

- sections `Recommandations personnalisées`, `Pourquoi pas` et `Ne correspond pas à mon profil` ;
- tri par popularité ;
- tri par date d'ajout ;
- films d'abord ;
- séries d'abord ;
- vue `Pas pour moi` ;
- roulette classique recentrée sur les bons scores ;
- lien de recherche JustWatch, sans appel MDBList.

## Studios et acteurs : état réel de l'API

Le moteur sait maintenant exploiter gratuitement les champs déjà présents sous les formes suivantes :

- studios, sociétés de production, réseaux ;
- acteurs ou casting principal.

Lorsqu'au moins trois titres historiques partagent un studio ou un acteur, le moteur peut détecter un studio fétiche ou un visage familier et accorder un petit bonus, expliqué dans l'infobulle.

Cependant, les réponses MDBList utilisées pour la Watchlist et les listes ne fournissent actuellement pas systématiquement ces champs. L'API batch MDBList accepte jusqu'à 200 médias mais sa documentation n'expose que `keyword` et `review` comme enrichissements facultatifs, pas le casting ni les sociétés de production. Les endpoints `people/favorites` donnent les personnes favorites du compte, mais pas le casting de chaque contenu candidat.

Media Smart Lists ne lance donc **aucun appel TMDb ou MDBList par contenu**. Le bonus fonctionne automatiquement si un fournisseur présent ou futur apporte ces métadonnées dans le modèle normalisé ; sinon il reste silencieusement désactivé.

## Coût API

- score : 0 appel ;
- profil : 0 appel ;
- infobulles : 0 appel ;
- nouveaux tris : 0 appel ;
- sections et vue Pas pour moi : 0 appel ;
- roulette : 0 appel ;
- studios/acteurs : 0 appel.

Le comportement déjà connu du filtre Genre reste inchangé : une source non encore filtrée peut demander une requête MDBList, ensuite mémorisée dans le cache de session.

## Installation

Envoyer uniquement ces trois fichiers à la racine du dépôt :

- `app.py`
- `recommendation_engine.py`
- `ETAPE-15.md`

Commit conseillé :

```text
feat: restore recommendation tooltips and legacy taste signals
```

Aucun changement de secret et aucun rechargement obligatoire du dataset. Un simple redéploiement suffit.
