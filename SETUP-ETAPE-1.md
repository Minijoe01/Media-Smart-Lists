# Media Smart Lists — Étape 1

Ce paquet ajoute uniquement les garde-fous de base. Il ne modifie pas encore `app.py`.

## Fichiers

- `.gitignore` : empêche d'ajouter par erreur secrets, ZIP et données personnelles.
- `.streamlit/config.toml` : conserve le thème et réactive les protections Streamlit par défaut.
- `.streamlit/secrets.example.toml` : exemple vide ; aucune vraie clé ne doit y être copiée.

## Mise en place sur GitHub

1. Extraire ce ZIP sur l'ordinateur.
2. Dans le dépôt `Media-Smart-Lists`, cliquer **Add file → Upload files**.
3. Déposer les trois fichiers en conservant les chemins et le dossier `.streamlit`.
4. Vérifier que `.streamlit/config.toml` remplace bien l'ancien fichier.
5. Commit message : `chore: secure initial Media Smart Lists configuration`.
6. Ne pas encore déployer l'app : l'ancien `app.py` exige toujours les secrets Trakt. La prochaine étape corrigera ce point.

## Important

Ne jamais créer ni envoyer sur GitHub :

```text
.streamlit/secrets.toml
```
