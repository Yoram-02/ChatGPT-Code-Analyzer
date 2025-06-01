import os
import json
import time
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from utils.file_utils import load_json_file, save_json_file
from utils.browser_utils import setup_browser, is_browser_alive, open_new_tab, switch_to_tab
import tempfile
import shutil
import git
from urllib.parse import urlparse
from selenium.webdriver.common.keys import Keys
from utils.markdown_utils import save_results_to_markdown, load_markdown_file, extract_results_from_markdown
import html2text

class AnalyzerWorker(QThread):
    update_progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    browser_closed = pyqtSignal()  # Nouveau signal pour notifier que le navigateur est fermé
    login_required = pyqtSignal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.driver = None
        self.results = {}
        self.running = True
        # self.chunk_size = 15000
        self.max_chunk_size = 8000 

    def run(self):
        temp_dir = None
        try:
            if self.config.get('github_url'):
                temp_dir = self.handle_github_repo()
                if temp_dir is None:  # Échec du clonage
                    return
            # Initialisation des résultats
            self.results = {}

            # Déterminer le chemin de fichier de sortie avec extension .md
            output_file = self.config['output_file']
            if not output_file.endswith('.md'):
                output_file = os.path.splitext(output_file)[0] + '.md'
                self.config['output_file'] = output_file
            
            # Chargement sécurisé du fichier existant
            # if os.path.exists(self.config['output_file']):
            #     self.results = load_json_file(self.config['output_file'])
            #     if self.results is None:  # En cas d'erreur avec le fichier
            #         self.update_progress.emit(0, "⚠ Erreur dans le fichier de sauvegarde - Nouvelle analyse")
            #         self.results = {}
            # Chargement du fichier existant (si présent)
            if os.path.exists(output_file):
                markdown_content = load_markdown_file(output_file)
                if markdown_content is not None:
                    # Extraire les résultats précédents du fichier Markdown
                    self.results = extract_results_from_markdown(markdown_content)
                    if not self.results:
                        self.update_progress.emit(0, "⚠ Fichier Markdown existant sans analyses - Nouvelle analyse")
                else:
                    self.update_progress.emit(0, "⚠ Erreur dans le fichier Markdown - Nouvelle analyse")

            # Récupération des fichiers à analyser
            files = self.get_files_to_analyze()
            files_to_analyze = [f for f in files if f not in self.results]
            
            if not files_to_analyze:
                self.update_progress.emit(100, "✅ Tous les fichiers ont déjà été analysés.")
                self.finished.emit(self.results)
                return

            total_files = len(files_to_analyze)
            self.update_progress.emit(0, f"🚀 Début de l'analyse de {total_files} fichiers...")

            # Initialisation du navigateur
            self.driver = setup_browser()
            if not self.driver:
                self.error.emit("Échec de l'initialisation du navigateur")
                return
            
            main_tab = self.driver.current_window_handle

            # Attendre la connexion de l'utilisateur si nécessaire
            if self.config.get('require_login', True):
                self.wait_for_login()
                if not self.running:  # Vérifier si l'arrêt a été demandé pendant l'attente
                    return

            # Analyse des fichiers
            for idx, file_path in enumerate(files_to_analyze, 1):
                if not self.running:
                    break
                
                # Vérifier si le navigateur est toujours ouvert
                if not is_browser_alive(self.driver):
                    self.browser_closed.emit()
                    self.error.emit("Le navigateur a été fermé. Analyse interrompue.")
                    raise WebDriverException("Le Navigateur s'est fermer")

                progress = int((idx / total_files) * 100)
                self.update_progress.emit(progress, f"📄 Analyse de {file_path} ({idx}/{total_files})...")

                content = self.read_file(file_path)
                
                # Vérifier si le fichier est trop long pour être traité en une seule fois
                if len(content) > self.max_chunk_size:
                    self.update_progress.emit(progress, f"📑 Fichier long détecté : {file_path}. Traitement par chunks...")
                    result = self.process_large_file(file_path, content, main_tab)
                else:
                    full_prompt = f"{self.config['prompt']} \n\n {file_path} \n\n {content}"
                    result = self.send_to_chatgpt(file_path, full_prompt)
                
                # Assurez-vous que nous sommes de retour sur l'onglet principal
                switch_to_tab(self.driver, main_tab)
                
                # result = self.process_file_in_chunks(file_path, content)
                
                self.results[file_path] = result
                # Sauvegarder en Markdown après chaque fichier pour préserver les progrès
                save_results_to_markdown(self.results, output_file)

                while True:
                # Vérifier si le navigateur est toujours ouvert pendant l'attente
                    if not is_browser_alive(self.driver):
                        self.browser_closed.emit()
                        raise WebDriverException("Le navigateur a été fermé pendant la génération de la réponse")
                        
                    time.sleep(2)
                    typing = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="stop-button"]')

                    if not typing:
                        break

                                    
                time.sleep(3)

            if self.running:
                self.update_progress.emit(100, "✅ Analyse terminée !")
                self.finished.emit(self.results)

        except WebDriverException as e:
            # Attraper spécifiquement les exceptions liées au navigateur
            self.browser_closed.emit()
            self.error.emit(f"Erreur du navigateur: {str(e)}")
        except Exception as e:
            self.error.emit(f"Erreur critique lors de l'analyse: {str(e)}")
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

            self.stop()


    def handle_github_repo(self):
        """Gère le clonage d'un dépôt GitHub et retourne le chemin temporaire"""
        try:
            temp_dir = tempfile.mkdtemp(prefix="github_")
            self.update_progress.emit(0, "⚡ Clonage du dépôt GitHub...")
            
            # Validation de l'URL
            if not self.validate_github_url(self.config['github_url']):
                raise ValueError("URL GitHub invalide")

            # Clonage avec feedback de progression
            repo_url = self.format_github_url(self.config['github_url'])
            git.Repo.clone_from(
                repo_url,
                temp_dir,
                depth=1,
                progress=GitProgress(self.update_progress))
            
            self.config['repo_path'] = temp_dir
            return temp_dir
            
        except Exception as e:
            self.error.emit(f"Échec du clonage GitHub: {str(e)}")
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            return None

    @staticmethod
    def validate_github_url(url):
        """Valide qu'une URL est bien un dépôt GitHub"""
        parsed = urlparse(url)
        return parsed.netloc.endswith('github.com') and parsed.path.strip('/')

    @staticmethod
    def format_github_url(url):
        """Formate l'URL pour le clonage Git"""
        if not url.endswith('.git'):
            url += '.git'
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    def wait_for_login(self):
            """Attend que l'utilisateur se connecte à ChatGPT"""
            self.update_progress.emit(0, "⏳ En attente de connexion à ChatGPT...")
            self.login_required.emit()  # Émet le signal pour afficher le message à l'utilisateur
            
            try:
                # Attendre que le bouton de profil apparaisse (indicateur que l'utilisateur est connecté)
                wait = WebDriverWait(self.driver, 300)  # Attente de 5 minutes maximum
                
                # Vérifier périodiquement si le bouton de profil est présent
                while self.running:
                    try:
                        # Vérifier si le navigateur est toujours ouvert
                        if not is_browser_alive(self.driver):
                            self.stop()
                            return
                        
                        # Attendre que le bouton de profil apparaisse
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="profile-button"]')))
                        self.update_progress.emit(0, "✅ Connecté à ChatGPT! Démarrage de l'analyse...")
                        return  # Connexion réussie, sortir de la fonction
                    except TimeoutException:
                        # Si délai d'attente écoulé, vérifier si l'utilisateur est déjà sur la page de chat
                        # (le bouton de profil pourrait être absent si on est directement sur la page de chat)
                        
                        try:
                            input_box = self.driver.find_element(By.CSS_SELECTOR, "div.ProseMirror")
                            if input_box:  # Si la zone de saisie est présente, on est probablement déjà connecté
                                self.update_progress.emit(0, "✅ Interface ChatGPT détectée! Démarrage de l'analyse...")
                                return
                        except:
                            pass
                        
                        # Attendre 5 secondes avant de réessayer
                        for _ in range(5):
                            if not self.running:
                                self.stop()
                                self.browser_closed.emit()
                            time.sleep(1)

            except WebDriverException as e:
            # Propager l'exception pour qu'elle soit gérée dans la méthode run()
                self.stop()
                self.browser_closed.emit()

            # # except Exception as e:
            # #     self.error.emit(f"Erreur lors de l'attente de connexion")
            # #     return


    def stop(self):
        self.running = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass  # Ignorer les erreurs lors de la fermeture du navigateur

    def get_files_to_analyze(self):
        """Version compatible avec GitHub et local"""
        files = []
        base_path = Path(self.config['repo_path'])

        # Exclusion spécifique pour GitHub
        github_ignores = {'.github'} if self.config.get('github_url') else set()

        for path in base_path.rglob("*"):
            if not self.running:
                break

            if path.is_file():
                # Exclusion des dossiers
                if not any(d in path.parts for d in {*self.config['relevant_folders'], *github_ignores}):
                    continue
                    
                # Exclusion des extensions
                if path.suffix.lower() not in self.config['relevant_extensions']:
                    continue
                    
                # Pour GitHub: stockage du chemin relatif
                file_path = str(path)
                files.append(file_path)

        return files
    
    
    # def process_file_in_chunks(self, file_path, content):
    #     """
    #     Traite un fichier en l'envoyant par morceaux à ChatGPT si nécessaire
        
    #     Args:
    #         file_path (str): Chemin du fichier en cours d'analyse
    #         content (str): Contenu du fichier
            
    #     Returns:
    #         str: Résultat de l'analyse
    #     """
    #     # Si le contenu est assez court, traitement normal
    #     if len(content) <= self.chunk_size:
    #         return self.send_to_chatgpt(file_path, content, is_chunk=False)
        
    #     # Sinon, on divise en chunks
    #     chunks = self.split_content_into_chunks(content)
    #     total_chunks = len(chunks)
        
    #     responses = []
    #     for i, chunk in enumerate(chunks, 1):
    #         if not self.running or not is_browser_alive(self.driver):
    #             if not is_browser_alive(self.driver):
    #                 self.browser_closed.emit()
    #             return "Analyse interrompue"
            
    #         self.update_progress.emit(
    #             -1,  # Valeur négative pour indiquer un progrès indéterminé
    #             f"📄 Analyse de {file_path} - Morceau {i}/{total_chunks}..."
    #         )
            
    #         # Premier chunk avec instructions initiales
    #         if i == 1:
    #             prompt = f"Ce fichier est trop long et sera envoyé en {total_chunks} parties. \n\n{file_path}  partie 1/{total_chunks} \n\n:\n\n{chunk}"
    #         # Chunks intermédiaires
    #         elif i < total_chunks:
    #             prompt = f"Voici la suite du fichier\n\n  {file_path} (partie {i}/{total_chunks}):\n\n{chunk}"
    #         # Dernier chunk avec demande de synthèse
    #         else:
    #             prompt = f"Voici la dernière partie du fichier \n\n{file_path} (partie {i}/{total_chunks}):\n\n{chunk}\n\nMaintenant que tu as reçu toutes les parties du fichier, veuillez fournir une analyse complète selon les instructions initiales en 4 lignes Maximum. \n\n{self.config['prompt']}"
            
    #         response = self.send_to_chatgpt_raw(prompt)
    #         responses.append(response)
            
    #         # Petite pause entre les chunks pour ne pas surcharger l'API
    #         time.sleep(5)
        
    #     # Si un seul chunk a été envoyé, on retourne directement la réponse
    #     if len(responses) == 1:
    #         return responses[0]
        
    #     # Sinon, on utilise la dernière réponse qui devrait contenir la synthèse complète
    #     return responses[-1]

    # def split_content_into_chunks(self, content):
    #     """
    #     Divise le contenu en morceaux de taille appropriée
        
    #     Args:
    #         content (str): Contenu à diviser
            
    #     Returns:
    #         list: Liste des chunks
    #     """
    #     chunks = []
    #     # Diviser par lignes pour éviter de couper au milieu d'une ligne
    #     lines = content.split('\n')
        
    #     current_chunk = ""
    #     for line in lines:
    #         # Si l'ajout de cette ligne ne dépasse pas la taille maximale, on l'ajoute
    #         if len(current_chunk) + len(line) + 1 <= self.chunk_size:
    #             if current_chunk:
    #                 current_chunk += '\n'
    #             current_chunk += line
    #         else:
    #             # Si la ligne est trop longue, on la divise
    #             if not current_chunk:  # Si le chunk est vide, cette ligne est trop longue seule
    #                 # Diviser la ligne en morceaux
    #                 for i in range(0, len(line), self.chunk_size):
    #                     chunks.append(line[i:i+self.chunk_size])
    #             else:
    #                 # Ajouter le chunk courant et commencer un nouveau avec cette ligne
    #                 chunks.append(current_chunk)
    #                 current_chunk = line
        
    #     # Ne pas oublier le dernier chunk
    #     if current_chunk:
    #         chunks.append(current_chunk)
            
    #     return chunks

    # def send_to_chatgpt(self, filename, content, is_chunk=False):
    #     """Version simplifiée qui utilise send_to_chatgpt_raw"""
    #     if not is_chunk:
    #         prompt = f"{self.config['prompt']} \n\n  {filename} \n\n {content[:self.chunk_size]}"
    #     else:
    #         prompt = content  # Le contenu est déjà formaté comme prompt
        
    #     return self.send_to_chatgpt_raw(prompt)

    def process_large_file(self, file_path, content, main_tab):
        """
        Traite un fichier trop long en le divisant en chunks
        
        Args:
            file_path (str): Chemin du fichier
            content (str): Contenu du fichier
            main_tab: Identifiant de l'onglet principal
            
        Returns:
            str: Résumé complet du fichier
        """
        try:
            # Ouvrir un nouvel onglet pour traiter ce fichier long
            new_tab = open_new_tab(self.driver)
            if not new_tab:
                raise Exception("Impossible d'ouvrir un nouvel onglet")
            time.sleep(5)
            switch_to_tab(self.driver, new_tab)
            
            # Diviser le contenu en chunks
            chunks = self.split_into_chunks(content)
            total_chunks = len(chunks)
            
            self.update_progress.emit(-1, f"💬 Traitement du fichier en {total_chunks} parties...")
            
            # Envoyer chaque chunk à ChatGPT
            for i, chunk in enumerate(chunks, 1):
                if not self.running:
                    raise Exception("Analyse interrompue par l'utilisateur")
                
                prompt = f"Partie {i}/{total_chunks} du fichier {file_path}. Analysez cette partie, mais ne donnez pas encore de conclusion générale:\n\n"
                self.send_message_to_chatgpt(prompt + chunk)
                
                self.update_progress.emit(-1, f"💬 Chunk {i}/{total_chunks} envoyé...")
                time.sleep(10)  # Attendre un peu entre chaque envoi
            
            # Demander à ChatGPT de résumer toutes les parties
            summary_prompt = f"""Maintenant que vous avez analysé toutes les {total_chunks} parties du fichier {file_path}, 
            veuillez fournir une analyse complète et un résumé global en suivant les instructions de départ.
            \n\n {self.config['prompt']} """
            
            
            self.update_progress.emit(-1, "📝 Demande de résumé final...")
            summary = self.send_message_to_chatgpt(summary_prompt)
            
            # Retourner à l'onglet principal avant de continuer
            switch_to_tab(self.driver, main_tab)
            
            # Fermez l'onglet temporaire (optionnel)
            self.driver.switch_to.window(new_tab)
            self.driver.close()
            self.driver.switch_to.window(main_tab)
            
            return summary
            
        except Exception as e:
            # En cas d'erreur, revenir à l'onglet principal
            try:
                switch_to_tab(self.driver, main_tab)
            except:
                pass
            return f"Erreur lors du traitement du fichier long: {str(e)}"

    def split_into_chunks(self, content):
        """
        Divise le contenu en chunks de taille appropriée
        
        Args:
            content (str): Contenu à diviser
            
        Returns:
            list: Liste des chunks
        """
        chunks = []
        # Diviser le contenu en lignes puis regrouper en chunks
        lines = content.split('\n')
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_length = len(line) + 1  # +1 pour le saut de ligne
            
            # Si ajouter cette ligne dépasse la taille maximale, sauvegarder le chunk actuel
            if current_size + line_length > self.max_chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # Si une seule ligne est plus grande que la taille du chunk, la diviser
            if line_length > self.max_chunk_size:
                # Diviser la ligne en morceaux de taille maximale
                for i in range(0, len(line), self.max_chunk_size):
                    chunks.append(line[i:i + self.max_chunk_size])
            else:
                current_chunk.append(line)
                current_size += line_length
        
        # Ajouter le dernier chunk s'il n'est pas vide
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
            
        return chunks

    def read_file(self, path):
        try:
           # Convertir en Path object si ce n'est pas déjà le cas
            file_path = Path(path) if not isinstance(path, Path) else path
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            print(f"Erreur lecture fichier {path}: {str(e)}")  # Debug
            return f"Error reading file: {str(e)}"

    def send_to_chatgpt(self, filename, content):
        """
        Envoie un fichier complet à ChatGPT
        """
        prompt_complete = f"{self.config['prompt']} \n\n {filename} \n\n {content}"
        return self.send_message_to_chatgpt(content)

    def send_message_to_chatgpt(self, content):
        try:
            # Vérifier si le navigateur est toujours ouvert avant de continuer
            if not is_browser_alive(self.driver):
                self.browser_closed.emit()
                raise WebDriverException("Le navigateur a été fermé")
                
            prompt_complete = content # Limit to 12k chars
            wait = WebDriverWait(self.driver, 60)
            
            input_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProseMirror")))
            self.driver.execute_script("arguments[0].focus();", input_div)

            self.driver.execute_script("""
            const div = arguments[0];
            const text = arguments[1];
            const clipboardData = new DataTransfer();
            clipboardData.setData('text/plain', text);

            const pasteEvent = new ClipboardEvent('paste', {
                bubbles: true,
                cancelable: true,
                clipboardData: clipboardData
            });

            div.focus();
            div.dispatchEvent(pasteEvent);
            """, input_div, prompt_complete)
            time.sleep(1)

            waitbtn = WebDriverWait(self.driver, 2)
            waitbtn.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="send-button"]'))) 

            send_button = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="send-button"]')
            send_button.click()

            

            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.markdown")))

            # Attente que la génération commence
            # while True:
            #     if not is_browser_alive(self.driver):
            #         self.browser_closed.emit()
            #         raise WebDriverException("Le navigateur a été fermé pendant l'envoi")

            #     typing = self.driver.find_elements(By.CSS_SELECTOR, "div.streaming-animation")
            #     thinking = self.driver.find_elements(By.CSS_SELECTOR, "div.result-thinking")

            #     if typing or thinking:
            #         break  # Ça commence à taper
            #     time.sleep(0.5)     
            
            # while True:
            #     # Vérifier si le navigateur est toujours ouvert pendant l'attente
            #     if not is_browser_alive(self.driver):
            #         self.browser_closed.emit()
            #         raise WebDriverException("Le navigateur a été fermé pendant la génération de la réponse")
                    
            #     time.sleep(2)
            #     typing = self.driver.find_elements(By.CSS_SELECTOR, "div.streaming-animation")
            #     thinking = self.driver.find_elements(By.CSS_SELECTOR, "div.result-thinking")
                
            #     if not typing or not thinking:
            #         break

            while True:
                # Vérifier si le navigateur est toujours ouvert pendant l'attente
                    if not is_browser_alive(self.driver):
                        self.browser_closed.emit()
                        raise WebDriverException("Le navigateur a été fermé pendant la génération de la réponse")
                        
                    time.sleep(2)
                    typing = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="stop-button"]')
                    if not typing:
                        break

            time.sleep(10)
            blocks = self.driver.find_elements(By.CSS_SELECTOR, "div.markdown")
            
            # return blocks[-1].text if blocks else "No response received"

            html_content = blocks[-1].get_attribute("outerHTML")if blocks else "No response received"

            markdown_content = self.html_to_markdown(html_content)
            
            return markdown_content

        except WebDriverException as e:
            # Propager l'exception pour qu'elle soit gérée dans la méthode run()
            raise e
        except Exception as e:
            return f"Error analyzing file: {str(e)}"
        
    def html_to_markdown(self,html):
        """
        Convertit le contenu HTML en un format Markdown lisible en utilisant html2text.
        
        Args:
            html (str): Le contenu HTML à convertir.
            
        Returns:
            str: Le contenu converti en Markdown.
        """
        h = html2text.HTML2Text()
        h.ignore_links = False  # Par défaut, html2text ignore les liens, on peut les activer si nécessaire
        markdown = h.handle(html)
        return markdown

class GitProgress(git.RemoteProgress):
    """Helper pour afficher la progression du clonage GitHub"""
    def __init__(self, progress_signal):
        super().__init__()
        self.progress_signal = progress_signal
    
    def update(self, op_code, cur_count, max_count=None, message=''):
        if max_count and cur_count:
            percent = min(int((cur_count / max_count) * 100), 100)
            self.progress_signal.emit(percent, f"Clonage: {message or 'En cours...'}")