import os
from pathlib import Path

def save_results_to_markdown(results, output_file):
    """
    Sauvegarde les résultats d'analyse dans un fichier Markdown lisible
    
    Args:
        results (dict): Dictionnaire contenant les résultats d'analyse par fichier
        output_file (str): Chemin où sauvegarder le fichier Markdown
    
    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    try:
        # Assurons-nous que l'extension du fichier est .md
        if not output_file.endswith('.md'):
            output_file = os.path.splitext(output_file)[0] + '.md'
        
        temp_file = output_file + ".tmp"
        
        with open(temp_file, "w", encoding="utf-8") as f:
            # Écriture de l'en-tête du document
            f.write("# Analyse du code source par ChatGPT\n\n")
            f.write("Ce document contient l'analyse automatisée des fichiers du projet.\n\n")
            f.write("---\n\n")
            
            # Tri des fichiers pour une meilleure organisation
            sorted_files = sorted(results.keys())
            
            # Organisation par dossier pour une meilleure structure
            folders = {}
            for file_path in sorted_files:
                folder = os.path.dirname(file_path)
                if folder not in folders:
                    folders[folder] = []
                folders[folder].append(file_path)
            
            # Écriture par dossier
            for folder, files in sorted(folders.items()):
                # Créer un titre pour le dossier
                folder_title = folder if folder else "Dossier racine"
                f.write(f"## {folder_title}\n\n")
                
                # Écrire chaque fichier de ce dossier
                for file_path in files:
                    file_name = os.path.basename(file_path)
                    analysis_result = results[file_path]
                    
                    f.write(f"### {file_name}\n\n")
                    f.write(f"**Chemin complet:** `{file_path}`\n\n")
                    f.write("**Analyse:**\n\n")
                    f.write("...\n\n")
                    f.write(analysis_result)
                    f.write("\n...\n\n")
                    f.write("---\n\n")
            
            # Pied de page
            f.write("\n\n*Généré automatiquement par l'analyseur de code ChatGPT*\n")
        
        # Remplace le fichier original seulement si l'écriture a réussi
        if os.path.exists(temp_file):
            os.replace(temp_file, output_file)
            return True
        return False
        
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du fichier Markdown: {str(e)}")
        return False

def load_markdown_file(file_path):
    """
    Vérifie si un fichier Markdown existe et renvoie son contenu
    
    Args:
        file_path (str): Chemin vers le fichier Markdown
        
    Returns:
        str: Contenu du fichier ou None en cas d'erreur
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        return None
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier Markdown: {str(e)}")
        return None

def extract_results_from_markdown(markdown_content):
    """
    Extrait les résultats d'analyse depuis un fichier Markdown existant
    
    Args:
        markdown_content (str): Contenu du fichier Markdown
        
    Returns:
        dict: Dictionnaire des résultats par fichier ou {} si vide
    """
    if not markdown_content:
        return {}
    
    results = {}
    current_file = None
    current_content = []
    in_analysis_block = False
    
    for line in markdown_content.split('\n'):
        # Détecter un nouveau fichier d'analyse
        if line.startswith("**Chemin complet:**"):
            # Sauvegarder le précédent si applicable
            if current_file and current_content:
                results[current_file] = '\n'.join(current_content)
                current_content = []
            
            # Extraire le chemin du fichier entre les backticks
            try:
                current_file = line.split('`')[1]
            except IndexError:
                continue
        
        # Détecter le début et la fin d'un bloc d'analyse
        elif line == "...":
            in_analysis_block = not in_analysis_block
            # Ne pas ajouter les délimiteurs de bloc de code
            continue
        
        # Collecter le contenu du bloc d'analyse
        elif in_analysis_block and current_file:
            current_content.append(line)
    
    # Sauvegarder le dernier fichier si applicable
    if current_file and current_content:
        results[current_file] = '\n'.join(current_content)
    
    return results