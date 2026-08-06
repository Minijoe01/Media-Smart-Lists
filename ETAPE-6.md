# Media Smart Lists — Étape 6

## Ajustements visuels

- wordmark servi directement depuis `app/static/wordmark.png`, comme dans l'app legacy : largeur maximale 300 px, responsive et net ;
- suppression de l'accroche au-dessus du logo ;
- titre `Tableau de bord` plus compact, police système moderne ;
- rubans jaunes plus fins et moins gras ;
- badges `TEMPS RÉEL` et `IMPORT LOCAL` strictement inchangés ;
- arrière-plan et boutons legacy strictement inchangés.

## Premier connecteur MDBList

- saisie masquée de la clé ;
- conservation dans `st.session_state` uniquement ;
- aucun cookie, fichier ou cache ;
- deux GET : `/user` et `/lists/user` ;
- affichage forfait, quota et listes ;
- bouton d'oubli immédiat ;
- aucune écriture MDBList.

## Installation

1. GitHub : **Add file → Upload files**.
2. Envoyer `app.py` et `ETAPE-6.md`.
3. Commit : `feat: add read-only MDBList session connector`.
4. Attendre le redéploiement puis recharger l'app.
5. Cliquer `Préparer la connexion MDBList`, saisir la clé localement et tester.
