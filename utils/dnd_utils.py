import os
import shlex  # Pour une meilleure gestion des chemins avec espaces


def clean_dropped_filepaths(filepaths_str: str | None) -> list[str]:
    """
    Nettoie la chaîne de caractères des chemins de fichiers retournée par TkinterDnD2.
    event.data peut retourner des chemins sous différentes formes :
    - "{C:/chemin/vers/fichier.pdf}" (un seul fichier, avec espaces possibles dans le chemin)
    - "{C:/chemin/un.pdf} {C:/chemin/deux.pdf}" (plusieurs fichiers)
    - "C:/chemin/sans_espace.txt" (un seul fichier sans espaces)
    - "C:/chemin/f1.txt C:/chemin/f2.txt" (plusieurs fichiers, si aucun n'a d'espaces)
    """
    if not filepaths_str:
        return []

    cleaned_paths = []

    # Tenter de traiter avec shlex pour gérer les espaces et les guillemets/accolades
    # TkinterDnD2 sur Windows peut entourer les chemins avec des accolades s'ils contiennent des espaces.
    # Il peut aussi retourner une liste de chaînes séparées par des espaces,
    # où chaque chemin contenant des espaces est entre accolades.

    # Étape 1: Supprimer les accolades de début/fin si la chaîne entière est encadrée
    processed_str = filepaths_str.strip()
    if processed_str.startswith("{") and processed_str.endswith("}"):
        # Vérifier s'il s'agit d'un seul chemin encapsulé ou de plusieurs
        # Exemple: "{path one} {path two}" vs "{a single path with spaces}"
        # Une heuristique simple: si on ne trouve pas "} {" alors c'est un seul chemin.
        if "} {" not in processed_str[1:-1]:
            processed_str = processed_str[1:-1]  # C'est un seul chemin

    # Utiliser shlex pour splitter correctement, en tenant compte des accolades comme des "quotes"
    # Temporairement remplacer les accolades par des guillemets pour shlex si cela aide
    # ou traiter les segments.
    # Une approche plus simple pour TkinterDnD2 est souvent de splitter par "} {"
    # puis de nettoyer chaque segment.

    if "} {" in processed_str:  # Cas probable de multiples fichiers avec espaces
        raw_paths = processed_str.split("} {")
        for raw_path in raw_paths:
            clean_path = raw_path.strip("{} ")  # Enlever les accolades restantes et espaces
            if clean_path and os.path.exists(clean_path):  # Valider si le chemin est plausible
                cleaned_paths.append(clean_path)
    elif processed_str.startswith("{") and processed_str.endswith("}"):  # Un seul chemin avec espace, déjà nettoyé
        clean_path = processed_str.strip("{} ")
        if clean_path and os.path.exists(clean_path):
            cleaned_paths.append(clean_path)
    else:  # Cas de chemins sans espaces ou un seul chemin sans accolades
        try:
            # shlex.split est bon pour les chaînes de type ligne de commande
            # Pour les chemins multiples sans protection, cela peut être délicat.
            # On suppose que TkinterDnD les sépare par des espaces.
            potential_paths = shlex.split(processed_str, posix=False)  # posix=False pour Windows
            for p_path in potential_paths:
                # Enlever les guillemets simples ou doubles que shlex pourrait conserver
                p_path_cleaned = p_path.strip("'\"")
                if p_path_cleaned and os.path.exists(p_path_cleaned):
                    cleaned_paths.append(p_path_cleaned)
        except ValueError:  # Erreur de shlex (ex: unmatched quotes)
            # Fallback: simple split, moins robuste pour les chemins avec espaces
            potential_paths = processed_str.split()
            for p_path in potential_paths:
                if p_path and os.path.exists(p_path):
                    cleaned_paths.append(p_path)

    # Filtrage final pour s'assurer que les fichiers existent réellement
    # Ceci est déjà fait dans les logiques ci-dessus, mais une double vérification peut être utile.
    # validated_paths = [p for p in cleaned_paths if os.path.exists(p)]

    if not cleaned_paths and os.path.exists(
            filepaths_str):  # Si aucun chemin n'a été parsé mais que la chaîne elle-même est un chemin valide
        cleaned_paths.append(filepaths_str)

    return cleaned_paths