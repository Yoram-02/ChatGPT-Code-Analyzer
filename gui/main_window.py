from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QTextEdit, QPushButton, QFileDialog, QRadioButton, 
                            QButtonGroup, QProgressBar, QMessageBox, QGroupBox, QCheckBox)
from PyQt5.QtCore import Qt
from workers.analyzer_worker import AnalyzerWorker
from gui.styles import get_main_style
import os

class CodeAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.setup_ui()
        self.setWindowTitle("ChatGPT Code Analyzer")
        self.setGeometry(100, 100, 800, 1200)
        self.setStyleSheet(get_main_style())

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Repository Selection Group
        repo_group = QGroupBox("Source Selection")
        repo_layout = QVBoxLayout()
        
        self.local_radio = QRadioButton("Local Repository")
        self.local_radio.setChecked(True)
        self.github_radio = QRadioButton("GitHub Repository")
        
        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.local_radio)
        self.radio_group.addButton(self.github_radio)
        
        # Local repo selection
        local_repo_layout = QHBoxLayout()
        self.local_path_input = QLineEdit()
        self.local_path_input.setPlaceholderText("Select local repository folder...")
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_local_repo)
        local_repo_layout.addWidget(self.local_path_input)
        local_repo_layout.addWidget(browse_button)
        
        # GitHub repo selection
        github_repo_layout = QHBoxLayout()
        self.github_url_input = QLineEdit()
        self.github_url_input.setPlaceholderText("https://github.com/user/repo/")
        github_repo_layout.addWidget(QLabel("GitHub URL:"))
        github_repo_layout.addWidget(self.github_url_input)
        
        repo_layout.addWidget(self.local_radio)
        repo_layout.addLayout(local_repo_layout)
        repo_layout.addWidget(self.github_radio)
        repo_layout.addLayout(github_repo_layout)
        repo_group.setLayout(repo_layout)
        
        # Prompt Group
        prompt_group = QGroupBox("Analysis Prompt")
        prompt_layout = QVBoxLayout()
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Enter your analysis prompt for ChatGPT...")
        prompt_layout.addWidget(self.prompt_edit)
        prompt_group.setLayout(prompt_layout)
        
        # ChatGPT Login Group
        login_group = QGroupBox("ChatGPT Authentication")
        login_layout = QVBoxLayout()
        self.require_login_checkbox = QCheckBox("Wait for user to login before analysis")
        self.require_login_checkbox.setChecked(True)
        login_layout.addWidget(self.require_login_checkbox)
        
        login_info_label = QLabel("If checked, the program will wait for you to log in to ChatGPT")
        login_info_label.setStyleSheet("color: #555;")
        login_layout.addWidget(login_info_label)
        login_group.setLayout(login_layout)

        # Output Group
        # output_group = QGroupBox("Output")
        # output_layout = QVBoxLayout()
        # self.output_file_input = QLineEdit()
        # self.output_file_input.setPlaceholderText("output.json")
        # browse_output_button = QPushButton("Browse...")
        # browse_output_button.clicked.connect(self.browse_output_file)
        # output_layout.addWidget(QLabel("Output File:"))
        # output_file_layout = QHBoxLayout()
        # output_file_layout.addWidget(self.output_file_input)
        # output_file_layout.addWidget(browse_output_button)
        # output_layout.addLayout(output_file_layout)
        # output_group.setLayout(output_layout)

        # Output Group
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        self.output_file_input = QLineEdit()
        self.output_file_input.setPlaceholderText("output.md")
        browse_output_button = QPushButton("Browse...")
        browse_output_button.clicked.connect(self.browse_output_file)
        output_layout.addWidget(QLabel("Output File (Markdown):"))
        output_file_layout = QHBoxLayout()
        output_file_layout.addWidget(self.output_file_input)
        output_file_layout.addWidget(browse_output_button)
        output_layout.addLayout(output_file_layout)
        output_group.setLayout(output_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Analysis")
        self.start_button.clicked.connect(self.start_analysis)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_analysis)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        # Bouton pour ouvrir le fichier Markdown
        open_file_button = QPushButton("Open Results File")
        open_file_button.clicked.connect(self.open_result_file)
        button_layout.addWidget(open_file_button)
        
        # Add all to main layout
        layout.addWidget(repo_group)
        layout.addWidget(prompt_group)
        layout.addWidget(login_group) 
        layout.addWidget(output_group)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addLayout(button_layout)
        
        # Set default values
        self.prompt_edit.setPlainText("""Analyse le code source en se concentrant sur plusieurs aspects clés :

1. Sécurité : Identifie toute vulnérabilité de sécurité (injections SQL, XSS, CSRF, RCE, SSRF, etc.), Détecte toute backdoor ou présence de code malveillant (exécution cachée, obfuscation, exfiltration de données, etc.), Vérifie les dépendances ou appel vers d'autre url externe.

2. Analyse des fonctionnalités Front & UI: Décrit les le fichier, s'il fait de l’interface utilisateur, où est-ce qu'on peut modifier est ce que c'est l'Ui principale avec les conversations ? Mon but est de modifier cette interface pour la rendre plus sexy

3. Ajout de TTS (Text-to-Speech) et STT (Speech-to-Text): Évalue la faisabilité de l’intégration d’un module de TTS/STT dans l’architecture existante. Est-ce que le fichier permet une intégration STT-TTS ? 

4. Je souhaite rendre ce logiciel agent-native. Pour cela j'aimerais connecter mon agent en api et faire en sorte qu'il soit disponible ensuite dans la conversation. Est ce que ce fichier est le backend qui me permet de rendre skiris agent-native ? Si oui, à quelle fonction/méthode je dois me connecte ? Est-ce que ce fichier permet de mettre le front de mon agent dans une conversation par exemple de type channel pour retrouver l'interface de mon agent ?

Remarque important: Sois précis et propose des solutions concrètes pour chaque problème détecté. Fournis des extraits de code si nécessaire pour illustrer les améliorations possibles. Ton analyse du fichier doit faire 4 lignes Maximum.
""")
        self.output_file_input.setText("resultats_chatgpt.md")
        
        # Update UI based on radio selection
        self.local_radio.toggled.connect(self.update_ui)
        self.update_ui()
    
    def start_analysis(self):
        if not self.validate_inputs():
            return
            
        config = self._create_config()

        # Assurer que le fichier de sortie a l'extension .md
        output_file = config['output_file']
        if not output_file.endswith('.md'):
            output_file = os.path.splitext(output_file)[0] + '.md'
            config['output_file'] = output_file
            self.output_file_input.setText(output_file)
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Initializing analysis...")
        
        self.worker = AnalyzerWorker(config)
        self.worker.update_progress.connect(self.update_progress)
        self.worker.finished.connect(self.analysis_finished)
        self.worker.error.connect(self.show_error)
        self.worker.browser_closed.connect(self.handle_browser_closed)  # Connecter le nouveau signal
        self.worker.login_required.connect(self.handle_login_required)
        self.worker.start()
    
    def handle_browser_closed(self):
        """Gère la fermeture inattendue du navigateur"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Navigateur fermé - Analyse interrompue")
        QMessageBox.warning(self, "Navigateur fermé", 
                           "Le navigateur a été fermé. L'analyse a été interrompue.")
        
    def handle_login_required(self):
        """Affiche un message lorsque l'authentification est nécessaire"""
        self.status_label.setText("En attente de connexion à ChatGPT...")
        QMessageBox.information(self, "Connexion requise", 
                             "Veuillez vous connecter à ChatGPT dans le navigateur qui vient de s'ouvrir.\n\n"
                             "L'analyse commencera automatiquement une fois que vous serez connecté.")
    
    def update_ui(self):
        self.github_url_input.setEnabled(self.github_radio.isChecked())
        self.local_path_input.setEnabled(self.local_radio.isChecked())
        browse_button = self.findChild(QPushButton, "Browse...")
        if browse_button:
            browse_button.setEnabled(self.local_radio.isChecked())
    
    def browse_local_repo(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Repository Folder")
        if folder:
            self.local_path_input.setText(folder)
    
    # def browse_output_file(self):
    #     file, _ = QFileDialog.getSaveFileName(self, "Select Output File", "", "JSON Files (*.json)")
    #     if file:
    #         self.output_file_input.setText(file)

    def browse_output_file(self):
        file, _ = QFileDialog.getSaveFileName(self, "Select Output File", "", "Markdown Files (*.md)")
        if file:
            self.output_file_input.setText(file)
    
    def open_result_file(self):
        """Ouvre le fichier Markdown des résultats avec l'application par défaut"""
        output_file = self.output_file_input.text()
        if not output_file:
            QMessageBox.warning(self, "Warning", "Please specify an output file first")
            return
         
        # Assurer que le fichier a l'extension .md
        if not output_file.endswith('.md'):
            output_file = os.path.splitext(output_file)[0] + '.md'
            
        if not os.path.exists(output_file):
            QMessageBox.warning(self, "Warning", "The result file doesn't exist yet")
            return
            
        try:
            # Utiliser la méthode appropriée selon le système d'exploitation
            import platform
            import subprocess
            
            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', output_file))
            elif platform.system() == 'Windows':
                os.startfile(output_file)
            else:  # Linux et autres
                subprocess.call(('xdg-open', output_file))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open the file: {str(e)}")
    
    
    # def start_analysis(self):
    #     if not self.validate_inputs():
    #         return
            
    #     config = self._create_config()
        
    #     self.start_button.setEnabled(False)
    #     self.stop_button.setEnabled(True)
    #     self.status_label.setText("Initializing analysis...")
        
    #     self.worker = AnalyzerWorker(config)
    #     self.worker.update_progress.connect(self.update_progress)
    #     self.worker.finished.connect(self.analysis_finished)
    #     self.worker.error.connect(self.show_error)
    #     self.worker.start()
    
    def _create_config(self):
        return {
            'repo_path': self.local_path_input.text() if self.local_radio.isChecked() else "",
            'github_url': self.github_url_input.text() if self.github_radio.isChecked() else None,
            'prompt': self.prompt_edit.toPlainText(),
            'output_file': self.output_file_input.text(),
            'ignored_extensions': {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg',
                                '.mp3', '.mp4', '.avi', '.mov',
                                '.zip', '.tar', '.gz', '.rar',
                                '.exe', '.dll', '.so', '.bin', '.class', '.jar',
                                '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                                '.log'},
            'ignored_folders': {'node_modules', '.git', '.github','.vscode', '.idea', 'dist', 
                              'build', '__pycache__', '.next', 'out', 'coverage'},
            'require_login': self.require_login_checkbox.isChecked(),
            'relevant_extensions' : {
                    ".js", ".ts", ".jsx", ".tsx",
                    ".php", ".py",
                    ".java", ".cs", ".rb", ".go",
                    ".json", ".env", ".yml", ".yaml",
                    ".html", ".htm",
                    ".css", ".scss", ".sass",
                    ".vue",
                    ".sh", ".bash",
                    ".lock", ".dockerfile"
                },
                'relevant_folders' : {
                    "src",
                },
                "chunck_prompt": """Analyse ce fichier code source"""
                    }
    
    def stop_analysis(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        self.status_label.setText("Analysis stopped by user")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def update_progress(self, progress, message):
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
        self.progress_bar.repaint()
        self.status_label.repaint()
        print(f"[PROGRESS] {progress}% - {message}") 

    
    def analysis_finished(self, results):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText(f"Analysis completed! {len(results)} files analyzed.")
        QMessageBox.information(self, "Success", "Analysis completed successfully!")
    
    def show_error(self, message):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QMessageBox.critical(self, "Error", message)
        self.status_label.setText("Error occurred")
    
    def validate_inputs(self):
        if self.local_radio.isChecked() and not self.local_path_input.text():
            QMessageBox.warning(self, "Warning", "Please select a local repository folder")
            return False
        
        if self.github_radio.isChecked():
            url = self.github_url_input.text()
            if not url:
                QMessageBox.warning(self, "Warning", "Please enter a GitHub repository URL")
                return False
            if not url.startswith(('http://', 'https://')):
                QMessageBox.warning(self, "Warning", "Please enter a valid URL starting with http:// or https://")
                return False
        
        if not self.prompt_edit.toPlainText().strip():
            QMessageBox.warning(self, "Warning", "Please enter an analysis prompt")
            return False
        
        if not self.output_file_input.text().strip():
            QMessageBox.warning(self, "Warning", "Please specify an output file")
            return False
        
        return True
    
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, 'Analysis in Progress',
                "An analysis is currently running. Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.worker.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()