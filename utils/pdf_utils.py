import pdfplumber
import re


def extraire_infos_facture(chemin_pdf_facture: str) -> dict:
    """
    Extrait le Nom, le Prénom et la Référence d'un fichier PDF de facture
    en se basant sur un format spécifique (comme l'exemple fourni).
    """
    infos = {"nom": None, "prenom": None, "reference": None}
    try:
        with pdfplumber.open(chemin_pdf_facture) as pdf:
            if not pdf.pages:
                print("Avertissement: Le PDF ne contient aucune page.")
                return infos

            page = pdf.pages[0]  # On suppose que les infos sont sur la première page
            texte_complet = page.extract_text()

            if not texte_complet:
                print("Avertissement: Aucun texte n'a pu être extrait du PDF.")
                return infos

            lignes = texte_complet.split('\n')

            # 1. Extraction de la Référence
            # Format attendu: "Référence: 25 4868" [cite: 3]
            for ligne in lignes:
                match_reference = re.search(r"Référence:\s*(25[\s\d]+)", ligne,
                                            re.IGNORECASE)  # Modifié pour + après [\s\d]
                if match_reference:
                    ref_brute = match_reference.group(1).strip()
                    # Nettoyage pour avoir "25XXXX" (ex: "254868" à partir de "25 4868")
                    # S'assure que ça commence par "25" et qu'il y a quelque chose après l'espace
                    if ref_brute.startswith("25 ") and len(ref_brute) > 3:
                        # Prend tout ce qui suit "25 " et enlève les espaces
                        infos["reference"] = "25" + ref_brute[3:].replace(" ", "")
                    elif ref_brute.startswith("25") and " " not in ref_brute and len(
                            ref_brute) > 2:  # Cas "25XXXX" direct
                        infos["reference"] = ref_brute
                    else:  # Fallback plus générique si le format est "25 XXXX" mais ne commence pas par "25 "
                        parts_ref = ref_brute.split(" ", 1)
                        if len(parts_ref) == 2 and parts_ref[0] == "25":
                            infos["reference"] = "25" + parts_ref[1].replace(" ", "")
                        else:
                            infos["reference"] = ref_brute.replace(" ", "")  # Fallback ultime
                    break

            # Si non trouvée avec le label "Référence:", tenter une recherche plus générique de "25XXXX" ou "25 XXXX"
            if not infos["reference"]:
                # Cherche un "25" suivi d'un espace (optionnel) et d'au moins 3 chiffres.
                # \b pour délimiter le mot/nombre.
                match_ref_simple = re.search(r"\b(25\s?\d{3,})\b", texte_complet)
                if match_ref_simple:
                    infos["reference"] = match_ref_simple.group(1).replace(" ", "")

            # 2. Extraction Nom et Prénom
            # Basé sur "DELFOSSE LOUISE" [cite: 5]

            # Priorité 1: Chercher "NOM PRENOM      ASSURE"
            for ligne_brute in lignes:
                ligne_nettoyee_pour_assure = ligne_brute.strip()
                # Regex pour capturer NOM PRENOM (majuscules, tirets, apostrophes) suivi par "ASSURE"
                # Le prénom peut être composé.
                match_nom_prenom_assure = re.match(r"^\s*([A-ZÀ-Ÿ'-]+)\s+([A-ZÀ-Ÿ'-]+(?:\s[A-ZÀ-Ÿ'-]+)*)\s+ASSURE\b",
                                                   ligne_nettoyee_pour_assure, re.IGNORECASE)
                if match_nom_prenom_assure:
                    infos["nom"] = match_nom_prenom_assure.group(1)
                    infos["prenom"] = match_nom_prenom_assure.group(2)
                    break  # Trouvé, on arrête

            # Priorité 2: Si non trouvé, chercher "NOM PRENOM" sur une ligne seule,
            # typiquement au-dessus d'une adresse.
            if not infos["nom"]:  # Si le nom n'a pas été trouvé avec "ASSURE"
                for i, ligne_brute in enumerate(lignes):
                    ligne_nettoyee = ligne_brute.strip()

                    # Cherche une ligne avec exactement un NOM puis un ou plusieurs PRENOMS (tout en majuscules)
                    # Ex: "DELFOSSE LOUISE" [cite: 5]
                    match_nom_prenom_seul = re.match(r"^\s*([A-ZÀ-Ÿ'-]+)\s+([A-ZÀ-Ÿ'-]+(?:\s[A-ZÀ-Ÿ'-]+)*)\s*$",
                                                     ligne_nettoyee)

                    if match_nom_prenom_seul:
                        potentiel_nom = match_nom_prenom_seul.group(1)
                        potentiel_prenom = match_nom_prenom_seul.group(2)

                        # Mots clés souvent trouvés dans les en-têtes ou adresses de l'hôpital, à éviter pour le nom du patient.
                        mots_hopital_a_eviter = ["HOPITAL", "PRIVE", "NATECIA", "AVENUE", "ROCKFELLER", "LYON", "TEL",
                                                 "SIRET", "FINESS", "REFERENCE", "PERIODE", "SERVICE", "SORTIE",
                                                 "PRESTATIONS", "TOTAL", "FAIT A", "CPAM", "MUTUELLE"]

                        # Vérifier que les mots trouvés ne sont pas des mots clés de l'hôpital
                        nom_est_valide = potentiel_nom.upper() not in mots_hopital_a_eviter
                        prenom_est_valide = True
                        for mot_prenom in potentiel_prenom.upper().split():
                            if mot_prenom in mots_hopital_a_eviter:
                                prenom_est_valide = False
                                break

                        if nom_est_valide and prenom_est_valide:
                            # Heuristique supplémentaire : la ligne suivante contient souvent une adresse (numéro + rue/av...) ou un code postal
                            ligne_suivante_suggere_adresse = False
                            if i + 1 < len(lignes):
                                ligne_suiv_nettoyee = lignes[i + 1].strip()
                                if re.search(r"^\d+.*(?:AVENUE|RUE|BOULEVARD|CHEMIN|PLACE|ALLÉE|BD|AV)\b",
                                             ligne_suiv_nettoyee, re.IGNORECASE) or \
                                        re.search(r"^\d{5}\s+[A-ZÀ-Ÿ'-]+",
                                                  ligne_suiv_nettoyee):  # Ex: "24 AVENUE DU CHATEAU" [cite: 5] ou "69003 LYON" [cite: 5]
                                    ligne_suivante_suggere_adresse = True

                            if ligne_suivante_suggere_adresse:
                                infos["nom"] = potentiel_nom
                                infos["prenom"] = potentiel_prenom
                                break  # Trouvé, on arrête

    except Exception as e:
        print(f"Erreur lors de l'extraction PDF ({chemin_pdf_facture}): {e}")

    print(f"Infos extraites du PDF: {infos}")  # Pour le débogage
    return infos