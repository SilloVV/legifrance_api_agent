import requests
import base64
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration des identifiants API Legifrance Sandbox
LEGIFRANCE_CLIENT_ID = os.getenv("LEGIFRANCE_CLIENT_ID")
LEGIFRANCE_CLIENT_SECRET = os.getenv("LEGIFRANCE_CLIENT_SECRET")
LEGIFRANCE_BASE_URL = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"
LEGIFRANCE_OAUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"

def obtenir_token_legifrance():
    """Obtient un token OAuth pour l'API Legifrance."""
    url = LEGIFRANCE_OAUTH_URL
    
    payload = {
        "grant_type": "client_credentials",
        "client_id": LEGIFRANCE_CLIENT_ID,
        "client_secret": LEGIFRANCE_CLIENT_SECRET,
        "scope": "openid"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(url, data=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Erreur d'authentification: {response.status_code} - {response.text}")
        return None

def test_ping_api():
    """Test simple pour vérifier la connexion à l'API Legifrance."""
    token = obtenir_token_legifrance()
    
    if not token:
        return "Échec de connexion à Legifrance (échec d'obtention du token)"
    
    print(f"Token obtenu avec succès: {token[:15]}...")
    
    # Test de requête simple - recherche de texte
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    
    # Requête simple pour rechercher le Code civil
    payload = {
        "recherche": {
            "champs": [
                {
                    "typeChamp": "ALL",
                    "criteres": [
                        {
                            "typeRecherche": "EXACTE",
                            "valeur": "Code civil",
                            "operateur": "ET"
                        }
                    ],
                    "operateur": "ET"
                }
            ],
            "pageNumber": 1,
            "pageSize": 1,
            "sort": "PERTINENCE"
        },
        "fond": "CODE_DATE"
    }
    
    response = requests.post(f"{LEGIFRANCE_BASE_URL}/search", headers=headers, json=payload)
    
    if response.status_code == 200:
        resultat = response.json()
        print("Requête réussie !")
        print(resultat)
        if "results" in resultat:
            nombre_resultats = len(resultat["results"])
            print(f"Nombre de résultats: {nombre_resultats}")
            return f"Connexion réussie à Legifrance, {nombre_resultats} résultat(s) obtenus"
        return "Connexion réussie à Legifrance, structure de réponse inhabituelle"
    else:
        print(f"Erreur lors de la requête: {response.status_code} - {response.text}")
        return f"Échec de la requête à Legifrance: code {response.status_code}"

def recherche_legifrance(
    query=None,
    type_champ="ALL",
    type_recherche="EXACTE", 
    fond="LEGI_ARTICLE",
    filtres=None,
    page=1,
    page_size=10,
    tri="PERTINENCE",
    token=None
):
    """
    Fonction générale pour rechercher dans l'API Legifrance avec de nombreuses options.
    
    Args:
        query: Texte à rechercher (None pour ne pas spécifier de recherche textuelle)
        type_champ: Type de champ pour la recherche (ALL, TITLE, NUM_ARTICLE, etc.)
        type_recherche: Type de recherche (EXACTE ou APPROXIMATIVE)
        fond: Fond documentaire (LEGI_ARTICLE, CODE_DATE, JURI_DATE, LODA_DATE, etc.)
        filtres: Liste de dictionnaires de filtres (ex: [{"facette": "NOM_CODE", "valeurs": ["Code civil"]}])
        page: Numéro de page
        page_size: Nombre de résultats par page
        tri: Méthode de tri (PERTINENCE, DATE)
        token: Token d'authentification (obtenu automatiquement si non fourni)
        
    Returns:
        Résultats de la recherche
    """
    if not token:
        token = obtenir_token_legifrance()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    
    # Construire la requête de base
    payload = {
        "recherche": {
            "pageNumber": page,
            "pageSize": page_size,
            "sort": tri,
            "typePagination": "DEFAUT"
        },
        "fond": fond
    }
    
    # Ajouter les critères de recherche textuelle si fournis
    if query:
        payload["recherche"]["champs"] = [
            {
                "typeChamp": type_champ,
                "criteres": [
                    {
                        "typeRecherche": type_recherche,
                        "valeur": query,
                        "operateur": "ET"
                    }
                ],
                "operateur": "ET"
            }
        ]
        payload["recherche"]["operateur"] = "ET"
    
    # Ajouter les filtres si fournis
    if filtres:
        payload["recherche"]["filtres"] = filtres
    
    # Effectuer la requête API
    try:
        response = requests.post(f"{LEGIFRANCE_BASE_URL}/search", headers=headers, json=payload)
        response.raise_for_status()  # Lever une exception en cas d'erreur HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête à l'API: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Détails: {e.response.status_code} - {e.response.text}")
        return None

# Exemples d'utilisation

def recherche_par_question(question):
    """Recherche des textes juridiques pertinents pour une question."""
    return recherche_legifrance(
        query=question,
        type_recherche="APPROXIMATIVE",  # Recherche approximative pour plus de pertinence
        fond="LEGI_ARTICLE",  # Recherche dans les articles de loi
        page_size=15
    )

def recherche_article_code(code_name, article_num):
    """Recherche un article spécifique dans un code."""
    filtres = [{"facette": "NOM_CODE", "valeurs": [code_name]}]
    return recherche_legifrance(
        query=article_num,
        type_champ="NUM_ARTICLE",
        filtres=filtres,
        fond="CODE_DATE"
    )

def recherche_jurisprudence(theme):
    """Recherche de la jurisprudence sur un thème donné."""
    return recherche_legifrance(
        query=theme,
        fond="JURI_DATE",
        tri="DATE",  # Trié par date pour avoir les décisions les plus récentes
        page_size=20
    )

def extraire_resultats(resultats):
    """Fonction utilitaire pour extraire les informations pertinentes des résultats."""
    if not resultats or "results" not in resultats:
        return []
    
    extraits = []
    for resultat in resultats["results"]:
        item = {
            "titre": resultat.get("titles", [{}])[0].get("title", "Sans titre") if "titles" in resultat else "Sans titre",
            "nature": resultat.get("nature", "Non spécifiée"),
            "date": resultat.get("date", "Date inconnue"),
            "id": resultat.get("id", resultat.get("titles", [{}])[0].get("id") if "titles" in resultat else None),
            "extraits": []
        }
        
        if "sections" in resultat:
            for section in resultat["sections"]:
                if "extracts" in section:
                    for extract in section["extracts"]:
                        item["extraits"].append({
                            "article": extract.get("num", "Non numéroté"),
                            "texte": extract.get("values", [""])[0] if "values" in extract and extract["values"] else "",
                            "id": extract.get("id", "")
                        })
        
        extraits.append(item)
    
    return extraits


if __name__ == "__main__":
    print("Test de connexion à l'API Legifrance...")
    resultat = test_ping_api()
    print("Fin de test.")

    # question = "Un enfant peut-il être commercant ?"
    # resultats = recherche_par_question(question)
    # textes_extraits = extraire_resultats(resultats)

    # for i, texte in enumerate(textes_extraits):
    #     print(f"\nRésultat {i+1}: {texte['titre']}")
    #     print(f"Nature: {texte['nature']}")
    #     print(f"Date: {texte['date']}")
        
    #     for extrait in texte['extraits']:
    #         print(f"  Article {extrait['article']}:")
    #         print(f"    {extrait['texte']}")
