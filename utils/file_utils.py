import os
import json

def load_json_file(file_path):
    """
    Charge un fichier JSON en toute sécurité
    
    Args:
        file_path (str): Chemin vers le fichier JSON
        
    Returns:
        dict: Contenu du fichier JSON ou None en cas d'erreur
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read().strip()
            if file_content:  # Vérifie si le fichier n'est pas vide
                return json.loads(file_content)
            else:
                return {}
    except json.JSONDecodeError as e:
        print(f"Erreur de décodage JSON: {str(e)}")
        return None
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier: {str(e)}")
        return None

def save_json_file(file_path, data):
    """
    Sauvegarde des données dans un fichier JSON de manière sécurisée
    
    Args:
        file_path (str): Chemin où sauvegarder le fichier
        data (dict): Données à sauvegarder
    
    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    try:
        # Sauvegarde dans un fichier temporaire d'abord
        temp_file = file_path + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Remplace le fichier original seulement si l'écriture a réussi
        if os.path.exists(temp_file):
            os.replace(temp_file, file_path)
            return True
        return False
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {str(e)}")
        return False