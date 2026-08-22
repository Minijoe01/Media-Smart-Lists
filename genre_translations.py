"""Traduction des genres (TMDB/MDBList sont en anglais) vers le français.

TMDB et MDBList renvoient les genres en anglais (« Comedy », « Science
Fiction »…). Ce module fournit la traduction officielle TMDB-FR, appliquée
au point d'entrée unique du modèle normalisé afin que les genres soient en
français PARTOUT (dashboard, statistiques, Que regarder ?, cartes…).

La correspondance par emoji/preset est ajustée côté moteur pour reconnaître
les deux langues (sécurité pour les données éventuellement non traduites).
"""

from __future__ import annotations


# Clé = genre en anglais (minuscules), valeur = libellé français officiel TMDB.
GENRE_FR: dict[str, str] = {
    "action": "Action",
    "adventure": "Aventure",
    "animation": "Animation",
    "comedy": "Comédie",
    "crime": "Crime",
    "documentary": "Documentaire",
    "drama": "Drame",
    "family": "Familial",
    "fantasy": "Fantastique",
    "history": "Histoire",
    "horror": "Horreur",
    "music": "Musique",
    "musical": "Comédie musicale",
    "mystery": "Mystère",
    "romance": "Romance",
    "science fiction": "Science-fiction",
    "sci-fi": "Science-fiction",
    "scifi": "Science-fiction",
    "tv movie": "Téléfilm",
    "thriller": "Thriller",
    "war": "Guerre",
    "western": "Western",
    # Genres spécifiques TV.
    "kids": "Enfants",
    "news": "Actualités",
    "reality": "Téléréalité",
    "soap": "Feuilleton",
    "talk": "Divertissement",
    "war & politics": "Guerre & Politique",
    "action & adventure": "Action & Aventure",
    "sci-fi & fantasy": "Science-fiction & Fantastique",
    "detective": "Policier",
    # Variantes francophones déjà rencontrées (idempotence).
    "comédie": "Comédie",
    "documentaire": "Documentaire",
    "fantastique": "Fantastique",
    "horreur": "Horreur",
    "guerre": "Guerre",
    "aventure": "Aventure",
    "mystère": "Mystère",
    "familial": "Familial",
    "science-fiction": "Science-fiction",
    "policier": "Policier",
    "téléfilm": "Téléfilm",
}


def translate_genre(name: str) -> str:
    """Renvoie le libellé français d'un genre, ou le libellé inchangé s'il est
    inconnu (certains genres atypiques restent tels quels plutôt que d'être
    mal traduits). Idempotent : un genre déjà en français reste en français.
    """
    if name is None:
        return ""
    text = str(name).strip()
    if not text:
        return ""
    translated = GENRE_FR.get(text.lower())
    return translated or text


def translate_genres(values: list) -> list[str]:
    """Traduit une liste de genres (chaînes ou dicts {name/title/slug})."""
    output: list[str] = []
    for value in values or []:
        if isinstance(value, dict):
            raw = value.get("name") or value.get("title") or value.get("slug")
        else:
            raw = value
        if raw is None:
            continue
        translated = translate_genre(str(raw))
        if translated and translated not in output:
            output.append(translated)
    return output
